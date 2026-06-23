"""HTTP integration tests (run against a live server with pytest -m integration)."""

from __future__ import annotations

import os

import httpx
import pytest

BASE_URL = os.environ.get("CHART_FACTS_URL", "http://127.0.0.1:8000")

pytestmark = pytest.mark.integration


@pytest.fixture
def client():
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as c:
        yield c


def test_health(client: httpx.Client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_meta(client: httpx.Client):
    r = client.get("/meta")
    assert r.status_code == 200
    data = r.json()
    assert "alcabitius" in data["house_systems"]
    assert "sun" in data["bodies"]


def test_facts_taipei(client: httpx.Client):
    r = client.post(
        "/facts",
        json={
            "datetime": "2026-06-23T04:18:00",
            "timezone": "Asia/Taipei",
            "latitude": 25.416667,
            "longitude": 121.5,
            "house_system": "alcabitius",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert len(data["houses"]) == 12
    assert len(data["bodies"]) >= 10
