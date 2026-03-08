"""Unit Tests für Admin-Reports-Router"""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "api"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.api.routers.admin import router, REPORTS_DIR
import services.api.routers.admin as admin_module
from fastapi import FastAPI
from models.schemas import ApiResponse

app = FastAPI()
app.include_router(router)
client = TestClient(app)


@pytest.fixture
def tmp_reports(tmp_path, monkeypatch):
    """Leitet REPORTS_DIR auf ein temporäres Verzeichnis um."""
    monkeypatch.setattr(admin_module, "REPORTS_DIR", tmp_path)
    return tmp_path


def test_list_reports_empty(tmp_reports):
    resp = client.get("/api/v1/admin/reports")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["count"] == 0
    assert data["reports"] == []


def test_save_report(tmp_reports):
    resp = client.post("/api/v1/admin/reports", json={
        "title": "Test-Bericht",
        "content": "<p>Hello</p>",
        "source_id": "esrl_mauna_loa",
        "tags": ["co2", "test"],
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "id" in data
    assert "created_at" in data


def test_save_report_creates_file(tmp_reports):
    client.post("/api/v1/admin/reports", json={
        "title": "Datei-Test",
        "content": "<h2>Inhalt</h2>",
        "source_id": "esrl_mauna_loa",
        "tags": [],
    })
    files = list(tmp_reports.glob("*.json"))
    assert len(files) == 1


def test_list_reports_after_save(tmp_reports):
    client.post("/api/v1/admin/reports", json={
        "title": "Bericht A",
        "content": "<p>A</p>",
        "source_id": "esrl_mauna_loa",
        "tags": ["a"],
    })
    resp = client.get("/api/v1/admin/reports")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["count"] == 1
    assert data["reports"][0]["title"] == "Bericht A"


def test_get_report(tmp_reports):
    save_resp = client.post("/api/v1/admin/reports", json={
        "title": "Detail-Bericht",
        "content": "<p>Inhalt</p>",
        "source_id": "esrl_ch4",
        "tags": ["ch4"],
    })
    report_id = save_resp.json()["data"]["id"]

    resp = client.get(f"/api/v1/admin/reports/{report_id}")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["title"] == "Detail-Bericht"
    assert data["content"] == "<p>Inhalt</p>"
    assert data["source_id"] == "esrl_ch4"
    assert "ch4" in data["tags"]


def test_get_report_not_found(tmp_reports):
    resp = client.get("/api/v1/admin/reports/nicht-vorhanden")
    assert resp.status_code == 404


def test_update_report(tmp_reports):
    save_resp = client.post("/api/v1/admin/reports", json={
        "title": "Alt",
        "content": "<p>alt</p>",
        "source_id": "esrl_mauna_loa",
        "tags": [],
    })
    report_id = save_resp.json()["data"]["id"]

    resp = client.put(f"/api/v1/admin/reports/{report_id}", json={
        "title": "Neu",
        "content": "<p>neu</p>",
        "source_id": "esrl_co2_global",
        "tags": ["updated"],
    })
    assert resp.status_code == 200

    get_resp = client.get(f"/api/v1/admin/reports/{report_id}")
    data = get_resp.json()["data"]
    assert data["title"] == "Neu"
    assert data["content"] == "<p>neu</p>"
    assert data["source_id"] == "esrl_co2_global"
    assert "updated" in data["tags"]


def test_update_report_not_found(tmp_reports):
    resp = client.put("/api/v1/admin/reports/xyz", json={
        "title": "T",
        "content": "C",
        "source_id": "esrl_mauna_loa",
        "tags": [],
    })
    assert resp.status_code == 404


def test_delete_report(tmp_reports):
    save_resp = client.post("/api/v1/admin/reports", json={
        "title": "Zum Löschen",
        "content": "<p>weg</p>",
        "source_id": "esrl_mauna_loa",
        "tags": [],
    })
    report_id = save_resp.json()["data"]["id"]

    del_resp = client.delete(f"/api/v1/admin/reports/{report_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["data"]["deleted"] == report_id

    # Nicht mehr vorhanden
    get_resp = client.get(f"/api/v1/admin/reports/{report_id}")
    assert get_resp.status_code == 404


def test_delete_report_not_found(tmp_reports):
    resp = client.delete("/api/v1/admin/reports/nicht-vorhanden")
    assert resp.status_code == 404


def test_multiple_reports_listed(tmp_reports):
    for i in range(3):
        client.post("/api/v1/admin/reports", json={
            "title": f"Bericht {i}",
            "content": f"<p>{i}</p>",
            "source_id": "esrl_mauna_loa",
            "tags": [],
        })
    resp = client.get("/api/v1/admin/reports")
    data = resp.json()["data"]
    assert data["count"] == 3


def test_report_has_created_at(tmp_reports):
    save_resp = client.post("/api/v1/admin/reports", json={
        "title": "Timestamp-Test",
        "content": "<p>x</p>",
        "source_id": "esrl_mauna_loa",
        "tags": [],
    })
    report_id = save_resp.json()["data"]["id"]
    get_resp = client.get(f"/api/v1/admin/reports/{report_id}")
    assert "created_at" in get_resp.json()["data"]
    assert "updated_at" in get_resp.json()["data"]


def test_report_update_changes_updated_at(tmp_reports):
    save_resp = client.post("/api/v1/admin/reports", json={
        "title": "Zeitstempel",
        "content": "<p>v1</p>",
        "source_id": "esrl_mauna_loa",
        "tags": [],
    })
    report_id = save_resp.json()["data"]["id"]
    orig = client.get(f"/api/v1/admin/reports/{report_id}").json()["data"]["created_at"]

    client.put(f"/api/v1/admin/reports/{report_id}", json={
        "title": "Zeitstempel",
        "content": "<p>v2</p>",
        "source_id": "esrl_mauna_loa",
        "tags": [],
    })
    updated = client.get(f"/api/v1/admin/reports/{report_id}").json()["data"]["updated_at"]
    assert "updated_at" in client.get(f"/api/v1/admin/reports/{report_id}").json()["data"]
    # created_at unverändert
    assert client.get(f"/api/v1/admin/reports/{report_id}").json()["data"]["created_at"] == orig


def test_list_reports_excludes_content(tmp_reports):
    """Listing soll keinen HTML-Inhalt enthalten (zu große Payload)."""
    client.post("/api/v1/admin/reports", json={
        "title": "Kein Inhalt in Liste",
        "content": "<p>sehr langer inhalt</p>",
        "source_id": "esrl_mauna_loa",
        "tags": [],
    })
    resp = client.get("/api/v1/admin/reports")
    reports = resp.json()["data"]["reports"]
    assert "content" not in reports[0]
