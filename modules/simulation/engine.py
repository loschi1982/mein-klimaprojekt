"""
Simulations-Engine für Klimaprojektionen
Team-Branch: team/simulation

Implementiert:
- CO₂-Projektion (lineares + exponentielles Wachstum)
- Strahlungsantrieb nach IPCC-Formel
- Temperaturanomalie-Berechnung (ECS-basiert)
- Szenario-Vergleich
"""
import math
from .models import (
    SimulationParameters,
    SimulationResult,
    ScenarioType,
    YearlyDataPoint,
    SCENARIO_DEFAULTS,
)


# ── Physikalische Formeln ─────────────────────────────────────────────────────

def radiative_forcing(co2_ppm: float, co2_reference: float = 280.0) -> float:
    """
    IPCC-Formel für CO₂-Strahlungsantrieb:
    ΔF = 5.35 × ln(C / C₀)   [W/m²]
    """
    if co2_ppm <= 0 or co2_reference <= 0:
        return 0.0
    return 5.35 * math.log(co2_ppm / co2_reference)


def temperature_anomaly(
    forcing_wm2: float,
    climate_sensitivity: float = 3.0,
) -> float:
    """
    Gleichgewichtstemperatur-Anomalie aus Strahlungsantrieb:
    ΔT = ECS × ΔF / F_2xCO2
    F_2xCO2 = 3.7 W/m² (Strahlungsantrieb bei CO₂-Verdopplung)
    """
    f_2x = 3.7
    return climate_sensitivity * forcing_wm2 / f_2x


# ── CO₂-Projektion ────────────────────────────────────────────────────────────

def project_co2_linear(
    start_ppm: float,
    growth_rate: float,
    years: int,
) -> list[float]:
    """Lineare CO₂-Projektion: C(t) = C₀ + r·t"""
    return [round(start_ppm + growth_rate * t, 3) for t in range(years + 1)]


def project_co2_exponential(
    start_ppm: float,
    annual_growth_fraction: float,
    years: int,
) -> list[float]:
    """
    Exponentielle CO₂-Projektion: C(t) = C₀ × (1 + r)^t
    annual_growth_fraction: z.B. 0.005 für 0.5%/Jahr
    """
    return [
        round(start_ppm * (1 + annual_growth_fraction) ** t, 3)
        for t in range(years + 1)
    ]


# ── Simulations-Engine ────────────────────────────────────────────────────────

class SimulationEngine:
    """Führt Klimaprojektionen für gegebene Parameter durch."""

    def run(self, params: SimulationParameters) -> SimulationResult:
        defaults = SCENARIO_DEFAULTS[params.scenario]
        growth_rate = params.co2_growth_rate or defaults["co2_growth_rate"]

        co2_series = project_co2_linear(
            start_ppm=params.co2_start_ppm,
            growth_rate=growth_rate,
            years=params.years,
        )

        projection = []
        for t, co2 in enumerate(co2_series):
            forcing = radiative_forcing(co2, params.pre_industrial_co2)
            temp = temperature_anomaly(forcing, params.temperature_sensitivity)
            projection.append(YearlyDataPoint(
                year=params.start_year + t,
                co2_ppm=co2,
                temperature_anomaly_c=round(temp, 3),
                radiative_forcing_wm2=round(forcing, 3),
            ))

        summary = self._build_summary(params, projection, defaults)

        return SimulationResult(
            scenario=params.scenario.value,
            scenario_name=defaults["name"],
            parameters=params,
            projection=projection,
            summary=summary,
        )

    def _build_summary(
        self,
        params: SimulationParameters,
        projection: list[YearlyDataPoint],
        defaults: dict,
    ) -> dict:
        last = projection[-1]
        first = projection[0]
        co2_increase = round(last.co2_ppm - first.co2_ppm, 2)
        temp_increase = round(last.temperature_anomaly_c - first.temperature_anomaly_c, 3)

        # Wann wird 450 ppm überschritten?
        year_450 = next(
            (p.year for p in projection if p.co2_ppm >= 450),
            None,
        )

        return {
            "scenario": params.scenario.value,
            "scenario_name": defaults["name"],
            "description": defaults["description"],
            "start_year": params.start_year,
            "end_year": last.year,
            "co2_start_ppm": first.co2_ppm,
            "co2_end_ppm": last.co2_ppm,
            "co2_increase_ppm": co2_increase,
            "temp_anomaly_start_c": first.temperature_anomaly_c,
            "temp_anomaly_end_c": last.temperature_anomaly_c,
            "temp_increase_c": temp_increase,
            "year_exceeds_450ppm": year_450,
            "forcing_end_wm2": last.radiative_forcing_wm2,
        }


# ── Szenario-Vergleich ────────────────────────────────────────────────────────

def compare_scenarios(
    scenarios: list[ScenarioType],
    years: int = 50,
    start_year: int = 2026,
    co2_start: float = 428.0,
) -> dict[str, SimulationResult]:
    """Führt mehrere Szenarien parallel aus und gibt Vergleichsdaten zurück."""
    engine = SimulationEngine()
    results = {}
    for scenario in scenarios:
        params = SimulationParameters(
            scenario=scenario,
            start_year=start_year,
            years=years,
            co2_start_ppm=co2_start,
        )
        results[scenario.value] = engine.run(params)
    return results
