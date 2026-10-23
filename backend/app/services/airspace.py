import logging
import requests

logger = logging.getLogger(__name__)


class AirspaceUpstreamError(RuntimeError):
    """VWorld request or response could not be processed safely."""

from app.core.config import get_settings

# VWorld API 주소
VWORLD_URL = "https://api.vworld.kr/req/data"

# 조회할 공역 종류
AIRSPACE_TYPES = {
    "P": "LT_C_AISPRHC",  # 비행금지구역
    "R": "LT_C_AISRESC",  # 비행제한구역
}


# 특정 좌표의 공역 조회
def get_airspace(longitude: float, latitude: float):
    settings = get_settings()
    api_key = settings.VWORLD_API_KEY

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
            "domain": settings.VWORLD_DOMAIN,
            "key": api_key,
        }

        try:
            response = requests.get(VWORLD_URL, params=params, timeout=15)
            response.raise_for_status()
            result = response.json()
        except requests.Timeout as exc:
            logger.warning("VWorld request timed out (airspace=%s)", airspace_type)
            raise AirspaceUpstreamError("VWorld request timed out") from exc
        except (requests.RequestException, ValueError) as exc:
            logger.warning("VWorld request failed (airspace=%s, type=%s)", airspace_type, type(exc).__name__)
            raise AirspaceUpstreamError("VWorld request failed") from exc

        if not isinstance(result, dict) or not isinstance(result.get("response"), dict):
            raise AirspaceUpstreamError("Invalid VWorld response")
        response_data = result["response"]
        status = response_data.get("status")

        if status == "NOT_FOUND":
            continue

        if status != "OK":
            logger.warning("VWorld non-OK status (airspace=%s, status=%s)", airspace_type, str(status)[:40])
            raise AirspaceUpstreamError("VWorld returned a non-OK status")

        features = (
            response_data.get("result", {})
            .get("featureCollection", {})
            .get("features", [])
        )

        if not isinstance(features, list):
            raise AirspaceUpstreamError("Invalid VWorld features")
        for feature in features:
            if not isinstance(feature, dict):
                raise AirspaceUpstreamError("Invalid VWorld feature")
            properties = feature.get("properties")
            if not isinstance(properties, dict):
                feature["properties"] = {}
            feature["properties"]["airspace_type"] = airspace_type

        all_features.extend(features)

    return {
        "type": "FeatureCollection",
        "features": all_features,
    }
