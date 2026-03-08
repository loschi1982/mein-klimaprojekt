"""
Simulationsmodelle für Klimaszenarien
Team-Branch: team/simulation
"""
from dataclasses import dataclass, field
from enum import Enum


class ScenarioType(str, Enum):
    RCP26 = "rcp26"
    RCP45 = "rcp45"
    RCP60 = "rcp60"
    RCP85 = "rcp85"
    CUSTOM = "custom"


@dataclass
class SimulationParameters:
    scenario: ScenarioType
    start_year: int = 2026
    years: int = 50
    co2_start_ppm: float = 428.0       # Startwert CO₂
    co2_growth_rate: float | None = None  # ppm/Jahr; None → Szenario-Default
    temperature_sensitivity: float = 3.0  # Klimasensitivität °C / CO₂-Verdopplung
    pre_industrial_co2: float = 280.0    # vorindustrieller Referenzwert


@dataclass
class YearlyDataPoint:
    year: int
    co2_ppm: float
    temperature_anomaly_c: float        # gegenüber vorindustriellem Niveau
    radiative_forcing_wm2: float        # Strahlungsantrieb


@dataclass
class SimulationResult:
    scenario: str
    scenario_name: str
    parameters: SimulationParameters
    projection: list[YearlyDataPoint] = field(default_factory=list)
    summary: dict = field(default_factory=dict)


# Szenario-Defaults (ppm/Jahr Wachstum)
SCENARIO_DEFAULTS: dict[ScenarioType, dict] = {
    ScenarioType.RCP26: {
        "name": "RCP 2.6 – Starke Reduktion",
        "co2_growth_rate": 0.5,
        "description": "Emissionen sinken stark. CO₂ stabilisiert sich ~450 ppm. Erwärmung: ~1.5–2°C.",
    },
    ScenarioType.RCP45: {
        "name": "RCP 4.5 – Moderate Reduktion",
        "co2_growth_rate": 1.5,
        "description": "Moderate Maßnahmen. CO₂ ~550 ppm bis 2100. Erwärmung: ~2–3°C.",
    },
    ScenarioType.RCP60: {
        "name": "RCP 6.0 – Geringe Maßnahmen",
        "co2_growth_rate": 2.5,
        "description": "Wenige Maßnahmen. CO₂ ~700 ppm bis 2100. Erwärmung: ~3–4°C.",
    },
    ScenarioType.RCP85: {
        "name": "RCP 8.5 – Business as Usual",
        "co2_growth_rate": 3.5,
        "description": "Keine Maßnahmen. CO₂ >900 ppm bis 2100. Erwärmung: >4°C.",
    },
    ScenarioType.CUSTOM: {
        "name": "Benutzerdefiniertes Szenario",
        "co2_growth_rate": 2.0,
        "description": "Frei konfigurierbares Szenario.",
    },
}
