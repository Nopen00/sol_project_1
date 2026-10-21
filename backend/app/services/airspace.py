import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# backend/.env 파일 불러오기
env_path = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(env_path)

# VWorld API 주소
VWORLD_URL = "https://api.vworld.kr/req/data"

# 조회할 공역 종류
AIRSPACE_TYPES = {
    "P": "LT_C_AISPRHC",  # 비행금지구역
    "R": "LT_C_AISRESC",  # 비행제한구역
}


# 특정 좌표의 공역 조회
def get_airspace(longitude: float, latitude: float):
    api_key = os.getenv("VWORLD_API_KEY")

    if not api_key:
        raise ValueError("VWORLD_API_KEY 환경변수가 설정되지 않았습니다.")

    point = f"POINT({longitude} {latitude})"
    all_features = []

    for airspace_type, data_id in AIRSPACE_TYPES.items():
        params = {
            "service": "data",
            "version": "2.0",
            "request": "GetFeature",
            "format": "json",
            "errorformat": "json",
            "size": 100,
            "page": 1,
            "data": data_id,
            "geomfilter": point,
            "geometry": "true",
            "attribute": "true",
            "crs": "EPSG:4326",
            "domain": "http://localhost:5173",
            "key": api_key,
        }

        response = requests.get(
            VWORLD_URL,
            params=params,
            timeout=15,
        )
        response.raise_for_status()

        result = response.json()
        response_data = result.get("response", {})
        status = response_data.get("status")

        if status == "NOT_FOUND":
            continue

        if status != "OK":
            raise RuntimeError(
                f"{airspace_type} 구역 조회 실패: {status}"
            )

        features = (
            response_data.get("result", {})
            .get("featureCollection", {})
            .get("features", [])
        )

        for feature in features:
            feature.setdefault("properties", {})
            feature["properties"]["airspace_type"] = airspace_type

        all_features.extend(features)

    return {
        "type": "FeatureCollection",
        "features": all_features,
    }
