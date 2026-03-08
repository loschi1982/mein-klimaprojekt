"""
Simulation-Modul für Klimaprojektionen
Team-Branch: team/simulation
"""
from .models import (
    ScenarioType,
    SimulationParameters,
    SimulationResult,
    YearlyDataPoint,
    SCENARIO_DEFAULTS,
)
from .engine import (
    SimulationEngine,
    radiative_forcing,
    temperature_anomaly,
    project_co2_linear,
    project_co2_exponential,
    compare_scenarios,
)

__all__ = [
    "ScenarioType",
    "SimulationParameters",
    "SimulationResult",
    "YearlyDataPoint",
    "SCENARIO_DEFAULTS",
    "SimulationEngine",
    "radiative_forcing",
    "temperature_anomaly",
    "project_co2_linear",
    "project_co2_exponential",
    "compare_scenarios",
]
