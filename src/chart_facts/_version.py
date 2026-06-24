"""Read release version from repository VERSION file."""

from __future__ import annotations

from pathlib import Path


def read_version() -> str:
    roots = (
        Path(__file__).resolve().parents[2],
        Path("/app"),
    )
    for root in roots:
        path = root / "VERSION"
        if path.is_file():
            line = path.read_text(encoding="utf-8").strip().splitlines()[0].strip()
            if line:
                return line
    return "0.0.0"
