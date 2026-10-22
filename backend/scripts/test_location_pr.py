
import os
import requests

# 1. VWorld API 키 가져오기
API_KEY = os.getenv("VWORLD_API_KEY")

if not API_KEY:
    raise ValueError("VWORLD_API_KEY 환경변수를 설정해 주세요.")

# 2. 조회할 위치 (안산 지역 테스트 좌표)
# 앞서 P61A, P61B가 조회됐던 테스트 좌표
longitude = 129.3019358189357
latitude = 35.323135956891576

point = f"POINT({longitude} {latitude})"

# 3. VWorld API 주소
url = "https://api.vworld.kr/req/data"

# 4. 조회할 공역 종류
airspace_types = {
    "P": "LT_C_AISPRHC",  # 비행금지구역
    "R": "LT_C_AISRESC",  # 비행제한구역
}

# 5. 공역 조회 함수
def get_airspace(airspace_type, data_id):
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
        "key": API_KEY,
    }

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()

    result = response.json()
    response_data = result.get("response", {})
    status = response_data.get("status")

    if status == "NOT_FOUND":
        print(f"{airspace_type} 구역: 조회 결과 없음")
        return []

    if status != "OK":
        raise RuntimeError(
            f"{airspace_type} 구역 API 오류: {status}, "
            f"{response_data.get('error', {})}"
        )

    features = (
        response_data.get("result", {})
        .get("featureCollection", {})
        .get("features", [])
    )

    for feature in features:
        feature.setdefault("properties", {})
        feature["properties"]["airspace_type"] = airspace_type

    print(f"{airspace_type} 구역: {len(features)}개 조회")
    return features


# 6. P 구역과 R 구역 조회
all_features = []

for airspace_type, data_id in airspace_types.items():
    features = get_airspace(airspace_type, data_id)
    all_features.extend(features)

# 7. GeoJSON 데이터 통합
geojson_data = {
    "type": "FeatureCollection",
    "features": all_features,
}

print("--------------------")
print("P/R 통합 조회 완료!")
print("전체 공역 수:", len(all_features))

for feature in all_features:
    properties = feature.get("properties", {})
    print("구역 종류:", properties.get("airspace_type"))
    print("공역 정보:", properties)
    print("좌표 형태:", (feature.get("geometry") or {}).get("type"))
