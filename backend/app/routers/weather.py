
import requests
from fastapi import APIRouter, HTTPException, Query

from backend.app.schemas.weather import WeatherResponse
from backend.app.services.weather import get_weather_by_location


router = APIRouter(
    prefix="/api",
    tags=["weather"]
)


@router.get("/weather", response_model=WeatherResponse)
def get_weather(
    latitude: float = Query(..., gt=-89, lt=89),
    longitude: float = Query(..., ge=-180, le=180)
):
    try:
        return get_weather_by_location(latitude, longitude)

    except (requests.RequestException, RuntimeError, KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail="기상청 날씨 정보를 가져오지 못했습니다."
        ) from exc
