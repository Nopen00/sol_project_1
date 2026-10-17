import json
from pathlib import Path

# 프로젝트 폴더 경로
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "raw"

# 기존 GeoJSON 파일 읽기
with open(DATA_DIR / "test_airspace.geojson", encoding="utf-8") as f:
    prohibited_data = json.load(f)

with open(DATA_DIR / "test_restricted.geojson", encoding="utf-8") as f:
    restricted_data = json.load(f)

# 비행금지구역과 비행제한구역 구분하기
features = []

for feature in prohibited_data["features"]:
    feature["properties"]["airspace_type"] = "P"
    features.append(feature)

for feature in restricted_data["features"]:
    feature["properties"]["airspace_type"] = "R"
    features.append(feature)

# GeoJSON 데이터 통합
merged_data = {
    "type": "FeatureCollection",
    "features": features
}

# 통합 파일 저장
output_file = DATA_DIR / "test_merged_airspace.geojson"

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(merged_data, f, ensure_ascii=False, indent=2)

print("공역 데이터 통합 완료!")
print("전체 공역 수:", len(features))
print("저장 위치:", output_file)


# 통합된 공역 데이터 확인
print("\n===== 통합 데이터 확인 =====")

for feature in merged_data["features"]:
    properties = feature.get("properties", {})
    geometry = feature.get("geometry") or {}

    airspace_type = properties.get("airspace_type")

    # P 구역과 R 구역의 공역 코드 필드가 다를 수 있음
    if airspace_type == "P":
        name = properties.get("prh_lbl_1")
    else:
        name = properties.get("res_lbl_1")

    print("--------------------")
    print("구역 종류:", airspace_type)
    print("공역 코드:", name or properties)
    print("좌표 형태:", geometry.get("type"))
    print("좌표 존재:", bool(geometry.get("coordinates")))
