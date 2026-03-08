"""Unit Tests für das Climate Analysis Module"""
import math
import tempfile
from pathlib import Path

import pytest

from modules.climate_analysis.analyzer import (
    annual_means,
    compute_stats,
    compute_trend,
    detect_anomalies,
    load_series,
    _interpret_trend,
)
from modules.climate_analysis.agents import DataAnalystAgent, TrendDetectorAgent, AgentReport


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_csv(rows: list[tuple[str, float]]) -> Path:
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False)
    tmp.write("date,value,unit,source,ingested_at\n")
    for date, value in rows:
        tmp.write(f"{date},{value},ppm,test,2026-01-01T00:00:00Z\n")
    tmp.flush()
    return Path(tmp.name)


MONTHLY_DATA = [(f"200{y}-{m:02d}-01", 370.0 + y * 2 + m * 0.1)
                for y in range(5) for m in range(1, 13)]

SIMPLE_SERIES = [("2020-01-01", 415.0), ("2021-01-01", 417.0),
                 ("2022-01-01", 419.0), ("2023-01-01", 421.0)]


# ── load_series ───────────────────────────────────────────────────────────────

def test_load_series_basic():
    path = make_csv(SIMPLE_SERIES)
    series = load_series(path)
    assert len(series) == 4
    assert series[0] == ("2020-01-01", 415.0)


def test_load_series_sorted():
    shuffled = [("2023-01-01", 421.0), ("2020-01-01", 415.0), ("2021-01-01", 417.0)]
    path = make_csv(shuffled)
    series = load_series(path)
    dates = [d for d, _ in series]
    assert dates == sorted(dates)


def test_load_series_skips_invalid():
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False)
    tmp.write("date,value,unit,source,ingested_at\n")
    tmp.write("2020-01-01,415.0,ppm,test,2026-01-01T00:00:00Z\n")
    tmp.write("2021-01-01,INVALID,ppm,test,2026-01-01T00:00:00Z\n")
    tmp.flush()
    series = load_series(Path(tmp.name))
    assert len(series) == 1


# ── annual_means ──────────────────────────────────────────────────────────────

def test_annual_means_count():
    path = make_csv(MONTHLY_DATA)
    series = load_series(path)
    means = annual_means(series)
    assert len(means) == 5  # 5 Jahre


def test_annual_means_values_in_range():
    path = make_csv(MONTHLY_DATA)
    series = load_series(path)
    means = annual_means(series)
    first_year_values = [v for d, v in MONTHLY_DATA if d.startswith("2000")]
    expected_mean = sum(first_year_values) / len(first_year_values)
    assert means[0][1] == pytest.approx(expected_mean, rel=1e-6)


def test_annual_means_sorted():
    path = make_csv(MONTHLY_DATA)
    series = load_series(path)
    means = annual_means(series)
    years = [y for y, _ in means]
    assert years == sorted(years)


# ── compute_stats ─────────────────────────────────────────────────────────────

def test_stats_count():
    stats = compute_stats(SIMPLE_SERIES)
    assert stats.count == 4


def test_stats_mean():
    stats = compute_stats(SIMPLE_SERIES)
    expected = (415 + 417 + 419 + 421) / 4
    assert stats.mean == pytest.approx(expected, rel=1e-6)


def test_stats_min_max():
    stats = compute_stats(SIMPLE_SERIES)
    assert stats.min == 415.0
    assert stats.max == 421.0
    assert stats.min_date == "2020-01-01"
    assert stats.max_date == "2023-01-01"


def test_stats_unit():
    stats = compute_stats(SIMPLE_SERIES, unit="ppm")
    assert stats.unit == "ppm"


def test_stats_empty_raises():
    with pytest.raises(ValueError, match="Leere Zeitreihe"):
        compute_stats([])


def test_stats_std_positive():
    stats = compute_stats(SIMPLE_SERIES)
    assert stats.std > 0


def test_stats_median():
    series = [("2020-01-01", 410.0), ("2021-01-01", 415.0), ("2022-01-01", 420.0)]
    stats = compute_stats(series)
    assert stats.median == 415.0


# ── compute_trend ─────────────────────────────────────────────────────────────

def test_trend_slope_positive():
    trend = compute_trend(SIMPLE_SERIES, unit="ppm")
    assert trend.slope > 0  # Anstieg erwartet


def test_trend_r_squared_range():
    trend = compute_trend(SIMPLE_SERIES, unit="ppm")
    assert 0.0 <= trend.r_squared <= 1.0


def test_trend_perfect_linear():
    # Perfekt linearer Datensatz → R² muss 1.0 sein
    series = [(f"200{i}-01-01", 400.0 + i * 2.0) for i in range(5)]
    trend = compute_trend(series, unit="ppm")
    assert trend.r_squared == pytest.approx(1.0, abs=1e-9)


def test_trend_too_few_points():
    with pytest.raises(ValueError, match="Mindestens 2"):
        compute_trend([("2020-01-01", 415.0)])


def test_trend_interpretation_strong_rise():
    result = _interpret_trend(3.0, "ppm")
    assert "Starker Anstieg" in result


def test_trend_interpretation_moderate():
    result = _interpret_trend(1.5, "ppm")
    assert "Moderater Anstieg" in result


def test_trend_interpretation_decline():
    result = _interpret_trend(-0.5, "ppm")
    assert "Rückgang" in result


# ── detect_anomalies ──────────────────────────────────────────────────────────

def test_detect_no_anomalies_uniform():
    series = [(f"202{i}-01-01", 415.0) for i in range(5)]
    anomalies = detect_anomalies(series)
    assert anomalies == []


def test_detect_anomaly_extreme_value():
    series = [(f"200{i}-01-01", 370.0) for i in range(9)]
    series.append(("2009-01-01", 9999.0))  # Extrem-Ausreißer
    anomalies = detect_anomalies(series)
    assert len(anomalies) >= 1
    assert any(a.date == "2009-01-01" for a in anomalies)


def test_detect_anomaly_severity():
    # Alle Werte nah beieinander, ein extremer Ausreißer → severity != "normal"
    series = [(f"2000-{m:02d}-01", 370.0) for m in range(1, 10)]
    series.append(("2000-10-01", 9999.0))
    anomalies = detect_anomalies(series)
    assert len(anomalies) >= 1
    assert all(a.severity in ("warning", "critical") for a in anomalies)


def test_detect_too_few_points():
    series = [("2020-01-01", 415.0), ("2021-01-01", 420.0)]
    anomalies = detect_anomalies(series)
    assert anomalies == []


def test_detect_z_score_computed():
    series = [(f"200{i}-01-01", 370.0) for i in range(9)]
    series.append(("2009-01-01", 9999.0))
    anomalies = detect_anomalies(series)
    assert all(isinstance(a.z_score, float) for a in anomalies)


# ── analyze_co2 + _save_result ────────────────────────────────────────────────

def test_analyze_co2_file_not_found():
    from modules.climate_analysis.analyzer import analyze_co2
    import modules.climate_analysis.analyzer as ana
    original = ana.RAW_DIR
    ana.RAW_DIR = Path("/tmp/nonexistent_xyz")
    with pytest.raises(FileNotFoundError):
        analyze_co2()
    ana.RAW_DIR = original


def test_analyze_co2_returns_result(tmp_path):
    from modules.climate_analysis.analyzer import analyze_co2, AnalysisResult
    import modules.climate_analysis.analyzer as ana

    # Echte CSV anlegen
    csv_path = tmp_path / "co2_mauna_loa.csv"
    csv_path.write_text(
        "date,value,unit,source,ingested_at\n"
        + "\n".join(f"200{y}-{m:02d}-01,{370+y*2+m*0.1:.1f},ppm,test,2026-01-01T00:00:00Z"
                    for y in range(5) for m in range(1, 13))
    )
    original_raw = ana.RAW_DIR
    original_proc = ana.PROCESSED_DIR
    ana.RAW_DIR = tmp_path
    ana.PROCESSED_DIR = tmp_path / "processed"

    result = analyze_co2()
    assert isinstance(result, AnalysisResult)
    assert result.stats.count == 60
    assert result.trend.slope != 0

    ana.RAW_DIR = original_raw
    ana.PROCESSED_DIR = original_proc


def test_analyze_co2_with_date_filter(tmp_path):
    from modules.climate_analysis.analyzer import analyze_co2
    import modules.climate_analysis.analyzer as ana

    csv_path = tmp_path / "co2_mauna_loa.csv"
    csv_path.write_text(
        "date,value,unit,source,ingested_at\n"
        "2020-01-01,415.0,ppm,test,2026-01-01T00:00:00Z\n"
        "2021-01-01,417.0,ppm,test,2026-01-01T00:00:00Z\n"
        "2022-01-01,419.0,ppm,test,2026-01-01T00:00:00Z\n"
    )
    original_raw = ana.RAW_DIR
    original_proc = ana.PROCESSED_DIR
    ana.RAW_DIR = tmp_path
    ana.PROCESSED_DIR = tmp_path / "processed"

    result = analyze_co2(from_date="2021-01-01", to_date="2022-12-31")
    assert result.stats.count == 2

    ana.RAW_DIR = original_raw
    ana.PROCESSED_DIR = original_proc


def test_analyze_co2_empty_range_raises(tmp_path):
    from modules.climate_analysis.analyzer import analyze_co2
    import modules.climate_analysis.analyzer as ana

    csv_path = tmp_path / "co2_mauna_loa.csv"
    csv_path.write_text(
        "date,value,unit,source,ingested_at\n"
        "2020-01-01,415.0,ppm,test,2026-01-01T00:00:00Z\n"
    )
    original_raw = ana.RAW_DIR
    original_proc = ana.PROCESSED_DIR
    ana.RAW_DIR = tmp_path
    ana.PROCESSED_DIR = tmp_path / "processed"

    with pytest.raises(ValueError, match="Keine Daten"):
        analyze_co2(from_date="2099-01-01")

    ana.RAW_DIR = original_raw
    ana.PROCESSED_DIR = original_proc


# ── DataAnalystAgent ──────────────────────────────────────────────────────────

def _make_analysis_result():
    from modules.climate_analysis.analyzer import AnalysisResult, SeriesStats, TrendResult
    stats = SeriesStats(
        count=816, mean=390.5, median=389.0, std=15.2,
        min=313.0, max=430.0, min_date="1958-03-01",
        max_date="2026-01-01", unit="ppm",
    )
    trend = TrendResult(
        slope=1.85, intercept=310.0, r_squared=0.98,
        p_value=None, unit="ppm",
        interpretation="Moderater Anstieg: +1.85 ppm/Jahr",
    )
    return AnalysisResult(source="esrl_mauna_loa", unit="ppm",
                          stats=stats, trend=trend, anomalies=[])


def test_analyst_agent_returns_report():
    result = _make_analysis_result()
    agent = DataAnalystAgent(use_llm=False)
    report = agent.run(result)
    assert isinstance(report, AgentReport)
    assert report.agent == "DataAnalystAgent"
    assert len(report.findings) > 0
    assert len(report.recommendations) > 0
    assert report.summary


def test_analyst_agent_findings_contain_trend():
    result = _make_analysis_result()
    agent = DataAnalystAgent(use_llm=False)
    report = agent.run(result)
    assert any("Trend" in f for f in report.findings)


def test_analyst_agent_high_r2_finding():
    result = _make_analysis_result()
    agent = DataAnalystAgent(use_llm=False)
    report = agent.run(result)
    assert any("R²" in f or "Linearität" in f for f in report.findings)


# ── TrendDetectorAgent ────────────────────────────────────────────────────────

def test_trend_agent_returns_report():
    result = _make_analysis_result()
    agent = TrendDetectorAgent(use_llm=False)
    report = agent.run(result)
    assert isinstance(report, AgentReport)
    assert report.agent == "TrendDetectorAgent"


def test_trend_agent_with_recent():
    full = _make_analysis_result()
    from modules.climate_analysis.analyzer import AnalysisResult, SeriesStats, TrendResult
    recent_stats = SeriesStats(count=120, mean=415.0, median=414.0, std=5.0,
                               min=400.0, max=430.0, min_date="2015-01-01",
                               max_date="2026-01-01", unit="ppm")
    recent_trend = TrendResult(slope=2.5, intercept=380.0, r_squared=0.97,
                               p_value=None, unit="ppm",
                               interpretation="Moderater Anstieg: +2.50 ppm/Jahr")
    recent = AnalysisResult(source="esrl_mauna_loa", unit="ppm",
                            stats=recent_stats, trend=recent_trend, anomalies=[])

    agent = TrendDetectorAgent(use_llm=False)
    report = agent.run(full, recent)
    assert any("Kurzzeit" in f for f in report.findings)


def test_trend_agent_acceleration_detected():
    full = _make_analysis_result()  # slope=1.85
    from modules.climate_analysis.analyzer import AnalysisResult, SeriesStats, TrendResult
    recent_stats = SeriesStats(count=120, mean=420.0, median=420.0, std=4.0,
                               min=405.0, max=430.0, min_date="2015-01-01",
                               max_date="2026-01-01", unit="ppm")
    recent_trend = TrendResult(slope=3.0, intercept=390.0, r_squared=0.96,
                               p_value=None, unit="ppm",
                               interpretation="Starker Anstieg: +3.00 ppm/Jahr")
    recent = AnalysisResult(source="esrl_mauna_loa", unit="ppm",
                            stats=recent_stats, trend=recent_trend, anomalies=[])

    agent = TrendDetectorAgent(use_llm=False)
    report = agent.run(full, recent)
    assert any("Beschleunigung" in f for f in report.findings)
