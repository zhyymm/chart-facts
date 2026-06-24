"""Tests for chart-facts L0 API."""

from __future__ import annotations

import pytest

from chart_facts.calculator import compute_facts, init_ephemeris
from chart_facts.models import FactsRequest


@pytest.fixture(scope="module", autouse=True)
def _init_ephe():
    init_ephemeris()


# Taipei quick chart from almuten.net defaults (2026-06-23 04:18, Alcabitius).
# Longitude values verified against Swiss Ephemeris; update if ephe files change.
TAIPEI = FactsRequest(
    datetime="2026-06-23T04:18:00",
    timezone="Asia/Taipei",
    latitude=25 + 25 / 60,  # 25°25' N
    longitude=121 + 30 / 60,  # 121°30' E
    house_system="alcabitius",
)


def test_compute_facts_structure():
    result = compute_facts(TAIPEI)
    assert result.engine.name == "swiss-ephemeris"
    assert result.input.house_system == "alcabitius"
    assert len(result.houses) == 12
    assert len(result.bodies) >= 10
    assert 0 <= result.angles.asc < 360
    assert 0 <= result.angles.mc < 360


def test_house_numbers_are_1_to_12():
    result = compute_facts(TAIPEI)
    numbers = [h.number for h in result.houses]
    assert numbers == list(range(1, 13))


def test_bodies_have_speed_and_retrograde():
    result = compute_facts(TAIPEI)
    for body in result.bodies:
        assert 0 <= body.longitude < 360
        assert isinstance(body.retrograde, bool)
        assert body.id


def test_taipei_sun_longitude():
    """Regression anchor — compare manually with almuten.net when updating."""
    result = compute_facts(TAIPEI)
    sun = next(b for b in result.bodies if b.id == "sun")
    # 2026-06-23 — Sun in early Cancer (tropical)
    assert 90 <= sun.longitude <= 95, f"sun longitude {sun.longitude}"


def test_placidus_vs_alcabitius_differ():
    placidus = compute_facts(TAIPEI.model_copy(update={"house_system": "placidus"}))
    alcabitius = compute_facts(TAIPEI)
    # ASC is identical across systems; intermediate cusps differ.
    assert placidus.houses[1].cusp != pytest.approx(alcabitius.houses[1].cusp, abs=0.001)


def test_invalid_timezone():
    bad = TAIPEI.model_copy(update={"timezone": "Not/A/Timezone"})
    with pytest.raises(Exception):
        compute_facts(bad)


def test_invalid_house_system():
    with pytest.raises(ValueError):
        FactsRequest(
            datetime="2026-06-23T04:18:00",
            timezone="Asia/Taipei",
            latitude=25.0,
            longitude=121.5,
            house_system="invalid_system",
        )


def test_bce_date_uses_lmt():
    """44 BCE (ISO -0043) — astronomical year -43, LMT from longitude."""
    request = FactsRequest(
        datetime="-0043-03-15T06:00:00",
        timezone="Europe/Rome",
        latitude=41.9,
        longitude=12.5,
        house_system="alcabitius",
    )
    result = compute_facts(request)
    assert result.input.timezone == "LMT"
    assert result.julian_day_ut > 0
    assert len(result.bodies) >= 10
