"""Region selection response schema (matches data/regions.json)."""
from pydantic import BaseModel, ConfigDict


class RegionPoint(BaseModel):
    model_config = ConfigDict(extra="forbid")
    lat: float
    lng: float
    level: int


class RegionItem(RegionPoint):
    name: str
    province: str


class RegionsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nationalView: RegionPoint
    regions: list[RegionItem]
