"""
Router: Charts & Visualization
Team-Branch: team/api
"""
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from models.schemas import ApiResponse, ChartMeta, Meta

router = APIRouter(prefix="/api/v1/charts", tags=["Visualization"])

CHARTS: dict[str, dict] = {
    "co2_timeseries": {
        "chart_id": "co2_timeseries",
        "type": "line",
        "title": "CO₂-Konzentration (Mauna Loa)",
        "x_label": "Datum",
        "y_label": "ppm",
        "data_endpoint": "/api/v1/analysis/co2",
    },
    "temperature_anomaly": {
        "chart_id": "temperature_anomaly",
        "type": "bar",
        "title": "Globale Temperaturanomalie",
        "x_label": "Jahr",
        "y_label": "°C",
        "data_endpoint": "/api/v1/analysis/temperature",
    },
}


def meta() -> Meta:
    return Meta(timestamp=datetime.now(timezone.utc).isoformat())


@router.get("/{chart_id}", response_model=ApiResponse, summary="Chart-Metadaten abrufen")
def get_chart(chart_id: str):
    """Gibt Metadaten und den Daten-Endpunkt für einen Chart zurück."""
    if chart_id not in CHARTS:
        raise HTTPException(
            status_code=404,
            detail={"code": "DATA_NOT_FOUND", "message": f"Chart '{chart_id}' nicht gefunden."},
        )
    return ApiResponse(data=ChartMeta(**CHARTS[chart_id]), meta=meta())


@router.get("/", response_model=ApiResponse, summary="Alle Charts auflisten")
def list_charts():
    """Listet alle verfügbaren Charts auf."""
    return ApiResponse(
        data=[ChartMeta(**c) for c in CHARTS.values()],
        meta=meta(),
    )
