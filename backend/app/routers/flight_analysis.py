from app.schemas.flight_analysis import FlightAnalysisResponse
from fastapi import APIRouter, HTTPException

from app.services.flight_analysis import analyze_flight
from app.services.weather_grid import latlon_to_grid

router = APIRouter()


@router.get("/flight-analysis", response_model=FlightAnalysisResponse)
def get_flight_analysis(
    model_id: str,
    nx: int | None = None,
    ny: int | None = None,
    latitude: float | None = None,
    longitude: float | None = None,

):
    # 위도,경도가 전달되면 격자 좌표로 변환
    if latitude is not None and longitude is not None:
        try:
            nx, ny = latlon_to_grid(latitude, longitude)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))


    # 격자 좌표가 없으면 오류
    if nx is None or ny is None:
        raise HTTPException(
            status_code=400,
            detail="위도,경도 또는 NX-NY 좌표가 필요합니다.",
        )

    result = analyze_flight(model_id, nx, ny)

    if "error" in result:
        raise HTTPException(
            status_code=404,
            detail=result["error"]
        )

    return result