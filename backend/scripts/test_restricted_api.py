import os
import requests

API_KEY = os.getenv("VWORLD_API_KEY")

if not API_KEY:
    raise ValueError("VWORLD_API_KEY 환경변수를 설정해 주세요.")

url = "https://api.vworld.kr/req/data"

params = {
    "service": "data",
    "version": "2.0",
    "request": "GetFeature",
    "format": "json",
    "errorformat": "json",
    "size": 10,
    "page": 1,
    "data": "LT_C_AISRESC",
    "geomfilter": "POINT(127.50951656820993 37.52862499999995)",
    "geometry": "true",
    "attribute": "true",
    "crs": "EPSG:4326",
    "domain": "http://localhost:5173",
    "key": API_KEY,
}

response = requests.get(url, params=params, timeout=15)
response.raise_for_status()

result = response.json()
response_data = result.get("response", {})

print("API 상태:", response_data.get("status"))

features = (
    response_data.get("result", {})
    .get("featureCollection", {})
    .get("features", [])
)

print("조회된 비행제한구역 수:", len(features))

for feature in features:
    print("--------------------")
    print("공역 정보:", feature.get("properties"))
    print("좌표 형태:", feature.get("geometry", {}).get("type"))


import json
from pathlib import Path

# GeoJSON 데이터 만들기
geojson_data = {
    "type": "FeatureCollection",
    "features": features
}

# 저장할 폴더 설정
output_dir = Path("data/raw")
output_dir.mkdir(parents=True, exist_ok=True)

# 저장할 파일 이름
output_file = output_dir / "test_restricted.geojson"

# GeoJSON 파일 저장
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(geojson_data, f, ensure_ascii=False, indent=2)

print("비행제한구역 GeoJSON 저장 완료!")
print("저장 위치:", output_file)
print("공역 개수:", len(features))
