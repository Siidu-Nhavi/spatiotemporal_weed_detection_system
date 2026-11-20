from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.services.analysis_service import analyze_field_image
from app.services.geospatial import GeospatialProcessingUnavailable, decode_geotiff
from app.utils.validation import decode_image, validate_upload

router = APIRouter(tags=["analysis"])


@router.post("/analyze")
async def analyze(
    image: UploadFile = File(...),
    rows: int = Form(8),
    columns: int = Form(12),
    low_threshold: float = Form(10.0),
    high_threshold: float = Form(30.0),
) -> dict:
    try:
        validate_upload(image, rows, columns, low_threshold, high_threshold)
        image_bytes = await image.read()
        is_geotiff = (image.filename or "").lower().endswith((".tif", ".tiff"))
        raster_metadata = None
        if is_geotiff:
            image_array, raster_metadata = decode_geotiff(image_bytes)
        else:
            image_array = decode_image(image_bytes)
        return analyze_field_image(
            image_array,
            rows=rows,
            columns=columns,
            low_threshold=low_threshold,
            high_threshold=high_threshold,
            raster_metadata=raster_metadata,
        )
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except GeospatialProcessingUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail="Image analysis failed. Please try another image."
        ) from exc
