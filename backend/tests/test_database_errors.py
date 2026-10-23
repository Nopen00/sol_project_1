"""Database failures are sanitized at the HTTP boundary (no live Oracle required)."""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from backend.main import app

client = TestClient(app)


@pytest.mark.parametrize("path,params,target", [
    ("/drones", None, "app.routers.drones.list_drones"),
    ("/weather/point", {"latitude": 37.5665, "longitude": 126.9780}, "app.routers.weather.get_weather"),
    ("/flight-analysis", {"model_id": "D1", "nx": 60, "ny": 127}, "app.routers.flight_analysis.analyze_flight"),
])
def test_db_failure_returns_safe_503(path, params, target):
    failure = OperationalError("SELECT secret_column", {"password": "hidden"}, Exception("connection failed"))
    with patch(target, side_effect=failure):
        response = client.get(path, params=params)
    assert response.status_code == 503
    assert response.json() == {"detail": "데이터베이스를 일시적으로 사용할 수 없습니다."}
    assert "secret_column" not in response.text
    assert "hidden" not in response.text


def test_non_db_validation_still_uses_existing_status():
    response = client.get("/flight-analysis", params={"model_id": "D1"})
    assert response.status_code == 400
