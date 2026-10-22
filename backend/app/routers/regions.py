import json
from pathlib import Path
from fastapi import APIRouter

router = APIRouter(prefix="/regions", tags=["regions"])

REGIONS_PATH = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "regions.json"
)


@router.get("")
def get_regions():
    with REGIONS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)