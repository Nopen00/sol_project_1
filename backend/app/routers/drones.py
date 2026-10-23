from app.schemas.drone import DroneResponse
from fastapi import APIRouter
from app.services.drone_repository import get_drones as list_drones

router = APIRouter()


@router.get("/drones", response_model=list[DroneResponse])
def get_drones():
    return list_drones()
