from fastapi import APIRouter

router = APIRouter(tags=["dataset"])


@router.post("/dataset/inspect")
def inspect_dataset() -> dict:
    return {
        "status": "not_implemented",
        "message": "Dataset inspection is scheduled for Milestone 2; no dataset is bundled or redistributed.",
    }
