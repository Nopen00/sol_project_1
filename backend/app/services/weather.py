
import requests

KMA_API_URL = (
    "https://apis.data.go.kr/1360000/"
    "VilageFcstInfoService_2.0/getUltraSrtNcst"
)


def fetch_current_weather(
    service_key: str,
    base_date: str,
    base_time: str,
    nx: int,
    ny: int,
):
    params = {
        "serviceKey": service_key,
        "pageNo": 1,
        "numOfRows": 100,
        "dataType": "JSON",
        "base_date": base_date,
        "base_time": base_time,
        "nx": nx,
        "ny": ny,
    }

    response = requests.get(
        KMA_API_URL,
        params=params,
        timeout=10,
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"기상청 API 접속 오류: {response.status_code}"
        )

    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError(
            "기상청 API 응답이 JSON 형식이 아닙니다."
        ) from exc

    header = data.get("response", {}).get("header", {})

    if str(header.get("resultCode")) != "00":
        raise RuntimeError(
            f"기상청 API 응답 오류: {header.get('resultMsg')}"
        )

    return data["response"]["body"]["items"]["item"]

import math


def latlon_to_grid(latitude: float, longitude: float) -> tuple[int, int]:
    """위도·경도를 기상청 5km 격자 좌표로 변환합니다."""
    if not (-89 < latitude < 89 and -180 <= longitude <= 180):
        raise ValueError("위도 또는 경도가 올바르지 않습니다.")

    re = 6371.00877 / 5.0
    rad = math.pi / 180

    slat1 = 30 * rad
    slat2 = 60 * rad
    olon = 126 * rad
    olat = 38 * rad

    sn = math.log(math.cos(slat1) / math.cos(slat2))
    sn /= math.log(
        math.tan(math.pi / 4 + slat2 / 2)
        / math.tan(math.pi / 4 + slat1 / 2)
    )

    sf = math.tan(math.pi / 4 + slat1 / 2) ** sn
    sf *= math.cos(slat1) / sn

    ro = re * sf / math.tan(math.pi / 4 + olat / 2) ** sn
    ra = re * sf / math.tan(math.pi / 4 + latitude * rad / 2) ** sn

    theta = longitude * rad - olon
    if theta > math.pi:
        theta -= 2 * math.pi
    elif theta < -math.pi:
        theta += 2 * math.pi
    theta *= sn

    nx = math.floor(ra * math.sin(theta) + 43 + 0.5)
    ny = math.floor(ro - ra * math.cos(theta) + 136 + 0.5)

    return nx, ny

from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import unquote


def get_weather_by_location(latitude: float, longitude: float):
    # 1. 위도·경도를 기상청 격자로 변환
    nx, ny = latlon_to_grid(latitude, longitude)

    # 2. .env 파일에서 인증키 읽기
    env_path = Path(__file__).resolve().parents[2] / ".env"
    lines = env_path.read_text(encoding="utf-8").splitlines()

    key = next(
        (
            line.partition("=")[2].strip()
            for line in lines
            if line.startswith("KMA_SERVICE_KEY=")
        ),
        ""
    )

    if not key:
        raise RuntimeError("기상청 API 인증키가 없습니다.")

    # 3. 한국 시간 기준 조회 시각 설정
    kst = timezone(timedelta(hours=9))
    base_at = datetime.now(kst) - timedelta(hours=1)

    # 4. 기상청 API 호출
    items = fetch_current_weather(
        unquote(key),
        base_at.strftime("%Y%m%d"),
        base_at.strftime("%H00"),
        nx,
        ny
    )

    # 5. 날씨 항목 정리
    values = {
        item["category"]: item["obsrValue"]
        for item in items
    }

    if not values:
        raise RuntimeError("조회된 날씨 데이터가 없습니다.")

    return {
        "latitude": latitude,
        "longitude": longitude,
        "nx": nx,
        "ny": ny,
        "base_date": base_at.strftime("%Y%m%d"),
        "base_time": base_at.strftime("%H00"),
        "temperature": values.get("T1H"),
        "wind_speed": values.get("WSD"),
        "wind_direction": values.get("VEC"),
        "rainfall": values.get("RN1")
    }
