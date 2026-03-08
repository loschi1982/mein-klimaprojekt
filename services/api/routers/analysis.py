"""
Router: Climate Analysis
Team-Branch: team/climate-analysis / team/api
"""
from datetime import datetime, timezone
from pathlib import Path
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
from modules.data_ingestion.sources import SOURCES

router = APIRouter(prefix="/api/v1/analysis", tags=["Climate Analysis"])

RAW_DIR = Path(__file__).parent.parent.parent.parent / "data" / "raw"


def meta() -> Meta:
    return Meta(timestamp=datetime.now(timezone.utc).isoformat())


def _load_normalized(source_id: str, from_date: str | None, to_date: str | None):
    """Lädt eine normalisierte CSV-Datei und filtert nach Zeitraum."""
    csv_file = RAW_DIR / f"{source_id}.csv"
    if not csv_file.exists():
        raise FileNotFoundError(
            f"Datensatz '{source_id}' nicht gefunden. "
            f"Bitte zuerst importieren: POST /api/v1/ingest mit source='{source_id}'"
        )
    series = load_series(csv_file)
    if from_date:
        series = [(d, v) for d, v in series if d >= from_date]
    if to_date:
        series = [(d, v) for d, v in series if d <= to_date]
    return series


@router.get("/co2", response_model=ApiResponse, summary="CO₂-Messdaten")
def analysis_co2(
    from_date: str | None = Query(None, description="Startdatum (ISO8601)"),
    to_date: str | None = Query(None, description="Enddatum (ISO8601)"),
):
    """Gibt normalisierte CO₂-Messdaten zurück (Mauna Loa)."""
    try:
        series_raw = _load_normalized("esrl_mauna_loa", from_date, to_date)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail={"code": "DATA_NOT_FOUND", "message": str(e)})
    except ValueError as e:
        raise HTTPException(status_code=400, detail={"code": "INVALID_PARAMS", "message": str(e)})

    return ApiResponse(
        data=Co2Series(series=[DataPoint(date=d, value=v) for d, v in series_raw]),
        meta=meta(),
    )


@router.get("/series/{source_id}", response_model=ApiResponse, summary="Generische Zeitreihe")
def analysis_series(
    source_id: str,
    from_date: str | None = Query(None, description="Startdatum (ISO8601)"),
    to_date: str | None = Query(None, description="Enddatum (ISO8601)"),
):
    """
    Gibt normalisierte Messdaten für eine beliebige Datenquelle zurück.
    source_id: esrl_mauna_loa | esrl_co2_global | esrl_ch4 | nasa_giss_global
    """
    if source_id not in SOURCES:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_SOURCE", "message": f"Unbekannte Quelle: {source_id}"},
        )
    try:
        series_raw = _load_normalized(source_id, from_date, to_date)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail={"code": "DATA_NOT_FOUND", "message": str(e)})

    source = SOURCES[source_id]
    return ApiResponse(
        data={
            "source_id": source_id,
            "name": source.name,
            "unit": source.unit,
            "source_url": source.source_url,
            "count": len(series_raw),
            "series": [{"date": d, "value": v} for d, v in series_raw],
        },
        meta=meta(),
    )


@router.get("/co2/stats", response_model=ApiResponse, summary="CO₂-Statistik")
def analysis_co2_stats(
    from_date: str | None = Query(None),
    to_date: str | None = Query(None),
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
    z_threshold: float = Query(2.5),
):
    """Z-Score-basierte Anomalie-Detektion."""
    try:
        result = analyze_co2(from_date=from_date, to_date=to_date)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail={"code": "DATA_NOT_FOUND", "message": str(e)})

    co2_file = RAW_DIR / "esrl_mauna_loa.csv"
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
    use_llm: bool = Query(False),
):
    """DataAnalystAgent + TrendDetectorAgent-Bericht."""
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


@router.get("/temperature", response_model=ApiResponse, summary="Globale Temperaturanomalie")
def analysis_temperature(
    from_date: str | None = Query(None, description="Startdatum (ISO8601)"),
    to_date: str | None = Query(None, description="Enddatum (ISO8601)"),
):
    """NASA GISS globale Temperaturanomalie (1880–heute, Referenz 1951–1980)."""
    try:
        series_raw = _load_normalized("nasa_giss_global", from_date, to_date)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail={"code": "DATA_NOT_FOUND", "message": str(e)})

    source = SOURCES["nasa_giss_global"]
    return ApiResponse(
        data={
            "source_id": "nasa_giss_global",
            "name": source.name,
            "unit": source.unit,
            "source_url": source.source_url,
            "baseline": "1951–1980",
            "count": len(series_raw),
            "series": [{"date": d, "value": v} for d, v in series_raw],
        },
        meta=meta(),
    )
