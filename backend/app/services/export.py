"""Export helpers for GeoJSON and aligned weed masks."""

from __future__ import annotations

import base64
import json
from io import BytesIO

import cv2
import numpy as np


class ExportUnavailable(RuntimeError):
    """Raised when a requested export cannot preserve its spatial reference."""


def grid_to_geojson(result: dict) -> bytes:
    """Serialize analysis grid cells as a GeoJSON FeatureCollection."""
    features = []
    for cell in result["grid"]["cells"]:
        bounds = cell.get("spatial_coordinates") or cell["coordinates"]
        x_min, y_min = bounds["x_min"], bounds["y_min"]
        x_max, y_max = bounds["x_max"], bounds["y_max"]
        features.append(
            {
                "type": "Feature",
                "id": cell["id"],
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [x_min, y_min],
                        [x_max, y_min],
                        [x_max, y_max],
                        [x_min, y_max],
                        [x_min, y_min],
                    ]],
                },
                "properties": {
                    key: value
                    for key, value in cell.items()
                    if key not in {"coordinates", "spatial_coordinates"}
                },
            }
        )
    document = {
        "type": "FeatureCollection",
        "features": features,
        "properties": {
            "coordinate_system": result["coordinate_system"],
            "crs": result.get("geospatial", {}).get("crs"),
            "note": (
                "Coordinates are image pixels."
                if result["coordinate_system"] == "image_pixels"
                else "Coordinates are in the source GeoTIFF CRS."
            ),
        },
    }
    return json.dumps(document, separators=(",", ":")).encode("utf-8")


def decode_mask_render(result: dict) -> np.ndarray:
    """Recover the binary mask from the aligned PNG render in an analysis result."""
    encoded = result["renders"]["mask"].split(",", 1)[1]
    decoded = cv2.imdecode(
        np.frombuffer(base64.b64decode(encoded), dtype=np.uint8),
        cv2.IMREAD_GRAYSCALE,
    )
    if decoded is None:
        raise ValueError("Could not decode the analysis mask.")
    return np.where(decoded > 0, 255, 0).astype(np.uint8)


def mask_to_png(mask: np.ndarray) -> bytes:
    success, encoded = cv2.imencode(".png", mask)
    if not success:
        raise ValueError("Could not encode the weed mask.")
    return encoded.tobytes()


def mask_to_geotiff(mask: np.ndarray, metadata: object) -> bytes:
    """Write a single-band mask GeoTIFF using the source raster CRS."""
    try:
        import rasterio
        from affine import Affine
    except ImportError as exc:
        raise ExportUnavailable("GeoTIFF export requires rasterio.") from exc

    output = BytesIO()
    with rasterio.open(
        output,
        "w",
        driver="GTiff",
        width=metadata.width,
        height=metadata.height,
        count=1,
        dtype="uint8",
        crs=metadata.crs,
        transform=Affine(*metadata.transform[:6]),
        nodata=0,
        compress="deflate",
    ) as dataset:
        dataset.write(mask, 1)
    return output.getvalue()
