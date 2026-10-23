"""HTTP-level regression checks without Oracle, SSH, or external API calls."""
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

DRONE = {"id": "D1", "name": "Sample", "wind": 8.0, "minTemp": -10.0, "maxTemp": 40.0}
WEATHER = {
    "forecast_at": "2026-10-23 12:00:00", "temperature": 20.0,
    "wind_speed": 2.0, "pty_raw": "0", "pcp_raw": "0",
    "pty_status": "OK", "pcp_status": "OK",
}
ANALYSIS = {
    "drone": "Sample", "forecast_at": "2026-10-23 12:00:00",
    "wind_speed": 2.0, "temperature": 20.0,
    "wind_result": "GOOD", "temperature_result": "GOOD",
    "precipitation_result": "UNKNOWN", "final_result": "UNKNOWN",
    "max_wind": 8.0, "min_temp": -10.0, "max_temp": 40.0,
}


def test_drones_http_contract():
    with patch("app.routers.drones.list_drones", return_value=[DRONE]):
        response = client.get("/drones")
    assert response.status_code == 200
    assert response.json() == [DRONE]


def test_drones_empty_list():
    with patch("app.routers.drones.list_drones", return_value=[]):
        response = client.get("/drones")
    assert response.status_code == 200
    assert response.json() == []


def test_weather_point_http_contract():
    with (patch("app.routers.weather.latlon_to_grid", return_value=(60, 127)) as grid,
          patch("app.routers.weather.get_weather", return_value=WEATHER) as repo):
        response = client.get("/weather/point", params={"latitude": 37.5665, "longitude": 126.9780})
    assert response.status_code == 200
    assert response.json() == {
        "nx": 60, "ny": 127, "forecast_at": WEATHER["forecast_at"],
        "temperature": 20.0, "wind_speed": 2.0,
        "precipitation": "0", "precipitation_type": "0",
        "precipitation_status": "OK", "precipitation_type_status": "OK",
    }
    grid.assert_called_once_with(37.5665, 126.978)
    repo.assert_called_once_with(60, 127)


def test_weather_point_not_found():
    with (patch("app.routers.weather.latlon_to_grid", return_value=(60, 127)),
          patch("app.routers.weather.get_weather", return_value=None)):
        response = client.get("/weather/point", params={"latitude": 37.5, "longitude": 127.0})
    assert response.status_code == 404


def test_weather_point_missing_coordinate():
    response = client.get("/weather/point", params={"latitude": 37.5})
    assert response.status_code == 422


@pytest.mark.parametrize("params,grid_expected", [
    ({"model_id": "D1", "nx": 60, "ny": 127}, False),
    ({"model_id": "D1", "latitude": 37.5, "longitude": 127.0}, True),
])
def test_flight_analysis_http_contract(params, grid_expected):
    with (patch("app.routers.flight_analysis.latlon_to_grid", return_value=(60, 127)) as grid,
          patch("app.routers.flight_analysis.analyze_flight", return_value=ANALYSIS) as analyze):
        response = client.get("/flight-analysis", params=params)
    assert response.status_code == 200
    assert response.json() == ANALYSIS
    analyze.assert_called_once_with("D1", 60, 127)
    assert grid.called == grid_expected


def test_flight_analysis_missing_location():
    response = client.get("/flight-analysis", params={"model_id": "D1"})
    assert response.status_code == 400


def test_flight_analysis_drone_not_found():
    with patch("app.routers.flight_analysis.analyze_flight", return_value={"error": "드론 정보를 찾을 수 없습니다."}):
        response = client.get("/flight-analysis", params={"model_id": "missing", "nx": 60, "ny": 127})
    assert response.status_code == 404


def test_api_routes_documented_in_openapi():
    paths = client.get("/openapi.json").json()["paths"]
    for route in ("/drones", "/weather/point", "/flight-analysis"):
        assert route in paths
        assert "200" in paths[route]["get"]["responses"]
