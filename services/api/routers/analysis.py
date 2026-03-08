"""
Router: Climate Analysis
Team-Branch: team/climate-analysis / team/api
"""
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from dataclasses import asdict

from models.schemas import ApiResponse, Co2Series, DataPoint, Meta
from modules.climate_analysis.analyzer import (
    analyze_co2,
    load_series,
    compute_stats,
    compute_trend,
    detect_anomalies,
)
from modules.climate_analysis.agents import DataAnalystAgent, TrendDetectorAgent

router = APIRouter(prefix="/api/v1/analysis", tags=["Climate Analysis"])


def meta() -> Meta:
    return Meta(timestamp=datetime.now(timezone.utc).isoformat())


@router.get("/co2", response_model=ApiResponse, summary="CO₂-Messdaten")
def analysis_co2(
    from_date: str | None = Query(None, description="Startdatum (ISO8601)"),
    to_date: str | None = Query(None, description="Enddatum (ISO8601)"),
):
    """Gibt normalisierte CO₂-Messdaten zurück."""
    try:
        result = analyze_co2(from_date=from_date, to_date=to_date)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail={"code": "DATA_NOT_FOUND", "message": str(e)})
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"code": "INVALID_PARAMS", "message": str(e)})

    from pathlib import Path
    co2_file = Path(__file__).parent.parent.parent.parent / "data" / "raw" / "co2_mauna_loa.csv"
    series_raw = load_series(co2_file)
    if from_date:
        series_raw = [(d, v) for d, v in series_raw if d >= from_date]
    if to_date:
        series_raw = [(d, v) for d, v in series_raw if d <= to_date]

    return ApiResponse(
        data=Co2Series(series=[DataPoint(date=d, value=v) for d, v in series_raw]),
        meta=meta(),
    )


@router.get("/co2/stats", response_model=ApiResponse, summary="CO₂-Statistik")
def analysis_co2_stats(
    from_date: str | None = Query(None, description="Startdatum (ISO8601)"),
    to_date: str | None = Query(None, description="Enddatum (ISO8601)"),
):
    """Deskriptive Statistik: Mittelwert, Median, Std, Min, Max, Trend."""
    try:
        result = analyze_co2(from_date=from_date, to_date=to_date)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail={"code": "DATA_NOT_FOUND", "message": str(e)})
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"code": "INVALID_PARAMS", "message": str(e)})

    return ApiResponse(
        data={
            "stats": asdict(result.stats),
            "trend": asdict(result.trend),
            "anomaly_count": len(result.anomalies),
        },
        meta=meta(),
    )


@router.get("/co2/anomalies", response_model=ApiResponse, summary="CO₂-Anomalien")
def analysis_co2_anomalies(
    from_date: str | None = Query(None),
    to_date: str | None = Query(None),
    z_threshold: float = Query(2.5, description="Z-Score-Schwellenwert"),
):
    """Z-Score-basierte Anomalie-Detektion."""
    try:
        result = analyze_co2(from_date=from_date, to_date=to_date)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail={"code": "DATA_NOT_FOUND", "message": str(e)})

    from pathlib import Path
    co2_file = Path(__file__).parent.parent.parent.parent / "data" / "raw" / "co2_mauna_loa.csv"
    series = load_series(co2_file)
    anomalies = detect_anomalies(series, z_threshold=z_threshold)

    return ApiResponse(
        data={
            "z_threshold": z_threshold,
            "total_points": result.stats.count,
            "anomalies": [asdict(a) for a in anomalies],
        },
        meta=meta(),
    )


@router.get("/co2/agent-report", response_model=ApiResponse, summary="KI-Analysebericht")
def analysis_co2_agent_report(
    from_date: str | None = Query(None),
    to_date: str | None = Query(None),
    use_llm: bool = Query(False, description="Claude API verwenden (ANTHROPIC_API_KEY erforderlich)"),
):
    """
    DataAnalystAgent + TrendDetectorAgent-Bericht.
    Gibt strukturierte Befunde und Empfehlungen zurück.
    """
    try:
        full_result = analyze_co2(from_date=from_date, to_date=to_date)
        recent_result = analyze_co2(from_date="2015-01-01", to_date=to_date)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail={"code": "DATA_NOT_FOUND", "message": str(e)})

    analyst = DataAnalystAgent(use_llm=use_llm)
    trend_agent = TrendDetectorAgent(use_llm=use_llm)

    analyst_report = analyst.run(full_result)
    trend_report = trend_agent.run(full_result, recent_result)

    return ApiResponse(
        data={
            "analyst": {
                "summary": analyst_report.summary,
                "findings": analyst_report.findings,
                "recommendations": analyst_report.recommendations,
            },
            "trend_detector": {
                "summary": trend_report.summary,
                "findings": trend_report.findings,
                "recommendations": trend_report.recommendations,
            },
        },
        meta=meta(),
    )


@router.get("/temperature", response_model=ApiResponse, summary="Temperaturdaten")
def analysis_temperature():
    """Temperaturdaten – folgt in Phase 2 (team/climate-analysis)."""
    raise HTTPException(
        status_code=404,
        detail={
            "code": "DATA_NOT_FOUND",
            "message": "Temperaturdaten noch nicht verfügbar.",
        },
    )
