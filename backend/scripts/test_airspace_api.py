import os
import requests

# 1. 환경변수에서 VWorld 개발키 가져오기
API_KEY = os.getenv("VWORLD_API_KEY")

if not API_KEY:
    raise ValueError("VWORLD_API_KEY 환경변수를 설정해 주세요.")

# 2. VWorld API 주소
url = "https://api.vworld.kr/req/data"

# 3. API 요청에 필요한 정보
params = {
    "service": "data",
    "version": "2.0",
    "request": "GetFeature",
    "format": "json",
    "errorformat": "json",
    "size": 10,
    "page": 1,
    "data": "LT_C_AISPRHC",
    "geomfilter": "POINT(129.3019358189357 35.323135956891576)",
    "columns": "prohibited,prh_lbl_1,prh_lbl_2,prh_lbl_3,prh_typ,ag_geom",
    "geometry": "true",
    "attribute": "true",
    "buffer": 10,
    "crs": "EPSG:4326",
    "domain": "http://localhost:5173",
    "key": API_KEY,
}

# 4. API에 데이터 요청하기
response = requests.get(url, params=params, timeout=15)

# 5. HTTP 오류 확인하기
response.raise_for_status()

# 6. 응답을 JSON 데이터로 변환하기
result = response.json()

# 7. 결과 출력하기

# API 응답 상태 확인
response_data = result.get("response", {})

print("API 상태:", response_data.get("status"))

# 비행금지구역 데이터 확인
features = response_data.get("result", {}).get("featureCollection", {}).get("features", [])

print("조회된 비행금지구역 수:", len(features))

for feature in features:
    print("--------------------")
    print("공역 정보:", feature.get("properties"))
    print("좌표 형태:", feature.get("geometry", {}).get("type"))

for feature in features:
    print("--------------------")
    print("공역 정보:", feature.get("properties"))

    geometry = feature.get("geometry", {})
    print("좌표 형태:", geometry.get("type"))
    print("좌표 데이터 존재:", bool(geometry.get("coordinates")))


# GeoJSON 데이터 구성
geojson_data = {
    "type": "FeatureCollection",
    "features": features
}

print("GeoJSON 생성 성공!")
print("공역 개수:", len(geojson_data["features"]))
print("첫 번째 공역:", geojson_data["features"][0]["properties"]["prh_lbl_1"])


import json
from pathlib import Path

# 저장할 폴더 경로
output_dir = Path("data/raw")
output_dir.mkdir(parents=True, exist_ok=True)

# 저장할 파일 경로
output_file = output_dir / "test_airspace.geojson"

# GeoJSON 파일 저장
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(geojson_data, f, ensure_ascii=False, indent=2)

print("GeoJSON 파일 저장 완료!")
print("저장 위치:", output_file)
