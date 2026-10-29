
from datetime import date, datetime
from decimal import Decimal

import oracledb
from fastapi import APIRouter, HTTPException, Query

from app.services.weather_grid import latlon_to_grid
from app.services.weather_repository import get_weather as get_db_weather


router = APIRouter(
    prefix="/api",
    tags=["weather"]
)


def serialize_value(value):
    """날짜와 Decimal 값을 JSON으로 변환"""
    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, Decimal):
        return float(value)

    return value


@router.get("/weather")
def get_weather(
    latitude: float = Query(..., gt=-89, lt=89),
    longitude: float = Query(..., ge=-180, le=180),
):
    # 위도·경도를 기상청 격자 좌표로 변환
    try:
        nx, ny = latlon_to_grid(latitude, longitude)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    # Oracle DB에서 날씨 데이터 조회
    try:
        weather = get_db_weather(nx, ny)

    except (oracledb.Error, ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=503,
            detail="날씨 데이터베이스 조회에 실패했습니다.",
        ) from exc

    if weather is None:
        raise HTTPException(
            status_code=404,
            detail="해당 지역에 조회 가능한 미래 날씨 데이터가 없습니다.",
        )

    return {
        "status": "success",
        "source": "oracle",
        "location": {
            "latitude": latitude,
            "longitude": longitude,
            "nx": nx,
            "ny": ny,
        },
        "weather": {
            key: serialize_value(value)
            for key, value in weather.items()
        },
    }
