"""
Gemeinsame Pydantic-Schemas für die Klimadaten-API.
Team-Branch: team/api
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── Meta ──────────────────────────────────────────────────────────────────────

class Meta(BaseModel):
    timestamp: str
    version: str = "1.0.0"


class ApiResponse(BaseModel):
    data: Any
    meta: Meta


class ApiError(BaseModel):
    code: str
    message: str
    details: dict = Field(default_factory=dict)


# ── Data Ingestion ─────────────────────────────────────────────────────────────

class IngestRequest(BaseModel):
    source: str = Field(..., examples=["esrl_mauna_loa"], description="Datenquelle")
    date_from: str | None = Field(None, examples=["2020-01-01"])
    date_to: str | None = Field(None, examples=["2024-12-31"])


class IngestResponse(BaseModel):
    status: str
    file: str | None = None
    job_id: str | None = None


class DatasetInfo(BaseModel):
    id: str
    file: str
    rows: int
    updated: str


# ── Analysis ──────────────────────────────────────────────────────────────────

class DataPoint(BaseModel):
    date: str
    value: float


class Co2Series(BaseModel):
    unit: str = "ppm"
    series: list[DataPoint]


class TrendInfo(BaseModel):
    slope: float | None = None
    r_squared: float | None = None


# ── Charts ────────────────────────────────────────────────────────────────────

class ChartMeta(BaseModel):
    chart_id: str
    type: str
    title: str
    x_label: str
    y_label: str
    data_endpoint: str


# ── Simulation ────────────────────────────────────────────────────────────────

class SimulateRequest(BaseModel):
    scenario: str = Field(..., examples=["rcp45"])
    years: int = Field(50, ge=1, le=200)
    parameters: dict = Field(default_factory=dict)


class ScenarioInfo(BaseModel):
    id: str
    name: str
    description: str
    co2_growth_rate: float


# ── AI Explanation ────────────────────────────────────────────────────────────

class ExplainRequest(BaseModel):
    data_point: dict = Field(..., examples=[{"type": "co2", "value": 421.5, "date": "2024-03"}])
    question: str = Field(..., examples=["Warum ist dieser Wert so hoch?"])


class ExplainResponse(BaseModel):
    explanation: str
    confidence: str = "high"
    sources: list[str] = Field(default_factory=list)
