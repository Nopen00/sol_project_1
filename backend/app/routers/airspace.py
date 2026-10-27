import logging
from app.services.airspace import AirspaceUpstreamError

logger = logging.getLogger(__name__)
from fastapi import APIRouter, HTTPException, Query
from app.services.airspace_analysis import analyze_airspace
from app.schemas.airspace import AirspaceGeoJSONResponse, AirspaceAnalysisResponse

from app.services.airspace import get_airspace

router = APIRouter(prefix="/airspace", tags=["공역 정보"])


@router.get("", response_model=AirspaceGeoJSONResponse)
def read_airspace(
    longitude: float = Query(..., ge=-180, le=180),
    latitude: float = Query(..., ge=-90, le=90),
):
    try:
        result = get_airspace(longitude, latitude)
        return result

    except AirspaceUpstreamError:
        raise HTTPException(
            status_code=502,
            detail="공역 정보를 조회하는 중 오류가 발생했습니다.",
        )

@router.get("/analysis", response_model=AirspaceAnalysisResponse)
def read_airspace_analysis(
    longitude: float = Query(..., ge=-180, le=180),
    latitude: float = Query(..., ge=-90, le=90),
):
    try:
        # 1. VWorld에서 공역 조회
        geojson = get_airspace(longitude, latitude)

        # 2. 조회한 공역 분석
        result = analyze_airspace(geojson)

        # 3. 분석 결과 반환
        return result

    except AirspaceUpstreamError:
        raise HTTPException(
            status_code=502,
            detail="공역 분석 중 오류가 발생했습니다."
        )
