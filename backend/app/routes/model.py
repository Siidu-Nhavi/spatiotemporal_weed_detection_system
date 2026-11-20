from fastapi import APIRouter

from app.services.model_status import get_model_status

router = APIRouter(tags=["model"])


@router.get("/model/status")
def model_status() -> dict:
    return get_model_status()
