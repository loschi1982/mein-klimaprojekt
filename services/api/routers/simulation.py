"""
Router: Simulation
Team-Branch: team/simulation
"""
import sys
import os
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from models.schemas import ApiResponse, Meta, ScenarioInfo, SimulateRequest

# Projektroot in sys.path
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from modules.simulation import (
    SimulationEngine,
    SimulationParameters,
    ScenarioType,
    SCENARIO_DEFAULTS,
    compare_scenarios,
)

router = APIRouter(prefix="/api/v1", tags=["Simulation"])

_engine = SimulationEngine()


def meta() -> Meta:
    return Meta(timestamp=datetime.now(timezone.utc).isoformat())


def _scenario_info(scenario_id: str) -> ScenarioInfo:
    try:
        stype = ScenarioType(scenario_id)
    except ValueError:
        return None
    defaults = SCENARIO_DEFAULTS[stype]
    return ScenarioInfo(
        id=scenario_id,
        name=defaults["name"],
        description=defaults["description"],
        co2_growth_rate=defaults["co2_growth_rate"],
    )


@router.get("/scenarios", response_model=ApiResponse, summary="Szenarien auflisten")
def list_scenarios():
    """Gibt alle verfügbaren Klimaszenarien zurück."""
    scenarios = [
        _scenario_info(s.value)
        for s in ScenarioType
        if s != ScenarioType.CUSTOM
    ]
    return ApiResponse(data=scenarios, meta=meta())


@router.post("/simulate", response_model=ApiResponse, summary="Simulation starten")
def simulate(request: SimulateRequest):
    """
    Führt eine Klimasimulation mit dem SimulationEngine durch.
    Unterstützt alle RCP-Szenarien und CUSTOM.
    """
    try:
        scenario_type = ScenarioType(request.scenario)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_PARAMS", "message": f"Unbekanntes Szenario: {request.scenario}"},
        )

    co2_growth_rate = request.parameters.get("co2_growth_rate") if request.parameters else None
    co2_start = request.parameters.get("co2_start_ppm", 428.0) if request.parameters else 428.0
    start_year = request.parameters.get("start_year", 2026) if request.parameters else 2026

    params = SimulationParameters(
        scenario=scenario_type,
        start_year=int(start_year),
        years=request.years,
        co2_start_ppm=float(co2_start),
        co2_growth_rate=float(co2_growth_rate) if co2_growth_rate is not None else None,
    )

    result = _engine.run(params)

    projection_data = [
        {
            "year": dp.year,
            "co2_ppm": dp.co2_ppm,
            "temperature_anomaly_c": dp.temperature_anomaly_c,
            "radiative_forcing_wm2": dp.radiative_forcing_wm2,
        }
        for dp in result.projection
    ]

    return ApiResponse(
        data={
            "scenario": result.scenario,
            "scenario_name": result.scenario_name,
            "years": request.years,
            "projection": projection_data,
            "summary": result.summary,
        },
        meta=meta(),
    )


@router.post("/simulate/compare", response_model=ApiResponse, summary="Szenarien vergleichen")
def simulate_compare(years: int = 50, co2_start: float = 428.0):
    """Vergleicht alle Standard-RCP-Szenarien."""
    scenarios = [ScenarioType.RCP26, ScenarioType.RCP45, ScenarioType.RCP60, ScenarioType.RCP85]
    results = compare_scenarios(scenarios, years=years, co2_start=co2_start)

    comparison = {
        scenario_id: {
            "scenario_name": res.scenario_name,
            "summary": res.summary,
            "final_co2_ppm": res.projection[-1].co2_ppm,
            "final_temp_anomaly_c": res.projection[-1].temperature_anomaly_c,
        }
        for scenario_id, res in results.items()
    }

    return ApiResponse(data=comparison, meta=meta())
