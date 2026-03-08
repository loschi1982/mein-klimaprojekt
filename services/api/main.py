"""
FastAPI Backend – Klimadaten-Projekt
Team-Branch: team/api

Start: uvicorn main:app --reload --port 8000
Docs:  http://localhost:8000/docs
"""
import sys
from pathlib import Path

# Projekt-Root ins Python-Pfad aufnehmen
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from modules.data_ingestion.ingester import list_datasets, normalize_co2_mauna_loa, download_co2_mauna_loa

app = FastAPI(
    title="Klimadaten API",
    description="REST API für das KI-gestützte Klimadaten-Projekt",
    version="1.0.0",
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def meta() -> dict:
    return {"timestamp": datetime.now(timezone.utc).isoformat(), "version": "1.0.0"}


# ── Health ──────────────────────────────────────────────────────────────────

@app.get("/api/v1/health")
def health_check():
    return {"data": {"status": "ok"}, "meta": meta()}


# ── Data Ingestion ──────────────────────────────────────────────────────────

class IngestRequest(BaseModel):
    source: str  # z.B. "esrl_mauna_loa"


@app.post("/api/v1/ingest")
def ingest(request: IngestRequest):
    if request.source == "esrl_mauna_loa":
        try:
            raw = download_co2_mauna_loa()
            output = normalize_co2_mauna_loa(raw)
            return {"data": {"status": "done", "file": str(output.name)}, "meta": meta()}
        except Exception as e:
            raise HTTPException(status_code=500, detail={"code": "PROCESSING_ERROR", "message": str(e)})
    raise HTTPException(status_code=400, detail={"code": "INVALID_PARAMS", "message": f"Unbekannte Quelle: {request.source}"})


@app.get("/api/v1/datasets")
def get_datasets():
    return {"data": list_datasets(), "meta": meta()}


# ── Climate Analysis ────────────────────────────────────────────────────────

@app.get("/api/v1/analysis/co2")
def analysis_co2(from_date: str | None = None, to_date: str | None = None):
    """CO₂-Trenddaten aus den normalisierten Rohdaten."""
    import csv
    from pathlib import Path

    co2_file = Path(__file__).parent.parent.parent / "data" / "raw" / "co2_mauna_loa.csv"
    if not co2_file.exists():
        raise HTTPException(
            status_code=404,
            detail={"code": "DATA_NOT_FOUND", "message": "CO₂-Daten nicht gefunden. Bitte zuerst POST /api/v1/ingest aufrufen."}
        )

    series = []
    with open(co2_file) as f:
        for row in csv.DictReader(f):
            if from_date and row["date"] < from_date:
                continue
            if to_date and row["date"] > to_date:
                continue
            series.append({"date": row["date"], "value": float(row["value"])})

    return {
        "data": {"unit": "ppm", "series": series},
        "meta": meta(),
    }


# ── Charts ──────────────────────────────────────────────────────────────────

@app.get("/api/v1/charts/{chart_id}")
def get_chart(chart_id: str):
    """Gibt Chart-Metadaten zurück (Daten kommen vom jeweiligen Analyse-Endpunkt)."""
    charts = {
        "co2_timeseries": {
            "chart_id": "co2_timeseries",
            "type": "line",
            "title": "CO₂-Konzentration (Mauna Loa)",
            "x_label": "Datum",
            "y_label": "ppm",
            "data_endpoint": "/api/v1/analysis/co2",
        }
    }
    if chart_id not in charts:
        raise HTTPException(status_code=404, detail={"code": "DATA_NOT_FOUND", "message": f"Chart '{chart_id}' nicht gefunden."})
    return {"data": charts[chart_id], "meta": meta()}


# ── AI Explanation ──────────────────────────────────────────────────────────

class ExplainRequest(BaseModel):
    data_point: dict
    question: str


@app.post("/api/v1/explain")
def explain(request: ExplainRequest):
    """Erklärt einen Datenpunkt in einfacher Sprache via Claude API."""
    import os
    try:
        import anthropic
    except ImportError:
        raise HTTPException(status_code=500, detail={"code": "PROCESSING_ERROR", "message": "anthropic-Paket nicht installiert."})

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail={"code": "AUTH_REQUIRED", "message": "ANTHROPIC_API_KEY nicht gesetzt."})

    client = anthropic.Anthropic(api_key=api_key)
    prompt = (
        f"Du bist ein Klimawissenschaftler, der Daten einfach erklärt.\n"
        f"Datenpunkt: {request.data_point}\n"
        f"Frage: {request.question}\n"
        f"Erkläre in 2-3 Sätzen, verständlich für Anfänger."
    )
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    return {
        "data": {
            "explanation": message.content[0].text,
            "confidence": "high",
        },
        "meta": meta(),
    }
