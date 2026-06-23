"""Request/response schemas for the /facts endpoint."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from chart_facts.constants import DEFAULT_BODIES, DEFAULT_HOUSE_SYSTEM, HOUSE_SYSTEMS


class FactsRequest(BaseModel):
    """Birth data for a single chart facts computation."""

    datetime: str = Field(
        ...,
        description="Local birth datetime ISO-8601, e.g. 1990-05-15T14:30:00",
        examples=["1990-05-15T14:30:00"],
    )
    timezone: str = Field(
        ...,
        description="IANA timezone for the birth place, e.g. Asia/Taipei",
        examples=["Asia/Taipei"],
    )
    latitude: float = Field(..., ge=-90, le=90, examples=[25.033])
    longitude: float = Field(..., ge=-180, le=180, examples=[121.5654])
    house_system: str = Field(
        default=DEFAULT_HOUSE_SYSTEM,
        description="House system key; see GET /meta/house-systems",
    )
    bodies: list[str] | None = Field(
        default=None,
        description="Subset of body ids; defaults to standard set",
    )

    @field_validator("house_system")
    @classmethod
    def validate_house_system(cls, value: str) -> str:
        key = value.lower().replace("-", "_").replace(" ", "_")
        if key not in HOUSE_SYSTEMS:
            supported = ", ".join(sorted(HOUSE_SYSTEMS))
            raise ValueError(f"Unsupported house_system '{value}'. Supported: {supported}")
        return key

    @field_validator("bodies")
    @classmethod
    def validate_bodies(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        from chart_facts.constants import BODY_IDS

        unknown = [b for b in value if b not in BODY_IDS]
        if unknown:
            supported = ", ".join(sorted(BODY_IDS))
            raise ValueError(f"Unknown bodies {unknown}. Supported: {supported}")
        return value


class EngineInfo(BaseModel):
    name: str
    version: str
    ephe_path: str | None
    zodiac: Literal["tropical"] = "tropical"
    node_types: list[str] = Field(default_factory=lambda: ["mean", "true"])


class InputEcho(BaseModel):
    datetime_local: str
    datetime_utc: str
    timezone: str
    latitude: float
    longitude: float
    house_system: str


class AngleFacts(BaseModel):
    asc: float
    mc: float
    armc: float
    vertex: float
    equatorial_asc: float
    co_asc_koch: float
    co_asc_munkasey: float
    polar_asc: float


class HouseCuspFacts(BaseModel):
    number: int = Field(..., ge=1, le=12)
    cusp: float


class BodyFacts(BaseModel):
    id: str
    longitude: float
    latitude: float
    distance: float
    speed: float
    retrograde: bool


class FactsResponse(BaseModel):
    engine: EngineInfo
    input: InputEcho
    julian_day_ut: float
    angles: AngleFacts
    houses: list[HouseCuspFacts]
    bodies: list[BodyFacts]


class MetaResponse(BaseModel):
    service: str
    version: str
    house_systems: list[str]
    bodies: list[str]
    default_house_system: str
    default_bodies: list[str]
