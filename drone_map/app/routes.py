
import asyncio
import math

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import KAKAO_API_KEY, MAX_GRID_COUNT
from app.grid import to_grid

# 아래 2개 함수는 기존 프로젝트의 실제 함수명에 맞춰 연결하세요.
# get_cached_weather(lat, lon): 캐시를 이용한 비동기 날씨 조회
# calculate_risk(weather): 위험도 계산
from app.cache import get_cached_weather
from app.risk import calculate_risk


router = APIRouter()
templates = Jinja2Templates(directory="templates")

# 기상청 격자의 대략적인 간격
WEATHER_GRID_KM = 5.0


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "kakao_api_key": KAKAO_API_KEY
        }
    )


@router.get("/api/weather")
async def get_weather(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180)
):
    try:
        weather = await get_cached_weather(lat, lon)
        risk = calculate_risk(weather)

        return {
            "weather": weather,
            "risk": risk
        }

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"기상 정보 조회 실패: {exc}"
        )


def estimate_grid_count(
    south: float,
    west: float,
    north: float,
    east: float
) -> int:
    mid_lat = (south + north) / 2

    lat_km = (north - south) * 111.32
    lon_km = (
        (east - west)
        * 111.32
        * max(0.01, math.cos(math.radians(mid_lat)))
    )

    lat_count = max(
        1,
        math.ceil(lat_km / WEATHER_GRID_KM)
    )

    lon_count = max(
        1,
        math.ceil(lon_km / WEATHER_GRID_KM)
    )

    return lat_count * lon_count


def build_sample_points(
    south: float,
    west: float,
    north: float,
    east: float,
    max_count: int
):
    """
    지도 범위에 샘플 지점을 균등 배치합니다.

    주의:
    넓은 지도에서는 일부 기상청 격자만 조회하므로
    전국 위험도를 완전히 조사한 결과가 아닙니다.
    """

    mid_lat = (south + north) / 2

    lat_km = max(
        0.001,
        (north - south) * 111.32
    )

    lon_km = max(
        0.001,
        (east - west)
        * 111.32
        * max(0.01, math.cos(math.radians(mid_lat)))
    )

    aspect = lon_km / lat_km

    lat_count = max(
        1,
        int(math.sqrt(max_count / aspect))
    )

    lon_count = max(
        1,
        int(max_count / lat_count)
    )

    while lat_count * lon_count > max_count:
        if lon_count > 1:
            lon_count -= 1
        elif lat_count > 1:
            lat_count -= 1
        else:
            break

    points = []
    seen = set()

    for i in range(lat_count):
        lat = south + (
            (i + 0.5) / lat_count
        ) * (north - south)

        for j in range(lon_count):
            lon = west + (
                (j + 0.5) / lon_count
            ) * (east - west)

            nx, ny = to_grid(lat, lon)
            key = (nx, ny)

            if key in seen:
                continue

            seen.add(key)
            points.append((lat, lon))

    return points


async def fetch_zone(lat: float, lon: float):
    try:
        weather = await get_cached_weather(lat, lon)
        risk = calculate_risk(weather)

        return {
            "lat": lat,
            "lon": lon,
            "weather": weather,
            "risk": risk
        }

    except Exception as exc:
        return {
            "lat": lat,
            "lon": lon,
            "error": str(exc)
        }


@router.get("/api/weather/zones")
async def get_weather_zones(
    south: float = Query(..., ge=-90, le=90),
    west: float = Query(..., ge=-180, le=180),
    north: float = Query(..., ge=-90, le=90),
    east: float = Query(..., ge=-180, le=180)
):
    if south >= north or west >= east:
        raise HTTPException(
            status_code=400,
            detail="올바르지 않은 지도 범위입니다."
        )

    estimated_count = estimate_grid_count(
        south,
        west,
        north,
        east
    )

    # 최대 40개 지점만 샘플링
    points = build_sample_points(
        south,
        west,
        north,
        east,
        MAX_GRID_COUNT
    )

    # 기존 cache.py의 동시 요청 제한을 활용
    results = await asyncio.gather(
        *[
            fetch_zone(lat, lon)
            for lat, lon in points
        ]
    )

    zones = []
    failed_grids = 0
    errors = []

    for result in results:
        if "error" in result:
            failed_grids += 1
            errors.append(result["error"])
            continue

        risk = result["risk"]
        level = risk.get("level", 0)

        if level <= 0:
            continue

        zones.append({
            "lat": result["lat"],
            "lon": result["lon"],
            "radius": 2500,
            "risk": risk,
            "weather": result["weather"]
        })

    # 추정 범위가 40개를 초과하거나
    # 조회 실패가 발생했다면 불완전한 결과
    complete = (
        estimated_count <= MAX_GRID_COUNT
        and failed_grids == 0
    )

    return {
        "zones": zones,
        "checked_grids": len(points),
        "failed_grids": failed_grids,
        "complete": complete,
        "estimated_grids": estimated_count,
        "errors": errors[:5]
    }
