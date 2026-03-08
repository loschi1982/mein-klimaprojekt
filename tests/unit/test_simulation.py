"""Unit Tests für das Simulation Module"""
import math
import pytest

from modules.simulation.models import (
    ScenarioType,
    SimulationParameters,
    SimulationResult,
    YearlyDataPoint,
    SCENARIO_DEFAULTS,
)
from modules.simulation.engine import (
    radiative_forcing,
    temperature_anomaly,
    project_co2_linear,
    project_co2_exponential,
    SimulationEngine,
    compare_scenarios,
)


# ── radiative_forcing ──────────────────────────────────────────────────────────

def test_radiative_forcing_at_reference():
    """Bei C = C₀ ist der Antrieb 0."""
    assert radiative_forcing(280.0, 280.0) == pytest.approx(0.0)


def test_radiative_forcing_doubled_co2():
    """CO₂-Verdopplung → ~3.7 W/m²."""
    result = radiative_forcing(560.0, 280.0)
    assert result == pytest.approx(5.35 * math.log(2), rel=1e-6)


def test_radiative_forcing_current_co2():
    """Aktueller CO₂-Wert (428 ppm) liefert positiven Antrieb."""
    result = radiative_forcing(428.0, 280.0)
    assert result > 0


def test_radiative_forcing_zero_co2():
    """Ungültige Werte (≤0) geben 0.0 zurück."""
    assert radiative_forcing(0.0) == 0.0
    assert radiative_forcing(-5.0) == 0.0


def test_radiative_forcing_zero_reference():
    """Ungültige Referenz (≤0) gibt 0.0 zurück."""
    assert radiative_forcing(400.0, 0.0) == 0.0


def test_radiative_forcing_formula():
    """Formel: ΔF = 5.35 × ln(C / C₀)."""
    co2, ref = 400.0, 280.0
    expected = 5.35 * math.log(co2 / ref)
    assert radiative_forcing(co2, ref) == pytest.approx(expected)


# ── temperature_anomaly ────────────────────────────────────────────────────────

def test_temperature_anomaly_zero_forcing():
    assert temperature_anomaly(0.0) == pytest.approx(0.0)


def test_temperature_anomaly_formula():
    """ΔT = ECS × ΔF / 3.7."""
    result = temperature_anomaly(3.7, 3.0)
    assert result == pytest.approx(3.0)


def test_temperature_anomaly_custom_sensitivity():
    result = temperature_anomaly(3.7, climate_sensitivity=4.5)
    assert result == pytest.approx(4.5)


def test_temperature_anomaly_positive():
    assert temperature_anomaly(2.0) > 0


# ── project_co2_linear ─────────────────────────────────────────────────────────

def test_project_co2_linear_length():
    result = project_co2_linear(400.0, 2.0, 10)
    assert len(result) == 11  # years+1 Datenpunkte


def test_project_co2_linear_start():
    result = project_co2_linear(400.0, 2.0, 10)
    assert result[0] == 400.0


def test_project_co2_linear_growth():
    result = project_co2_linear(400.0, 2.0, 5)
    assert result[5] == pytest.approx(410.0)


def test_project_co2_linear_zero_growth():
    result = project_co2_linear(400.0, 0.0, 5)
    assert all(v == 400.0 for v in result)


def test_project_co2_linear_rounded():
    result = project_co2_linear(400.0, 1.0 / 3.0, 3)
    # Werte sollten auf 3 Dezimalstellen gerundet sein
    for v in result:
        assert round(v, 3) == v


# ── project_co2_exponential ───────────────────────────────────────────────────

def test_project_co2_exponential_length():
    result = project_co2_exponential(400.0, 0.01, 10)
    assert len(result) == 11


def test_project_co2_exponential_start():
    result = project_co2_exponential(400.0, 0.01, 10)
    assert result[0] == 400.0


def test_project_co2_exponential_growth():
    result = project_co2_exponential(400.0, 0.01, 1)
    assert result[1] == pytest.approx(404.0)


def test_project_co2_exponential_zero_growth():
    result = project_co2_exponential(400.0, 0.0, 5)
    assert all(v == 400.0 for v in result)


# ── SimulationEngine ──────────────────────────────────────────────────────────

def test_engine_returns_simulation_result():
    engine = SimulationEngine()
    params = SimulationParameters(scenario=ScenarioType.RCP45)
    result = engine.run(params)
    assert isinstance(result, SimulationResult)


def test_engine_projection_length():
    engine = SimulationEngine()
    params = SimulationParameters(scenario=ScenarioType.RCP45, years=30)
    result = engine.run(params)
    assert len(result.projection) == 31


def test_engine_projection_years_correct():
    engine = SimulationEngine()
    params = SimulationParameters(scenario=ScenarioType.RCP26, start_year=2026, years=10)
    result = engine.run(params)
    assert result.projection[0].year == 2026
    assert result.projection[-1].year == 2036


def test_engine_co2_increases_rcp85():
    engine = SimulationEngine()
    params = SimulationParameters(scenario=ScenarioType.RCP85, years=50)
    result = engine.run(params)
    assert result.projection[-1].co2_ppm > result.projection[0].co2_ppm


def test_engine_summary_keys():
    engine = SimulationEngine()
    params = SimulationParameters(scenario=ScenarioType.RCP45)
    result = engine.run(params)
    expected_keys = {
        "scenario", "scenario_name", "start_year", "end_year",
        "co2_start_ppm", "co2_end_ppm", "co2_increase_ppm",
        "temp_anomaly_end_c", "temp_increase_c", "forcing_end_wm2",
    }
    assert expected_keys.issubset(result.summary.keys())


def test_engine_summary_co2_increase_positive():
    engine = SimulationEngine()
    params = SimulationParameters(scenario=ScenarioType.RCP85, years=50)
    result = engine.run(params)
    assert result.summary["co2_increase_ppm"] > 0


def test_engine_custom_growth_rate():
    engine = SimulationEngine()
    params = SimulationParameters(
        scenario=ScenarioType.CUSTOM,
        co2_growth_rate=5.0,
        years=10,
        co2_start_ppm=400.0,
    )
    result = engine.run(params)
    assert result.projection[-1].co2_ppm == pytest.approx(450.0)


def test_engine_scenario_name_rcp26():
    engine = SimulationEngine()
    params = SimulationParameters(scenario=ScenarioType.RCP26)
    result = engine.run(params)
    assert "RCP 2.6" in result.scenario_name


def test_engine_yearly_datapoints_have_all_fields():
    engine = SimulationEngine()
    params = SimulationParameters(scenario=ScenarioType.RCP45, years=5)
    result = engine.run(params)
    for dp in result.projection:
        assert isinstance(dp, YearlyDataPoint)
        assert dp.co2_ppm > 0
        assert isinstance(dp.temperature_anomaly_c, float)
        assert isinstance(dp.radiative_forcing_wm2, float)


def test_engine_temperature_increases_with_co2():
    engine = SimulationEngine()
    params = SimulationParameters(scenario=ScenarioType.RCP85, years=50)
    result = engine.run(params)
    assert result.projection[-1].temperature_anomaly_c > result.projection[0].temperature_anomaly_c


def test_engine_year_exceeds_450ppm_rcp85():
    engine = SimulationEngine()
    params = SimulationParameters(
        scenario=ScenarioType.RCP85,
        years=50,
        co2_start_ppm=428.0,
    )
    result = engine.run(params)
    year_450 = result.summary.get("year_exceeds_450ppm")
    assert year_450 is not None
    assert 2026 <= year_450 <= 2076


def test_engine_year_exceeds_450ppm_rcp26_none_or_far():
    engine = SimulationEngine()
    params = SimulationParameters(
        scenario=ScenarioType.RCP26,
        years=10,
        co2_start_ppm=428.0,
    )
    result = engine.run(params)
    # RCP2.6 mit 0.5 ppm/Jahr: 428 + 5 = 433 nach 10 Jahren → 450 nicht erreicht
    assert result.summary.get("year_exceeds_450ppm") is None


# ── compare_scenarios ─────────────────────────────────────────────────────────

def test_compare_scenarios_returns_dict():
    results = compare_scenarios([ScenarioType.RCP26, ScenarioType.RCP85], years=10)
    assert isinstance(results, dict)


def test_compare_scenarios_all_scenarios_present():
    scenarios = [ScenarioType.RCP26, ScenarioType.RCP45, ScenarioType.RCP85]
    results = compare_scenarios(scenarios, years=10)
    for s in scenarios:
        assert s.value in results


def test_compare_scenarios_rcp85_higher_co2():
    results = compare_scenarios(
        [ScenarioType.RCP26, ScenarioType.RCP85], years=50
    )
    assert results["rcp85"].projection[-1].co2_ppm > results["rcp26"].projection[-1].co2_ppm


# ── SCENARIO_DEFAULTS ─────────────────────────────────────────────────────────

def test_scenario_defaults_all_scenarios():
    for scenario in ScenarioType:
        assert scenario in SCENARIO_DEFAULTS


def test_scenario_defaults_have_required_keys():
    for scenario, defaults in SCENARIO_DEFAULTS.items():
        assert "name" in defaults
        assert "co2_growth_rate" in defaults
        assert "description" in defaults
