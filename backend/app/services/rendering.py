import base64
from io import BytesIO

import cv2
import numpy as np
from PIL import Image


def image_data_url(image: np.ndarray) -> str:
    success, encoded = cv2.imencode(".png", image)
    if not success:
        raise ValueError("Could not encode analysis image.")
    return "data:image/png;base64," + base64.b64encode(encoded.tobytes()).decode("ascii")


def render_outputs(image: np.ndarray, mask: np.ndarray, grid: list[dict], rows: int, columns: int) -> dict[str, str]:
    overlay = image.copy()
    overlay[mask > 0] = (40, 190, 90)
    overlay = cv2.addWeighted(image, 0.62, overlay, 0.38, 0)
    mask_rgb = np.zeros_like(image)
    mask_rgb[mask > 0] = (40, 190, 90)

    heatmap = image.copy()
    for cell in grid:
        bounds = cell["coordinates"]
        color = {"low": (120, 185, 90), "medium": (40, 180, 230), "high": (60, 75, 235)}[cell["density_category"]]
        cv2.rectangle(heatmap, (bounds["x_min"], bounds["y_min"]), (bounds["x_max"], bounds["y_max"]), color, -1)
        cv2.putText(heatmap, f'{cell["weed_density_percent"]:.1f}%', (bounds["x_min"] + 6, bounds["y_min"] + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.rectangle(heatmap, (bounds["x_min"], bounds["y_min"]), (bounds["x_max"], bounds["y_max"]), (245, 245, 245), 1)
    heatmap = cv2.addWeighted(image, 0.48, heatmap, 0.52, 0)
    return {"original": image_data_url(image), "mask": image_data_url(mask_rgb), "overlay": image_data_url(overlay), "heatmap": image_data_url(heatmap)}
