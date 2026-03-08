"""
Router: Data Ingestion
Team-Branch: team/api
"""
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException

from models.schemas import ApiResponse, IngestRequest, IngestResponse, DatasetInfo, Meta
from modules.data_ingestion.ingester import (
    download_co2_mauna_loa,
    normalize_co2_mauna_loa,
    list_datasets,
)

router = APIRouter(prefix="/api/v1", tags=["Data Ingestion"])


def meta() -> Meta:
    return Meta(timestamp=datetime.now(timezone.utc).isoformat())


@router.post("/ingest", response_model=ApiResponse, summary="Datenabruf starten")
def ingest(request: IngestRequest):
    """Lädt Klimadaten von einer externen Quelle herunter und normalisiert sie."""
    if request.source == "esrl_mauna_loa":
        try:
            raw = download_co2_mauna_loa()
            output = normalize_co2_mauna_loa(raw)
            return ApiResponse(
                data=IngestResponse(status="done", file=output.name),
                meta=meta(),
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail={"code": "PROCESSING_ERROR", "message": str(e)},
            )
    raise HTTPException(
        status_code=400,
        detail={"code": "INVALID_PARAMS", "message": f"Unbekannte Quelle: {request.source}"},
    )


@router.get("/datasets", response_model=ApiResponse, summary="Datensätze auflisten")
def get_datasets():
    """Listet alle verfügbaren normalisierten Datensätze auf."""
    datasets = [DatasetInfo(**d) for d in list_datasets()]
    return ApiResponse(data=datasets, meta=meta())
