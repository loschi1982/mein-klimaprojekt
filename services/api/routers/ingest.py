"""
Router: Data Ingestion
Team-Branch: team/api / team/data-ingestion
"""
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException

from models.schemas import ApiResponse, IngestRequest, IngestResponse, DatasetInfo, Meta
from modules.data_ingestion.ingester import (
    run_pipeline,
    list_datasets,
    list_available_sources,
)

router = APIRouter(prefix="/api/v1", tags=["Data Ingestion"])


def meta() -> Meta:
    return Meta(timestamp=datetime.now(timezone.utc).isoformat())


@router.get("/sources", response_model=ApiResponse, summary="Verfügbare Datenquellen")
def get_sources():
    """Listet alle konfigurierten Datenquellen auf."""
    return ApiResponse(data=list_available_sources(), meta=meta())


@router.post("/ingest", response_model=ApiResponse, summary="Datenabruf starten")
def ingest(request: IngestRequest):
    """
    Führt die vollständige Ingestion-Pipeline aus:
    Download → Normalisierung → Validierung
    """
    result = run_pipeline(request.source)

    if result["status"] == "error":
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_PARAMS",
                "message": result["errors"][0] if result["errors"] else "Unbekannter Fehler",
            },
        )
    if result["status"] == "validation_failed":
        raise HTTPException(
            status_code=500,
            detail={"code": "PROCESSING_ERROR", "message": "Validierung fehlgeschlagen"},
        )

    return ApiResponse(
        data=IngestResponse(status=result["status"], file=result["normalized_file"]),
        meta=meta(),
    )


@router.get("/datasets", response_model=ApiResponse, summary="Datensätze auflisten")
def get_datasets():
    """Listet alle verfügbaren normalisierten Datensätze auf."""
    datasets = [DatasetInfo(**d) for d in list_datasets()]
    return ApiResponse(data=datasets, meta=meta())
