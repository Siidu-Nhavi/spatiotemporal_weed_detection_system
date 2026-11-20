from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.analysis import router as analysis_router
from app.routes.dataset import router as dataset_router
from app.routes.exports import router as exports_router
from app.routes.model import router as model_router

app = FastAPI(
    title="Closed-Loop Weed State Estimation",
    version="0.1.0",
    description="Image-coordinate weed detection and spatial density analysis.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analysis_router, prefix="/api")
app.include_router(dataset_router, prefix="/api")
app.include_router(exports_router, prefix="/api")
app.include_router(model_router, prefix="/api")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "weed-analysis-api"}
