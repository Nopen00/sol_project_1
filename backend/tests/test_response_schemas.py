"""Schema validation without a database connection."""
import pytest
from pydantic import ValidationError
from app.schemas.drone import DroneResponse
from app.schemas.weather import WeatherPointResponse
from app.schemas.flight_analysis import FlightAnalysisResponse

def test_drone_contract():
    payload = {"id":"X", "name":"Test", "wind":10, "minTemp":-5, "maxTemp":40}
    assert DroneResponse.model_validate(payload).model_dump() == payload

def test_weather_contract():
    payload = dict(nx=60,ny=127,forecast_at="2026-10-23 12:00",temperature=20,wind_speed=2,precipitation="0",precipitation_type="0",precipitation_status="OK",precipitation_type_status="OK")
    assert WeatherPointResponse.model_validate(payload).model_dump()["nx"] == 60

def test_flight_contract():
    payload = dict(drone="Test",forecast_at="2026-10-23 12:00",wind_speed=2,temperature=20,wind_result="GOOD",temperature_result="GOOD",precipitation_result="UNKNOWN",final_result="UNKNOWN",max_wind=10,min_temp=-5,max_temp=40)
    assert FlightAnalysisResponse.model_validate(payload).final_result == "UNKNOWN"

def test_missing_required_field_rejected():
    with pytest.raises(ValidationError):
        DroneResponse.model_validate({"id":"X"})
