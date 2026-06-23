"""Swiss Ephemeris fact computation — positions and cusps only."""

from __future__ import annotations

import os
from datetime import datetime
from zoneinfo import ZoneInfo

import swisseph as swe

from chart_facts.constants import (
    BODY_IDS,
    CALC_FLAGS,
    DEFAULT_BODIES,
    ENGINE_NAME,
    HOUSE_SYSTEMS,
)
from chart_facts.models import (
    AngleFacts,
    BodyFacts,
    EngineInfo,
    FactsRequest,
    FactsResponse,
    HouseCuspFacts,
    InputEcho,
)

_ephe_initialized = False
_ephe_path: str | None = None


def init_ephemeris(ephe_path: str | None = None) -> str | None:
    """Configure Swiss Ephemeris data path once per process."""
    global _ephe_initialized, _ephe_path
    if _ephe_initialized:
        return _ephe_path

    path = ephe_path or os.environ.get("EPHE_PATH")
    if path and os.path.isdir(path):
        swe.set_ephe_path(path)
        _ephe_path = path
    else:
        # Falls back to built-in Moshier ephemeris when files are absent.
        _ephe_path = None

    _ephe_initialized = True
    return _ephe_path


def _parse_local_datetime(value: str, timezone: str) -> tuple[datetime, datetime]:
    """Parse ISO local datetime and convert to UTC."""
    normalized = value.strip().replace("Z", "+00:00")
    try:
        local = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"Invalid datetime '{value}': {exc}") from exc

    tz = ZoneInfo(timezone)
    if local.tzinfo is None:
        local = local.replace(tzinfo=tz)
    else:
        local = local.astimezone(tz)

    utc = local.astimezone(ZoneInfo("UTC"))
    return local, utc


def _datetime_to_jd_ut(dt_utc: datetime) -> float:
    hour = (
        dt_utc.hour
        + dt_utc.minute / 60
        + dt_utc.second / 3600
        + dt_utc.microsecond / 3_600_000_000
    )
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hour)


def _normalize_longitude(value: float) -> float:
    return value % 360.0


def compute_facts(request: FactsRequest) -> FactsResponse:
    """Compute chart facts for one birth event."""
    init_ephemeris()

    local_dt, utc_dt = _parse_local_datetime(request.datetime, request.timezone)
    jd_ut = _datetime_to_jd_ut(utc_dt)

    hsys = HOUSE_SYSTEMS[request.house_system]
    cusps, ascmc = swe.houses(jd_ut, request.latitude, request.longitude, hsys)

    # pyswisseph >= 2.10 returns 12 cusps (index 0 = house 1); older builds use index 1–12.
    if len(cusps) == 12:
        houses = [
            HouseCuspFacts(number=i + 1, cusp=_normalize_longitude(cusps[i]))
            for i in range(12)
        ]
    else:
        houses = [
            HouseCuspFacts(number=i, cusp=_normalize_longitude(cusps[i]))
            for i in range(1, 13)
        ]

    body_keys = tuple(request.bodies) if request.bodies else DEFAULT_BODIES
    bodies: list[BodyFacts] = []
    for body_id in body_keys:
        swe_id = BODY_IDS[body_id]
        result, _retflag = swe.calc_ut(jd_ut, swe_id, CALC_FLAGS)
        lon, lat, dist, speed = result[0], result[1], result[2], result[3]
        bodies.append(
            BodyFacts(
                id=body_id,
                longitude=_normalize_longitude(lon),
                latitude=lat,
                distance=dist,
                speed=speed,
                retrograde=speed < 0,
            )
        )

    angles = AngleFacts(
        asc=_normalize_longitude(ascmc[0]),
        mc=_normalize_longitude(ascmc[1]),
        armc=_normalize_longitude(ascmc[2]),
        vertex=_normalize_longitude(ascmc[3]),
        equatorial_asc=_normalize_longitude(ascmc[4]),
        co_asc_koch=_normalize_longitude(ascmc[5]),
        co_asc_munkasey=_normalize_longitude(ascmc[6]),
        polar_asc=_normalize_longitude(ascmc[7]),
    )

    return FactsResponse(
        engine=EngineInfo(
            name=ENGINE_NAME,
            version=swe.version,
            ephe_path=_ephe_path,
        ),
        input=InputEcho(
            datetime_local=local_dt.isoformat(),
            datetime_utc=utc_dt.isoformat(),
            timezone=request.timezone,
            latitude=request.latitude,
            longitude=request.longitude,
            house_system=request.house_system,
        ),
        julian_day_ut=jd_ut,
        angles=angles,
        houses=houses,
        bodies=bodies,
    )
