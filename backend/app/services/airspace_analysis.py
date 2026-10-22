def analyze_airspace(geojson: dict) -> dict:
    features = geojson.get("features", [])

    airspace_types = {
        feature.get("properties", {}).get("airspace_type")
        for feature in features
    }

    if "P" in airspace_types:
        status = "PROHIBITED_AIRSPACE"
        message = "비행금지구역(P)이 조회되었습니다."

    elif "R" in airspace_types:
        status = "RESTRICTED_AIRSPACE"
        message = "비행제한구역(R)이 조회되었습니다. 승인 요건을 확인하세요."

    else:
        status = "ADDITIONAL_CHECK_REQUIRED"
        message = "조회된 P/R 공역이 없습니다. 다른 비행 제한 사항도 확인해야 합니다."

    return {
        "status": status,
        "message": message,
        "airspace_count": len(features),
    }
