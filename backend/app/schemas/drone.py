"""Existing /drones response schema."""
from pydantic import BaseModel, ConfigDict

class DroneResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    name: str
    wind: float
    minTemp: float
    maxTemp: float
