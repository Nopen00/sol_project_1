from fastapi import APIRouter, HTTPException

from app.services.weather_grid import latlon_to_grid
from app.services.weather_repository import get_weather

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("/point")
def get_weather_point(latitude: float, longitude: float):
    try:
        nx, ny = latlon_to_grid(latitude, longitude)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    weather = get_weather(nx, ny)

    if weather is None:
        raise HTTPException(
            status_code=404,
            detail="해당 지역의 조회 가능한 미래 날씨 예보가 없습니다."
        )

    return {
        "nx": nx,
        "ny": ny,
        "forecast_at": str(weather["forecast_at"]),
        "temperature": weather["temperature"],
        "wind_speed": weather["wind_speed"],
        "precipitation": weather["pcp_raw"],
        "precipitation_type": weather["pty_raw"],
        "precipitation_status": weather["pcp_status"],
        "precipitation_type_status": weather["pty_status"],
    }