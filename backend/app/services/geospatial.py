"""GeoTIFF decoding and pixel-to-CRS conversion."""

from __future__ import annotations

from io import BytesIO

import cv2
import numpy as np

from app.schemas.geospatial import RasterMetadata


class GeospatialProcessingUnavailable(RuntimeError):
    """Raised when GeoTIFF support is not installed."""


def decode_geotiff(image_bytes: bytes) -> tuple[np.ndarray, RasterMetadata]:
    """Decode a GeoTIFF into an OpenCV-compatible image and preserve its CRS."""
    try:
        import rasterio
    except ImportError as exc:
        raise GeospatialProcessingUnavailable(
            "GeoTIFF support requires the rasterio dependency."
        ) from exc

    with rasterio.MemoryFile(BytesIO(image_bytes)) as memory_file:
        with memory_file.open() as dataset:
            bands = dataset.read()
            if bands.shape[0] == 1:
                image = _scale_band_to_uint8(bands[0])
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            elif bands.shape[0] >= 3:
                image = np.stack(
                    [_scale_band_to_uint8(bands[index]) for index in range(3)],
                    axis=-1,
                )
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            else:
                raise ValueError("GeoTIFF must contain one or at least three bands.")

            if dataset.crs is None:
                raise ValueError("GeoTIFF must contain a coordinate reference system (CRS).")

            metadata = RasterMetadata(
                width=dataset.width,
                height=dataset.height,
                crs=dataset.crs.to_string(),
                transform=tuple(float(value) for value in dataset.transform),
                bounds=(
                    float(dataset.bounds.left),
                    float(dataset.bounds.bottom),
                    float(dataset.bounds.right),
                    float(dataset.bounds.top),
                ),
                nodata=float(dataset.nodata) if dataset.nodata is not None else None,
                is_projected=bool(dataset.crs.is_projected),
                linear_units=dataset.crs.linear_units,
            )
            return image, metadata


def pixel_bounds_to_crs(
    pixel_bounds: dict[str, float],
    transform: tuple[float, ...],
) -> dict[str, float]:
    """Return the CRS-aligned envelope for a pixel rectangle."""
    if len(transform) < 6:
        raise ValueError("A raster transform must contain at least six coefficients.")
    affine = _affine_from_tuple(transform)
    corners = [
        affine @ (pixel_bounds["x_min"], pixel_bounds["y_min"]),
        affine @ (pixel_bounds["x_max"], pixel_bounds["y_min"]),
        affine @ (pixel_bounds["x_min"], pixel_bounds["y_max"]),
        affine @ (pixel_bounds["x_max"], pixel_bounds["y_max"]),
    ]
    x_values = [point[0] for point in corners]
    y_values = [point[1] for point in corners]
    return {
        "x_min": min(x_values),
        "y_min": min(y_values),
        "x_max": max(x_values),
        "y_max": max(y_values),
    }


def pixel_area(transform: tuple[float, ...]) -> float:
    """Return the area represented by one pixel in CRS square units."""
    if len(transform) < 6:
        raise ValueError("A raster transform must contain at least six coefficients.")
    return abs(transform[0] * transform[4] - transform[1] * transform[3])


def _scale_band_to_uint8(band: np.ndarray) -> np.ndarray:
    if band.dtype == np.uint8:
        return band
    values = band.astype(np.float32)
    valid = np.isfinite(values)
    if not np.any(valid):
        return np.zeros(values.shape, dtype=np.uint8)
    minimum = float(values[valid].min())
    maximum = float(values[valid].max())
    if maximum <= minimum:
        return np.zeros(values.shape, dtype=np.uint8)
    scaled = (values - minimum) * (255.0 / (maximum - minimum))
    return np.clip(scaled, 0, 255).astype(np.uint8)


def _affine_from_tuple(transform: tuple[float, ...]):
    try:
        from affine import Affine
    except ImportError as exc:
        raise GeospatialProcessingUnavailable(
            "GeoTIFF support requires rasterio and affine dependencies."
        ) from exc
    return Affine(*transform[:6])
