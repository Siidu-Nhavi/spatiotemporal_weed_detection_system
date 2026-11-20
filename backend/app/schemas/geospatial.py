from typing import Literal

from pydantic import BaseModel


class RasterMetadata(BaseModel):
    width: int
    height: int
    crs: str
    transform: tuple[float, ...]
    bounds: tuple[float, float, float, float]
    nodata: float | int | None = None
    is_projected: bool
    linear_units: str | None = None


class GeospatialStatus(BaseModel):
    coordinate_system: Literal["image_pixels", "geographic"]
    available: bool
    metadata: RasterMetadata | None = None
    note: str
