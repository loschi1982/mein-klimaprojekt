"""
Router: Climate Analysis
Team-Branch: team/api
"""
import csv
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query

from models.schemas import ApiResponse, Co2Series, DataPoint, Meta

router = APIRouter(prefix="/api/v1/analysis", tags=["Climate Analysis"])

RAW_DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "raw"


def meta() -> Meta:
    return Meta(timestamp=datetime.now(timezone.utc).isoformat())


@router.get("/co2", response_model=ApiResponse, summary="CO₂-Trenddaten")
def analysis_co2(
    from_date: str | None = Query(None, examples=["2020-01-01"], description="Startdatum (ISO8601)"),
    to_date: str | None = Query(None, examples=["2024-12-31"], description="Enddatum (ISO8601)"),
):
    """Gibt normalisierte CO₂-Messdaten aus Mauna Loa zurück."""
    co2_file = RAW_DATA_DIR / "co2_mauna_loa.csv"
    if not co2_file.exists():
        raise HTTPException(
            status_code=404,
            detail={
                "code": "DATA_NOT_FOUND",
                "message": "CO₂-Daten nicht gefunden. Bitte zuerst POST /api/v1/ingest aufrufen.",
            },
        )

    series = []
    with open(co2_file) as f:
        for row in csv.DictReader(f):
            if from_date and row["date"] < from_date:
                continue
            if to_date and row["date"] > to_date:
                continue
            series.append(DataPoint(date=row["date"], value=float(row["value"])))

    return ApiResponse(data=Co2Series(series=series), meta=meta())


@router.get("/temperature", response_model=ApiResponse, summary="Temperaturdaten (Platzhalter)")
def analysis_temperature():
    """Temperaturdaten – wird von team/climate-analysis implementiert."""
    raise HTTPException(
        status_code=404,
        detail={
            "code": "DATA_NOT_FOUND",
            "message": "Temperaturdaten noch nicht verfügbar. Wird von team/climate-analysis implementiert.",
        },
    )
