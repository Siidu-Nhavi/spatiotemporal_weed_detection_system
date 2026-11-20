from pathlib import Path

from app.core.config import settings


def get_model_status() -> dict:
    model_path = Path(settings.model_path) if settings.model_path else None
    return {
        "configured": model_path is not None,
        "available": bool(model_path and model_path.is_file()),
        "model_path": str(model_path) if model_path else None,
        "mode": "custom_model" if model_path and model_path.is_file() else "demo",
        "note": (
            "A trained agricultural segmentation model is available."
            if model_path and model_path.is_file()
            else "No trained agricultural model is configured; analysis will be explicitly labelled DEMO MODE."
        ),
    }
