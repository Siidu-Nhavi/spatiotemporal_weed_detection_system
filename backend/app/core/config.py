from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    project_root: Path
    model_path: str | None
    max_upload_bytes: int
    default_grid_rows: int
    default_grid_columns: int
    low_density_threshold: float
    high_density_threshold: float


def load_settings() -> Settings:
    backend_root = Path(__file__).resolve().parents[2]
    project_root = backend_root.parent
    default_model = project_root / "backend" / "models" / "cwfid-balanced-30ep.pt"
    configured_model = os.getenv("WEED_MODEL_PATH")
    return Settings(
        project_root=project_root,
        model_path=configured_model or (str(default_model) if default_model.is_file() else None),
        max_upload_bytes=int(os.getenv("MAX_UPLOAD_BYTES", str(15 * 1024 * 1024))),
        default_grid_rows=int(os.getenv("DEFAULT_GRID_ROWS", "8")),
        default_grid_columns=int(os.getenv("DEFAULT_GRID_COLUMNS", "12")),
        low_density_threshold=float(os.getenv("LOW_DENSITY_THRESHOLD", "10")),
        high_density_threshold=float(os.getenv("HIGH_DENSITY_THRESHOLD", "30")),
    )


settings = load_settings()
