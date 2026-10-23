"""Existing /weather/point response schema."""
from pydantic import BaseModel, ConfigDict

class WeatherPointResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nx: int
    ny: int
    forecast_at: str
    temperature: float | None
    wind_speed: float | None
    precipitation: str | float | None
    precipitation_type: str | float | None
    precipitation_status: str | None
    precipitation_type_status: str | None
