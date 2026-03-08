"""API-Tests für das FastAPI-Backend"""
import pytest
from fastapi.testclient import TestClient

from services.api.main import app

client = TestClient(app)


# ── Health ───────────────────────────────────────────────────────────────────

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "ok"
    assert "timestamp" in data["meta"]


# ── Data Ingestion ────────────────────────────────────────────────────────────

def test_get_datasets():
    response = client.get("/api/v1/datasets")
    assert response.status_code == 200
    assert isinstance(response.json()["data"], list)


def test_ingest_invalid_source():
    response = client.post("/api/v1/ingest", json={"source": "unbekannte_quelle"})
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_PARAMS"


# ── Charts ────────────────────────────────────────────────────────────────────

def test_get_chart_co2():
    response = client.get("/api/v1/charts/co2_timeseries")
    assert response.status_code == 200
    chart = response.json()["data"]
    assert chart["chart_id"] == "co2_timeseries"
    assert chart["type"] == "line"
    assert "data_endpoint" in chart


def test_list_charts():
    response = client.get("/api/v1/charts/")
    assert response.status_code == 200
    charts = response.json()["data"]
    assert len(charts) >= 1
    assert any(c["chart_id"] == "co2_timeseries" for c in charts)


def test_get_chart_not_found():
    response = client.get("/api/v1/charts/nonexistent")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "DATA_NOT_FOUND"


# ── Simulation ────────────────────────────────────────────────────────────────

def test_list_scenarios():
    response = client.get("/api/v1/scenarios")
    assert response.status_code == 200
    scenarios = response.json()["data"]
    ids = [s["id"] for s in scenarios]
    assert "rcp26" in ids
    assert "rcp45" in ids
    assert "rcp85" in ids


def test_simulate_rcp45():
    response = client.post("/api/v1/simulate", json={"scenario": "rcp45", "years": 10})
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["scenario"] == "rcp45"
    assert len(data["projection"]) == 11  # 0..10 Jahre
    assert data["projection"][0]["year"] == 2026
    assert data["projection"][10]["co2_ppm"] > data["projection"][0]["co2_ppm"]


def test_simulate_invalid_scenario():
    response = client.post("/api/v1/simulate", json={"scenario": "nonexistent", "years": 10})
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_PARAMS"


# ── AI Explanation (ohne API-Key) ─────────────────────────────────────────────

def test_explain_without_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    response = client.post("/api/v1/explain", json={
        "data_point": {"type": "co2", "value": 421.5, "date": "2024-03"},
        "question": "Warum ist dieser Wert so hoch?",
    })
    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "AUTH_REQUIRED"
