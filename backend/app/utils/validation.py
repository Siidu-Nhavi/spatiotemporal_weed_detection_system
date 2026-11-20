import cv2
import numpy as np
from fastapi import HTTPException, UploadFile

MAX_UPLOAD_BYTES = 15 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/tiff",
    "image/x-tiff",
    "application/geotiff",
    "application/octet-stream",
}


def validate_upload(
    upload: UploadFile,
    rows: int,
    columns: int,
    low_threshold: float,
    high_threshold: float,
) -> None:
    filename = (upload.filename or "").lower()
    is_geotiff = filename.endswith((".tif", ".tiff"))
    if upload.content_type not in ALLOWED_CONTENT_TYPES or (
        upload.content_type == "application/octet-stream" and not is_geotiff
    ):
        raise HTTPException(
            status_code=415,
            detail="Only JPG, JPEG, PNG, and GeoTIFF images are supported.",
        )
    if rows < 1 or rows > 32 or columns < 1 or columns > 32:
        raise HTTPException(status_code=422, detail="Grid rows and columns must be between 1 and 32.")
    if low_threshold < 0 or high_threshold > 100 or low_threshold >= high_threshold:
        raise HTTPException(status_code=422, detail="Density thresholds must satisfy 0 <= low < high <= 100.")


def decode_image(image_bytes: bytes) -> np.ndarray:
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image must be 15 MB or smaller.")
    decoded = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    if decoded is None:
        raise HTTPException(status_code=400, detail="The uploaded file could not be decoded.")
    return decoded
