
from datetime import datetime, timedelta

import httpx
from fastapi import HTTPException

from app.core.config import KMA_SERVICE_KEY, KMA_URL, KST
from app.services.grid import to_grid


# ==========================================
# 1. 초단기실황 발표 시각 계산
# ==========================================

def observation_base(now):
    base = now.replace(
        minute=0,
        second=0,
        microsecond=0
    )

    # 발표 자료 반영 지연 고려
    if now.minute < 45:
        base -= timedelta(hours=1)

    return base


# ==========================================
# 2. 단기예보 발표 시각 계산
# ==========================================

def forecast_base(now):
    hours = [2, 5, 8, 11, 14, 17, 20, 23]

    # 최신 발표 자료의 반영 지연 고려
    target = now - timedelta(minutes=30)

    for hour in reversed(hours):
        candidate = target.replace(
            hour=hour,
            minute=0,
            second=0,
            microsecond=0
        )

        if candidate <= target:
            return candidate

    return (
        target - timedelta(days=1)
    ).replace(
        hour=23,
        minute=0,
        second=0,
        microsecond=0
    )


# ==========================================
# 3. 기상청 데이터 값 변환
# ==========================================

def parse_weather_value(value):
    if value is None:
        return None

    value = str(value).strip()

    if value in ("", "-", "null"):
        return None

    # 강수나 적설이 없는 경우
    if value in ("강수없음", "적설없음"):
        return 0.0

    try:
        return float(value)

    except ValueError:
        # 예: "1mm 미만", "1cm 미만"
        return value


# ==========================================
# 4. 기상청 API 호출
# ==========================================

async def fetch_kma(
    client,
    endpoint,
    base,
    nx,
    ny
):
    if not KMA_SERVICE_KEY:
        raise ValueError(
            "기상청 API 키가 없습니다. "
            ".env의 KMA_SERVICE_KEY를 확인하세요."
        )

    params = {
        "serviceKey": KMA_SERVICE_KEY,
        "pageNo": 1,
        "numOfRows": 1000,
        "dataType": "JSON",
        "base_date": base.strftime("%Y%m%d"),
        "base_time": base.strftime("%H%M"),
        "nx": nx,
        "ny": ny
    }

    response = await client.get(
        f"{KMA_URL}/{endpoint}",
        params=params
    )

    response.raise_for_status()

    data = response.json()

    header = data["response"]["header"]

    if str(header["resultCode"]) != "00":
        raise ValueError(
            f"{endpoint} 조회 실패 | "
            f"발표시각: {base:%Y-%m-%d %H:%M} | "
            f"격자: ({nx}, {ny}) | "
            f"응답: {header['resultMsg']}"
        )

    return (
        data.get("response", {})
        .get("body", {})
        .get("items", {})
        .get("item", [])
    )


# ==========================================
# 5. 초단기실황 조회
# ==========================================

async def fetch_observation(
    client,
    now,
    nx,
    ny
):
    checked = set()

    for hours_back in [0, 1, 2, 3]:
        base = observation_base(
            now - timedelta(hours=hours_back)
        )

        if base in checked:
            continue

        checked.add(base)

        try:
            items = await fetch_kma(
                client,
                "getUltraSrtNcst",
                base,
                nx,
                ny
            )

            if items:
                return items, base

        except ValueError as exc:
            if "NO_DATA" not in str(exc):
                raise

    raise ValueError(
        "초단기실황 자료가 없습니다."
    )


# ==========================================
# 6. 단기예보 조회
# ==========================================

async def fetch_forecast(
    client,
    now,
    nx,
    ny
):
    checked = set()

    for hours_back in [0, 3, 6, 9, 12]:
        base = forecast_base(
            now - timedelta(hours=hours_back)
        )

        if base in checked:
            continue

        checked.add(base)

        try:
            items = await fetch_kma(
                client,
                "getVilageFcst",
                base,
                nx,
                ny
            )

            if items:
                return items, base

        except ValueError as exc:
            if "NO_DATA" not in str(exc):
                raise

    raise ValueError(
        "단기예보 자료가 없습니다."
    )


# ==========================================
# 7. 가장 가까운 미래 예보값 검색
# ==========================================

def find_forecast_value(
    items,
    category,
    now
):
    now_key = now.strftime("%Y%m%d%H%M")

    candidates = []

    for item in items:
        if item.get("category") != category:
            continue

        forecast_time = (
            item["fcstDate"]
            + item["fcstTime"]
        )

        if forecast_time >= now_key:
            candidates.append(
                (
                    forecast_time,
                    item["fcstValue"]
                )
            )

    if not candidates:
        return None, None

    forecast_time, raw_value = min(
        candidates,
        key=lambda item: item[0]
    )

    return (
        parse_weather_value(raw_value),
        forecast_time
    )


# ==========================================
# 8. 기상 데이터 6개 통합 조회
# ==========================================

async def get_weather_data(
    lat: float,
    lon: float
):
    # 좌표 범위 검사
    if not (
        33 <= lat <= 39.5
        and 124 <= lon <= 132
    ):
        raise HTTPException(
            status_code=400,
            detail="기상청 조회 지원 범위 밖입니다."
        )

    if not KMA_SERVICE_KEY:
        raise HTTPException(
            status_code=500,
            detail=(
                "기상청 API 키가 없습니다. "
                ".env의 KMA_SERVICE_KEY를 확인하세요."
            )
        )

    # 위경도 -> 기상청 격자 좌표
    nx, ny = to_grid(lat, lon)

    # 현재 한국 시간
    now = datetime.now(KST)

    try:
        async with httpx.AsyncClient(
            timeout=15.0
        ) as client:

            # 초단기실황 조회
            obs_items, obs_base = (
                await fetch_observation(
                    client,
                    now,
                    nx,
                    ny
                )
            )

            # 단기예보 조회
            fcst_items, fcst_base = (
                await fetch_forecast(
                    client,
                    now,
                    nx,
                    ny
                )
            )

        # 초단기실황 데이터 정리
        obs = {
            item["category"]: parse_weather_value(
                item.get("obsrValue")
            )
            for item in obs_items
        }

        # 강수확률
        pop, pop_time = find_forecast_value(
            fcst_items,
            "POP",
            now
        )

        # 적설량
        sno, sno_time = find_forecast_value(
            fcst_items,
            "SNO",
            now
        )

        # ==================================
        # 최종 JSON 응답
        # ==================================

        return {
            "location": {
                "lat": lat,
                "lon": lon,
                "nx": nx,
                "ny": ny
            },

            "observation_time": (
                obs_base.isoformat()
            ),

            "forecast_base_time": (
                fcst_base.isoformat()
            ),

            "forecast_time": pop_time,

            "snowfall_forecast_time": sno_time,

            # 기상 데이터 6개
            "temperature": obs.get("T1H"),
            "wind_speed": obs.get("WSD"),
            "wind_direction": obs.get("VEC"),
            "precipitation": obs.get("RN1"),
            "precipitation_probability": pop,
            "snowfall": sno
        }

    except (
        httpx.HTTPError,
        ValueError,
        KeyError,
        TypeError,
        AttributeError
    ) as exc:

        raise HTTPException(
            status_code=502,
            detail=(
                f"기상청 API 조회 실패: {exc}"
            )
        ) from exc
