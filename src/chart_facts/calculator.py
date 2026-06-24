"""Swiss Ephemeris fact computation — positions and cusps only."""

from __future__ import annotations

import os
import re
from datetime import datetime, timezone
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

_ISO_LOCAL = re.compile(
    r"^(?P<year>-?\d{1,6})-(?P<month>\d{2})-(?P<day>\d{2})T"
    r"(?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})"
)


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
        _ephe_path = None

    _ephe_initialized = True
    return _ephe_path


def _strip_offset(value: str) -> str:
    normalized = value.strip().replace("Z", "+00:00")
    t_index = normalized.find("T")
    if t_index < 0:
        return normalized
    tail = normalized[t_index:]
    for sep in ("+", "-"):
        idx = tail.find(sep, 1)
        if idx > 0:
            return normalized[: t_index + idx]
    return normalized


def _parse_iso_components(value: str) -> tuple[int, int, int, int, int, int]:
    base = _strip_offset(value)
    match = _ISO_LOCAL.match(base)
    if not match:
        raise ValueError(f"Invalid datetime '{value}'")
    return (
        int(match.group("year")),
        int(match.group("month")),
        int(match.group("day")),
        int(match.group("hour")),
        int(match.group("minute")),
        int(match.group("second")),
    )


def _format_iso(year: int, month: int, day: int, hour: int, minute: int, second: int) -> str:
    y = f"{year:04d}" if year >= 0 else f"-{abs(year):04d}"
    return f"{y}-{month:02d}-{day:02d}T{hour:02d}:{minute:02d}:{second:02d}"


def _lmt_to_jd_ut(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    second: int,
    longitude: float,
) -> float:
    """Local Mean Time → Julian Day UT (east-positive longitude)."""
    local_hour = hour + minute / 60 + second / 3600
    ut_hour = local_hour - longitude / 15.0
    return swe.julday(year, month, day, ut_hour)


def _jd_ut_to_utc_datetime(jd_ut: float) -> datetime:
    y, m, d, ut_hours = swe.revjul(jd_ut)
    hour = int(ut_hours)
    minute = int((ut_hours - hour) * 60)
    second = int(round(((ut_hours - hour) * 60 - minute) * 60))
    if 1 <= y <= 9999:
        return datetime(y, m, d, hour, minute, second, tzinfo=timezone.utc)
    return datetime(1970, 1, 1, tzinfo=timezone.utc)  # placeholder; echo uses strings


def _parse_local_datetime(
    value: str,
    timezone_name: str,
    longitude: float,
) -> tuple[str, datetime, float, bool]:
    """Returns (local_iso, utc_dt, jd_ut, used_lmt)."""
    year, month, day, hour, minute, second = _parse_iso_components(value)
    local_iso = _format_iso(year, month, day, hour, minute, second)

    if year < 1 or year > 9999:
        jd_ut = _lmt_to_jd_ut(year, month, day, hour, minute, second, longitude)
        utc_dt = _jd_ut_to_utc_datetime(jd_ut)
        return local_iso, utc_dt, jd_ut, True

    try:
        local = datetime.fromisoformat(local_iso)
    except ValueError as exc:
        raise ValueError(f"Invalid datetime '{value}': {exc}") from exc

    tz = ZoneInfo(timezone_name)
    if local.tzinfo is None:
        local = local.replace(tzinfo=tz)
    else:
        local = local.astimezone(tz)

    utc_dt = local.astimezone(ZoneInfo("UTC"))
    jd_ut = _datetime_to_jd_ut(utc_dt)
    return local.isoformat(), utc_dt, jd_ut, False


def _datetime_to_jd_ut(dt_utc: datetime) -> float:
    hour = (
        dt_utc.hour
        + dt_utc.minute / 60
        + dt_utc.second / 3600
        + dt_utc.microsecond / 3_600_000_000
    )
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hour)


def _utc_iso_from_jd(jd_ut: float) -> str:
    y, m, d, ut_hours = swe.revjul(jd_ut)
    hour = int(ut_hours)
    minute = int((ut_hours - hour) * 60)
    second = int(round(((ut_hours - hour) * 60 - minute) * 60))
    return _format_iso(y, m, d, hour, minute, second) + "+00:00"


def _normalize_longitude(value: float) -> float:
    return value % 360.0


def compute_facts(request: FactsRequest) -> FactsResponse:
    """Compute chart facts for one birth event."""
    init_ephemeris()

    local_text, utc_dt, jd_ut, used_lmt = _parse_local_datetime(
        request.datetime,
        request.timezone,
        request.longitude,
    )

    hsys = HOUSE_SYSTEMS[request.house_system]
    cusps, ascmc = swe.houses(jd_ut, request.latitude, request.longitude, hsys)

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

    tz_label = "LMT" if used_lmt else request.timezone
    utc_text = _utc_iso_from_jd(jd_ut) if used_lmt else utc_dt.isoformat()

    return FactsResponse(
        engine=EngineInfo(
            name=ENGINE_NAME,
            version=swe.version,
            ephe_path=_ephe_path,
        ),
        input=InputEcho(
            datetime_local=local_text,
            datetime_utc=utc_text,
            timezone=tz_label,
            latitude=request.latitude,
            longitude=request.longitude,
            house_system=request.house_system,
        ),
        julian_day_ut=jd_ut,
        angles=angles,
        houses=houses,
        bodies=bodies,
    )
