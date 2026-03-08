"""API-Tests für das FastAPI-Backend"""
import pytest
from fastapi.testclient import TestClient

from services.api.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "ok"
    assert "timestamp" in data["meta"]


def test_get_datasets():
    response = client.get("/api/v1/datasets")
    assert response.status_code == 200
    assert isinstance(response.json()["data"], list)


def test_get_chart_co2():
    response = client.get("/api/v1/charts/co2_timeseries")
    assert response.status_code == 200
    chart = response.json()["data"]
    assert chart["chart_id"] == "co2_timeseries"
    assert chart["type"] == "line"


def test_get_chart_not_found():
    response = client.get("/api/v1/charts/nonexistent")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "DATA_NOT_FOUND"


def test_ingest_invalid_source():
    response = client.post("/api/v1/ingest", json={"source": "unbekannte_quelle"})
    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "INVALID_PARAMS"
