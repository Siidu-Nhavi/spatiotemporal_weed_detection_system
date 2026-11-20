import numpy as np

from app.schemas.geospatial import RasterMetadata
from app.services.geospatial import pixel_area, pixel_bounds_to_crs
from app.services.rendering import render_outputs
from app.services.spatial_mapper import build_grid
from app.services.weed_detector import WeedDetector

detector = WeedDetector()


def analyze_field_image(
    image: np.ndarray,
    rows: int,
    columns: int,
    low_threshold: float,
    high_threshold: float,
    raster_metadata: RasterMetadata | None = None,
) -> dict:
    detection = detector.predict(image)
    grid = build_grid(detection.weed_mask, detection.instances, rows, columns, low_threshold, high_threshold)
    if raster_metadata is not None:
        for cell in grid:
            cell["spatial_coordinates"] = pixel_bounds_to_crs(
                cell["coordinates"],
                raster_metadata.transform,
            )
            if raster_metadata.is_projected:
                cell["valid_field_area_square_units"] = round(
                    cell["total_valid_field_pixels"] * pixel_area(raster_metadata.transform),
                    6,
                )
    height, width = image.shape[:2]
    weed_pixels = int(np.count_nonzero(detection.weed_mask))
    coverage = weed_pixels / (height * width) * 100
    category_counts = {category: sum(1 for cell in grid if cell["density_category"] == category) for category in ("low", "medium", "high")}
    hottest = max(grid, key=lambda cell: cell["weed_density_percent"], default=None)
    hotspot_cells = [
        cell for cell in grid if cell["density_category"] == "high"
    ]
    confidence_values = [item["confidence"] for item in detection.instances if item["confidence"] > 0]
    return {
        "schema_version": "1.0",
        "coordinate_system": "geographic" if raster_metadata is not None else "image_pixels",
        "image": {"width": width, "height": height, "channels": 3},
        "geospatial": (
            {
                "available": True,
                "crs": raster_metadata.crs,
                "transform": list(raster_metadata.transform),
                "bounds": list(raster_metadata.bounds),
                "nodata": raster_metadata.nodata,
                "area_unit": raster_metadata.linear_units if raster_metadata.is_projected else None,
            }
            if raster_metadata is not None
            else {
                "available": False,
                "crs": None,
                "note": "Ordinary images use image-pixel coordinates; no GPS or CRS was inferred.",
            }
        ),
        "detection": {
            "mode": detection.mode,
            "model_name": detection.model_name,
            "note": detection.note,
            "instances": detection.instances,
            "instance_count": len(detection.instances),
            "weed_pixels": weed_pixels,
            "weed_coverage_percent": round(coverage, 3),
            "average_confidence": round(sum(confidence_values) / len(confidence_values), 4) if confidence_values else 0,
        },
        "grid": {"rows": rows, "columns": columns, "low_threshold": low_threshold, "high_threshold": high_threshold, "cells": grid},
        "statistics": {
            "low_density_cells": category_counts["low"],
            "medium_density_cells": category_counts["medium"],
            "high_density_cells": category_counts["high"],
            "hotspot_count": len(hotspot_cells),
            "hotspot_cells": hotspot_cells,
            "highest_density_region": hottest,
        },
        "renders": render_outputs(image, detection.weed_mask, grid, rows, columns),
    }
