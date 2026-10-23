"""Existing /flight-analysis response schema."""
from pydantic import BaseModel, ConfigDict

class FlightAnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    drone: str
    forecast_at: str
    wind_speed: float | None
    temperature: float | None
    wind_result: str
    temperature_result: str
    precipitation_result: str
    final_result: str
    max_wind: float | None
    min_temp: float | None
    max_temp: float | None
