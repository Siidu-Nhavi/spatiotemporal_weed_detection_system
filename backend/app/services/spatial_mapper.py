import cv2
import numpy as np


def build_grid(
    mask: np.ndarray,
    instances: list[dict],
    rows: int,
    columns: int,
    low_threshold: float,
    high_threshold: float,
) -> list[dict]:
    image_height, image_width = mask.shape
    grid: list[dict] = []
    for row in range(rows):
        y_min = round(row * image_height / rows)
        y_max = round((row + 1) * image_height / rows)
        for column in range(columns):
            x_min = round(column * image_width / columns)
            x_max = round((column + 1) * image_width / columns)
            cell_mask = mask[y_min:y_max, x_min:x_max]
            total_pixels = int(cell_mask.size)
            weed_pixels = int(cv2.countNonZero(cell_mask))
            density = weed_pixels / total_pixels * 100 if total_pixels else 0
            cell_instances = [
                item for item in instances
                if item["bbox"]["x_max"] > x_min and item["bbox"]["x_min"] < x_max
                and item["bbox"]["y_max"] > y_min and item["bbox"]["y_min"] < y_max
            ]
            category = "low" if density < low_threshold else "medium" if density <= high_threshold else "high"
            grid.append(
                {
                    "id": f"r{row + 1}c{column + 1}",
                    "row": row,
                    "column": column,
                    "coordinates": {"x_min": x_min, "y_min": y_min, "x_max": x_max, "y_max": y_max},
                    "total_valid_field_pixels": total_pixels,
                    "weed_pixels": weed_pixels,
                    "weed_density_percent": round(density, 3),
                    "weed_instance_count": len(cell_instances),
                    "average_detection_confidence": round(
                        sum(item["confidence"] for item in cell_instances) / len(cell_instances), 4
                    ) if cell_instances else 0,
                    "density_category": category,
                }
            )
    return grid
