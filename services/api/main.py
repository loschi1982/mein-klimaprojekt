"""
FastAPI Backend – Klimadaten-Projekt
Team-Branch: team/api

Start: uvicorn main:app --reload --port 8001
Docs:  http://localhost:8001/docs
"""
import sys
from pathlib import Path

# Projekt-Root ins Python-Pfad aufnehmen
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import ingest, analysis, charts, simulation, explain, knowledge, admin

app = FastAPI(
    title="Klimadaten API",
    description=(
        "REST API für das KI-gestützte Klimadaten-Projekt.\n\n"
        "## Teams\n"
        "- **Data Ingestion** – Datenabruf und Normalisierung\n"
        "- **Climate Analysis** – Statistische Analyse\n"
        "- **Visualization** – Chart-Metadaten\n"
        "- **Simulation** – Klimaszenarien\n"
        "- **AI Explanation** – Claude-Integration\n"
        "- **Knowledge Base** – Strukturiertes Klimawissen\n"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router einbinden
app.include_router(ingest.router)
app.include_router(analysis.router)
app.include_router(charts.router)
app.include_router(simulation.router)
app.include_router(explain.router)
app.include_router(knowledge.router)
app.include_router(admin.router)


@app.get("/api/v1/health", tags=["System"])
def health_check():
    return {
        "data": {"status": "ok", "version": "1.0.0"},
        "meta": {"timestamp": datetime.now(timezone.utc).isoformat(), "version": "1.0.0"},
    }
