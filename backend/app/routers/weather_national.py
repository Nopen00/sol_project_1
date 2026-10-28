
from datetime import date

from fastapi import APIRouter, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from sqlalchemy.exc import SQLAlchemyError

from backend.app.services.weather_national_query import get_weather


router = APIRouter(tags=["전국 날씨"])


@router.get("/api/weather/national")
def read_national_weather(
    forecast_date: date = Query(..., alias="date"),
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
):
    try:
        rows = get_weather(
            day=forecast_date.isoformat(),
            latitude=latitude,
            longitude=longitude,
        )

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="조회할 수 없는 위도 또는 경도입니다.",
        ) from None

    except (SQLAlchemyError, RuntimeError):
        raise HTTPException(
            status_code=503,
            detail="Oracle 날씨 데이터 조회에 실패했습니다.",
        ) from None

    return {
        "status": "success",
        "source": "oracle",
        "date": forecast_date.isoformat(),
        "location": {
            "latitude": latitude,
            "longitude": longitude,
        },
        "count": len(rows),
        "forecasts": jsonable_encoder(rows),
    }
