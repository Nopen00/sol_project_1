"""Flight suitability service regression tests (mocked repositories)."""
from unittest.mock import patch

from app.services.flight_analysis import analyze_flight

DRONE = {"name": "Sample", "max_wind": 8.0, "min_temp": -10.0, "max_temp": 40.0}
WEATHER = {"forecast_at": "2026-10-23 12:00:00", "wind_speed": 2.0,
           "temperature": 20.0, "pty_raw": "0", "pty_status": "OK"}


def test_missing_drone_skips_weather_query():
    with (patch("app.services.flight_analysis.get_drone", return_value=None),
          patch("app.services.flight_analysis.get_weather") as get_weather):
        assert analyze_flight("missing", 60, 127) == {"error": "드론 정보를 찾을 수 없습니다."}
        get_weather.assert_not_called()


def test_missing_weather():
    with (patch("app.services.flight_analysis.get_drone", return_value=DRONE),
          patch("app.services.flight_analysis.get_weather", return_value=None)):
        assert analyze_flight("D1", 60, 127) == {"error": "날씨 예보가 없습니다."}


def test_flight_result_with_unknown_precipitation():
    with (patch("app.services.flight_analysis.get_drone", return_value=DRONE),
          patch("app.services.flight_analysis.get_weather", return_value=WEATHER)):
        result = analyze_flight("D1", 60, 127)
    assert result["wind_result"] == "GOOD"
    assert result["temperature_result"] == "GOOD"
    assert result["precipitation_result"] == "GOOD"
    assert result["final_result"] == "GOOD"


def test_high_wind_not_recommended():
    weather = {**WEATHER, "wind_speed": 6.0}
    with (patch("app.services.flight_analysis.get_drone", return_value=DRONE),
          patch("app.services.flight_analysis.get_weather", return_value=weather)):
        result = analyze_flight("D1", 60, 127)
    assert result["final_result"] == "NOT_RECOMMENDED"
