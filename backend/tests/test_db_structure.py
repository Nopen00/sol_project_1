"""Offline regression tests: no Oracle connection required."""
from unittest.mock import patch
from app.routers.drones import get_drones
from app.services import drone_repository, weather_repository


def test_drones_router_delegates():
    expected = [{"id": "D1", "name": "Test", "wind": 8.0, "minTemp": -10.0, "maxTemp": 40.0}]
    with patch("app.routers.drones.list_drones", return_value=expected):
        assert get_drones() == expected


def test_weather_contract():
    class FakeResult:
        def first(self):
            return ("2026-10-23", 20, 3, "0", "0", "OK", "OK")

    class FakeSession:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def execute(self, statement, params):
            assert params == {"nx": 60, "ny": 127}
            return FakeResult()

    with patch.object(weather_repository, "get_session", return_value=FakeSession()):
        result = weather_repository.get_weather(60, 127)
    assert result["temperature"] == 20
    assert result["forecast_at"] == "2026-10-23"
