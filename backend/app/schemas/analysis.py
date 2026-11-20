from typing import Literal

from pydantic import BaseModel, Field


class ImageDimensions(BaseModel):
    width: int
    height: int
    channels: int


class PixelBounds(BaseModel):
    x_min: float
    y_min: float
    x_max: float
    y_max: float


class CoordinateReference(BaseModel):
    system: Literal["image_pixels", "geographic"]
    crs: str | None = None
    note: str


class DensityCell(BaseModel):
    id: str
    row: int
    column: int
    coordinates: PixelBounds
    total_valid_field_pixels: int = Field(ge=0)
    weed_pixels: int = Field(ge=0)
    weed_density_percent: float = Field(ge=0, le=100)
    weed_instance_count: int = Field(ge=0)
    average_detection_confidence: float = Field(ge=0, le=1)
    density_category: Literal["low", "medium", "high"]
