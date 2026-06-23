"""Swiss Ephemeris mappings and supported configuration."""

from __future__ import annotations

import swisseph as swe

# Swiss Ephemeris house system byte codes (swe.houses hsys argument).
HOUSE_SYSTEMS: dict[str, bytes] = {
    "placidus": b"P",
    "koch": b"K",
    "porphyry": b"O",
    "regiomontanus": b"R",
    "campanus": b"C",
    "equal": b"E",
    "whole_sign": b"W",
    "alcabitius": b"A",
    "morinus": b"M",
    "topocentric": b"T",
    "krusinski": b"U",
    "apc": b"Y",
}

DEFAULT_HOUSE_SYSTEM = "alcabitius"

# Bodies returned in ChartFacts (id → Swiss Ephemeris constant).
BODY_IDS: dict[str, int] = {
    "sun": swe.SUN,
    "moon": swe.MOON,
    "mercury": swe.MERCURY,
    "venus": swe.VENUS,
    "mars": swe.MARS,
    "jupiter": swe.JUPITER,
    "saturn": swe.SATURN,
    "uranus": swe.URANUS,
    "neptune": swe.NEPTUNE,
    "pluto": swe.PLUTO,
    "mean_node": swe.MEAN_NODE,
    "true_node": swe.TRUE_NODE,
    "chiron": swe.CHIRON,
}

DEFAULT_BODIES: tuple[str, ...] = (
    "sun",
    "moon",
    "mercury",
    "venus",
    "mars",
    "jupiter",
    "saturn",
    "uranus",
    "neptune",
    "pluto",
    "mean_node",
    "true_node",
)

CALC_FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED

ENGINE_NAME = "swiss-ephemeris"
