from dataclasses import dataclass
import importlib.util
from pathlib import Path

import cv2
import numpy as np

from app.core.config import settings


@dataclass
class DetectionResult:
    weed_mask: np.ndarray
    instances: list[dict]
    mode: str
    model_name: str | None
    note: str


class WeedDetector:
    """Inference boundary for trained segmentation models or explicit demo mode."""

    def __init__(self) -> None:
        self.model_path = settings.model_path
        self._model = None
        self._semantic_model = None
        self._torch = None
        self._semantic_classes: list[str] = []
        if self.model_path and Path(self.model_path).is_file():
            self._load_model()

    def _load_model(self) -> None:
        try:
            import torch
            model_definition = settings.project_root / "ml" / "model.py"
            spec = importlib.util.spec_from_file_location("weed_segmentation_model", model_definition)
            if spec is None or spec.loader is None:
                raise ImportError(f"Unable to load model definition: {model_definition}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            build_model = module.build_model

            checkpoint = torch.load(self.model_path, map_location="cpu", weights_only=False)
            if not isinstance(checkpoint, dict) or "state_dict" not in checkpoint:
                raise ValueError("Checkpoint does not contain a semantic segmentation state_dict.")
            classes = checkpoint.get("classes", [])
            if "weed" not in classes:
                raise ValueError("Checkpoint does not declare a weed class.")
            model = build_model(len(classes))
            model.load_state_dict(checkpoint["state_dict"])
            model.eval()
            self._torch = torch
            self._semantic_model = model
            self._semantic_classes = [str(item) for item in classes]
            return
        except (ImportError, KeyError, OSError, RuntimeError, ValueError):
            self._semantic_model = None
        try:
            from ultralytics import YOLO

            self._model = YOLO(self.model_path)
        except (ImportError, OSError, RuntimeError, ValueError):
            self._model = None

    def predict(self, image: np.ndarray) -> DetectionResult:
        if self._semantic_model is not None:
            return self._predict_with_semantic_model(image)
        if self._model is not None:
            return self._predict_with_yolo(image)
        return self._predict_demo(image)

    def _predict_with_semantic_model(self, image: np.ndarray) -> DetectionResult:
        height, width = image.shape[:2]
        image_size = 256
        resized = cv2.resize(image, (image_size, image_size), interpolation=cv2.INTER_AREA)
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        tensor = self._torch.from_numpy(rgb.transpose(2, 0, 1)).unsqueeze(0)
        with self._torch.no_grad():
            probabilities = self._torch.softmax(self._semantic_model(tensor), dim=1)[0]
        weed_class = self._semantic_classes.index("weed")
        weed_probability = probabilities[weed_class].cpu().numpy()
        class_map = probabilities.argmax(dim=0).cpu().numpy().astype(np.uint8)
        weed_map = cv2.resize(class_map, (width, height), interpolation=cv2.INTER_NEAREST) == weed_class
        mask = np.where(weed_map, 255, 0).astype(np.uint8)
        confidence_map = cv2.resize(weed_probability, (width, height), interpolation=cv2.INTER_LINEAR)
        instances: list[dict] = []
        component_count, component_labels, stats, _ = cv2.connectedComponentsWithStats(
            (mask > 0).astype(np.uint8), connectivity=8
        )
        for component_id in range(1, component_count):
            x, y, component_width, component_height, area = stats[component_id]
            if area < 20:
                continue
            component = component_labels == component_id
            confidence = float(confidence_map[component].mean())
            instances.append(
                {
                    "id": len(instances) + 1,
                    "class_name": "weed",
                    "confidence": round(confidence, 4),
                    "bbox": {
                        "x_min": int(x),
                        "y_min": int(y),
                        "x_max": int(x + component_width),
                        "y_max": int(y + component_height),
                    },
                    "mask_area_pixels": int(area),
                }
            )
        return DetectionResult(
            mask,
            instances,
            "custom_model",
            Path(self.model_path).name,
            "Custom trained semantic weed/crop segmentation model.",
        )

    def _predict_with_yolo(self, image: np.ndarray) -> DetectionResult:
        result = self._model.predict(source=image, verbose=False)[0]
        height, width = image.shape[:2]
        mask = np.zeros((height, width), dtype=np.uint8)
        instances: list[dict] = []
        if result.masks is None or result.boxes is None:
            return DetectionResult(mask, instances, "custom_model", Path(self.model_path).name, "No weed instances detected.")

        class_names = result.names
        for index, polygon in enumerate(result.masks.data.cpu().numpy()):
            class_id = int(result.boxes.cls[index].item())
            class_name = str(class_names[class_id]).lower()
            if "weed" not in class_name:
                continue
            resized = cv2.resize(polygon, (width, height), interpolation=cv2.INTER_NEAREST) > 0.5
            mask[resized] = 255
            confidence = float(result.boxes.conf[index].item())
            x1, y1, x2, y2 = result.boxes.xyxy[index].cpu().numpy().tolist()
            instances.append(
                {
                    "id": index + 1,
                    "class_name": class_name,
                    "confidence": round(confidence, 4),
                    "bbox": {"x_min": round(x1, 2), "y_min": round(y1, 2), "x_max": round(x2, 2), "y_max": round(y2, 2)},
                    "mask_area_pixels": int(resized.sum()),
                }
            )
        return DetectionResult(mask, instances, "custom_model", Path(self.model_path).name, "Custom agricultural YOLO segmentation model.")

    def _predict_demo(self, image: np.ndarray) -> DetectionResult:
        # Deterministic green-region segmentation is for UI demonstration only.
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array([25, 45, 35]), np.array([95, 255, 240]))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        instances: list[dict] = []
        filtered_mask = np.zeros_like(mask)
        for index, contour in enumerate(contours):
            area = int(cv2.contourArea(contour))
            if area < max(20, image.shape[0] * image.shape[1] // 5000):
                continue
            cv2.drawContours(filtered_mask, [contour], -1, 255, -1)
            x, y, width, height = cv2.boundingRect(contour)
            instances.append(
                {
                    "id": len(instances) + 1,
                    "class_name": "demo-vegetation",
                    "confidence": 0.0,
                    "bbox": {"x_min": x, "y_min": y, "x_max": x + width, "y_max": y + height},
                    "mask_area_pixels": area,
                }
            )
        return DetectionResult(
            filtered_mask,
            instances,
            "demo",
            None,
            "DEMO MODE: deterministic green-region segmentation. Configure WEED_MODEL_PATH with a trained agricultural model for valid weed predictions.",
        )
