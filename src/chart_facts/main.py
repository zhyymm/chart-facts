"""FastAPI application for Chart Facts L0 service."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from chart_facts import __version__
from chart_facts.calculator import compute_facts, init_ephemeris
from chart_facts.constants import BODY_IDS, DEFAULT_BODIES, DEFAULT_HOUSE_SYSTEM, HOUSE_SYSTEMS
from chart_facts.models import FactsRequest, FactsResponse, MetaResponse

app = FastAPI(
    title="Chart Facts",
    description="L0 astrological facts API — Swiss Ephemeris positions and house cusps only.",
    version=__version__,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    init_ephemeris()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "chart-facts", "version": __version__}


@app.get("/meta", response_model=MetaResponse)
def meta() -> MetaResponse:
    return MetaResponse(
        service="chart-facts",
        version=__version__,
        house_systems=sorted(HOUSE_SYSTEMS.keys()),
        bodies=sorted(BODY_IDS.keys()),
        default_house_system=DEFAULT_HOUSE_SYSTEM,
        default_bodies=list(DEFAULT_BODIES),
    )


@app.post("/facts", response_model=FactsResponse)
def facts(request: FactsRequest) -> FactsResponse:
    try:
        return compute_facts(request)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Calculation failed: {exc}") from exc
