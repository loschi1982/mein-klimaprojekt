"""
Router: Simulation
Team-Branch: team/api  (Grundgerüst – Logik folgt von team/simulation)
"""
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from models.schemas import ApiResponse, Meta, ScenarioInfo, SimulateRequest

router = APIRouter(prefix="/api/v1", tags=["Simulation"])

SCENARIOS = {
    "rcp26": ScenarioInfo(
        id="rcp26",
        name="RCP 2.6 – Starke Reduktion",
        description="Emissionen werden stark reduziert. CO₂-Konzentration stabilisiert sich bei ~450 ppm.",
        co2_growth_rate=0.5,
    ),
    "rcp45": ScenarioInfo(
        id="rcp45",
        name="RCP 4.5 – Moderate Reduktion",
        description="Moderate Maßnahmen. CO₂-Konzentration stabilisiert sich bei ~550 ppm.",
        co2_growth_rate=1.5,
    ),
    "rcp85": ScenarioInfo(
        id="rcp85",
        name="RCP 8.5 – Business as Usual",
        description="Keine Maßnahmen. CO₂-Konzentration steigt auf über 900 ppm.",
        co2_growth_rate=3.5,
    ),
}


def meta() -> Meta:
    return Meta(timestamp=datetime.now(timezone.utc).isoformat())


@router.get("/scenarios", response_model=ApiResponse, summary="Szenarien auflisten")
def list_scenarios():
    """Gibt alle verfügbaren Klimaszenarien zurück."""
    return ApiResponse(data=list(SCENARIOS.values()), meta=meta())


@router.post("/simulate", response_model=ApiResponse, summary="Simulation starten")
def simulate(request: SimulateRequest):
    """
    Führt eine einfache CO₂-Projektion durch.
    Komplexe Simulationslogik wird von team/simulation implementiert.
    """
    if request.scenario not in SCENARIOS:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_PARAMS", "message": f"Unbekanntes Szenario: {request.scenario}"},
        )

    scenario = SCENARIOS[request.scenario]
    base_co2 = 425.0  # ppm (aktuell ca. 2026)
    growth = request.parameters.get("co2_growth_rate", scenario.co2_growth_rate)

    projection = [
        {"year": 2026 + i, "co2_ppm": round(base_co2 + growth * i, 2)}
        for i in range(request.years + 1)
    ]

    return ApiResponse(
        data={
            "scenario": scenario.id,
            "scenario_name": scenario.name,
            "years": request.years,
            "projection": projection,
        },
        meta=meta(),
    )
