#!/usr/bin/env python3
"""Print /facts JSON for manual comparison with almuten.net."""

from __future__ import annotations

import json
import sys

from chart_facts.calculator import compute_facts, init_ephemeris
from chart_facts.models import FactsRequest


def main() -> None:
    init_ephemeris()
    req = FactsRequest(
        datetime=sys.argv[1] if len(sys.argv) > 1 else "2026-06-23T04:18:00",
        timezone=sys.argv[2] if len(sys.argv) > 2 else "Asia/Taipei",
        latitude=float(sys.argv[3]) if len(sys.argv) > 3 else 25 + 25 / 60,
        longitude=float(sys.argv[4]) if len(sys.argv) > 4 else 121 + 30 / 60,
        house_system=sys.argv[5] if len(sys.argv) > 5 else "alcabitius",
    )
    result = compute_facts(req)
    print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
