from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


class CoverageMode(StrEnum):
    RADIUS = "RADIUS"
    AREAS = "AREAS"


class Location(BaseModel):
    id: str | None = None
    label: str = Field(min_length=1, max_length=200)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class RadiusCoverage(BaseModel):
    mode: Literal[CoverageMode.RADIUS]
    location: Location
    radius_km: float = Field(gt=0, le=500)


class AreasCoverage(BaseModel):
    mode: Literal[CoverageMode.AREAS]
    area_ids: list[str] = Field(min_length=1, max_length=100)


Coverage = Annotated[RadiusCoverage | AreasCoverage, Field(discriminator="mode")]


class ServiceAreaPatch(BaseModel):
    expected_revision: int = Field(ge=0)
    coverage: Coverage


class ServiceAreaResponse(BaseModel):
    vendor_id: str
    revision: int
    coverage: Coverage | None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class LocationResult(Location):
    pass


class EligibilityRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    area_id: str | None = None


class EligibilityResponse(BaseModel):
    eligible: bool
    reason: str
