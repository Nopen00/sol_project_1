
from pydantic import BaseModel


class WeatherResponse(BaseModel):
    latitude: float
    longitude: float
    nx: int
    ny: int

    base_date: str
    base_time: str

    temperature: str | None = None
    wind_speed: str | None = None
    wind_direction: str | None = None
    rainfall: str | None = None
