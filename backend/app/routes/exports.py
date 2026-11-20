from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from app.services.analysis_service import analyze_field_image
from app.services.export import (
    ExportUnavailable,
    decode_mask_render,
    grid_to_geojson,
    mask_to_geotiff,
    mask_to_png,
)
from app.services.geospatial import GeospatialProcessingUnavailable, decode_geotiff
from app.utils.validation import decode_image, validate_upload

router = APIRouter(prefix="/export", tags=["exports"])


@router.post("")
async def export_analysis(
    image: UploadFile = File(...),
    export_format: str = Form("geojson"),
    rows: int = Form(8),
    columns: int = Form(12),
    low_threshold: float = Form(10.0),
    high_threshold: float = Form(30.0),
) -> Response:
    try:
        validate_upload(image, rows, columns, low_threshold, high_threshold)
        image_bytes = await image.read()
        is_geotiff = (image.filename or "").lower().endswith((".tif", ".tiff"))
        raster_metadata = None
        if is_geotiff:
            image_array, raster_metadata = decode_geotiff(image_bytes)
        else:
            image_array = decode_image(image_bytes)

        result = analyze_field_image(
            image_array,
            rows=rows,
            columns=columns,
            low_threshold=low_threshold,
            high_threshold=high_threshold,
            raster_metadata=raster_metadata,
        )
        normalized_format = export_format.lower()
        if normalized_format == "geojson":
            return Response(grid_to_geojson(result), media_type="application/geo+json")
        if normalized_format == "png":
            mask = decode_mask_render(result)
            return Response(mask_to_png(mask), media_type="image/png")
        if normalized_format in {"geotiff", "tif", "tiff"}:
            if raster_metadata is None:
                raise HTTPException(
                    status_code=422,
                    detail="GeoTIFF export requires a GeoTIFF source with CRS metadata.",
                )
            mask = decode_mask_render(result)
            return Response(
                mask_to_geotiff(mask, raster_metadata),
                media_type="image/tiff",
            )
        raise HTTPException(status_code=422, detail="Export format must be geojson, png, or geotiff.")
    except (GeospatialProcessingUnavailable, ExportUnavailable) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
