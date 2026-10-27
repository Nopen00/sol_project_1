"""VWorld GeoJSON and airspace-analysis response schemas."""
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class AirspaceFeature(BaseModel):
    # Preserve arbitrary VWorld attributes and geometry types.
    model_config = ConfigDict(extra="allow")
    type: Literal["Feature"]
    geometry: dict[str, Any] | None = None
    properties: dict[str, Any] = Field(default_factory=dict)


class AirspaceGeoJSONResponse(BaseModel):
    type: Literal["FeatureCollection"]
    features: list[AirspaceFeature]


class AirspaceAnalysisResponse(BaseModel):
    status: Literal[
        "PROHIBITED_AIRSPACE",
        "RESTRICTED_AIRSPACE",
        "ADDITIONAL_CHECK_REQUIRED",
    ]
    message: str
    airspace_count: int = Field(ge=0)
