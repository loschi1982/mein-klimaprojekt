"""Unit Tests für ReportScanner und /api/v1/admin/scan-reports"""
from pathlib import Path
import sys
import json
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "api"))

from modules.climate_analysis.report_scanner import (
    ReportScanner,
    ScientificPaper,
    ScanResult,
    PRESET_TOPICS,
    _reconstruct_abstract,
    _rule_summary,
    _fetch_openalex,
)


# ── Hilfsfunktionen ────────────────────────────────────────────────────────────

def _make_paper(title="Test Paper", authors=None, year=2023, abstract="Test abstract."):
    return ScientificPaper(
        title=title,
        authors=authors or ["Author A", "Author B"],
        year=year,
        abstract=abstract,
        url="https://doi.org/10.1000/test",
        doi="https://doi.org/10.1000/test",
    )


FAKE_OPENALEX_RESPONSE = {
    "results": [
        {
            "title": "Arctic Amplification and Northern Hemisphere Warming",
            "authorships": [
                {"author": {"display_name": "Jane Smith"}},
                {"author": {"display_name": "John Doe"}},
            ],
            "publication_year": 2022,
            "doi": "https://doi.org/10.1000/arctic",
            "abstract_inverted_index": {
                "Arctic": [0], "amplification": [1], "causes": [2], "faster": [3], "warming": [4]
            },
            "primary_location": {"landing_page_url": "https://example.com/paper1"},
            "open_access": {},
        },
        {
            "title": "Polar Amplification Mechanisms",
            "authorships": [{"author": {"display_name": "Alice Brown"}}],
            "publication_year": 2021,
            "doi": "https://doi.org/10.1000/polar",
            "abstract_inverted_index": {
                "Polar": [0], "amplification": [1], "is": [2], "well": [3], "documented": [4]
            },
            "primary_location": {},
            "open_access": {},
        },
    ]
}


# ── _reconstruct_abstract ──────────────────────────────────────────────────────

def test_reconstruct_abstract_basic():
    idx = {"Hello": [0], "World": [1]}
    assert _reconstruct_abstract(idx) == "Hello World"


def test_reconstruct_abstract_none():
    assert _reconstruct_abstract(None) == ""


def test_reconstruct_abstract_empty():
    assert _reconstruct_abstract({}) == ""


def test_reconstruct_abstract_multiword():
    idx = {"The": [0], "quick": [1], "brown": [2], "fox": [3]}
    assert _reconstruct_abstract(idx) == "The quick brown fox"


# ── _rule_summary ──────────────────────────────────────────────────────────────

def test_rule_summary_contains_title():
    papers = [_make_paper(title="Climate Study 2023")]
    summary = _rule_summary(papers, "Klimatest")
    assert "Climate Study 2023" in summary


def test_rule_summary_contains_authors():
    papers = [_make_paper(authors=["Prof. Mustermann", "Dr. Test"])]
    summary = _rule_summary(papers, "Klimatest")
    assert "Prof. Mustermann" in summary


def test_rule_summary_contains_article_ref():
    papers = [_make_paper()]
    summary = _rule_summary(papers, "Klimatest")
    assert "[Artikel 1]" in summary


def test_rule_summary_multiple_papers():
    papers = [_make_paper(title=f"Paper {i}") for i in range(3)]
    summary = _rule_summary(papers, "Klimatest")
    assert "[Artikel 3]" in summary


def test_rule_summary_et_al_for_many_authors():
    papers = [_make_paper(authors=["A", "B", "C", "D", "E"])]
    summary = _rule_summary(papers, "Test")
    assert "et al." in summary


# ── PRESET_TOPICS ──────────────────────────────────────────────────────────────

def test_preset_topics_not_empty():
    assert len(PRESET_TOPICS) >= 3


def test_preset_topics_have_label_and_query():
    for t in PRESET_TOPICS:
        assert "label" in t and t["label"]
        assert "query" in t and t["query"]


def test_preset_topics_arctic_included():
    queries = [t["query"].lower() for t in PRESET_TOPICS]
    assert any("arctic" in q or "northern" in q for q in queries)


# ── _fetch_openalex (gemockt) ──────────────────────────────────────────────────

def _mock_urlopen(response_data):
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(response_data).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


def test_fetch_openalex_returns_papers():
    with patch("urllib.request.urlopen") as mock_open:
        mock_open.return_value = _mock_urlopen(FAKE_OPENALEX_RESPONSE)
        papers = _fetch_openalex("arctic amplification", 5)
    assert len(papers) == 2
    assert papers[0].title == "Arctic Amplification and Northern Hemisphere Warming"


def test_fetch_openalex_authors_parsed():
    with patch("urllib.request.urlopen") as mock_open:
        mock_open.return_value = _mock_urlopen(FAKE_OPENALEX_RESPONSE)
        papers = _fetch_openalex("arctic", 5)
    assert "Jane Smith" in papers[0].authors
    assert "John Doe" in papers[0].authors


def test_fetch_openalex_doi_set():
    with patch("urllib.request.urlopen") as mock_open:
        mock_open.return_value = _mock_urlopen(FAKE_OPENALEX_RESPONSE)
        papers = _fetch_openalex("arctic", 5)
    assert papers[0].doi == "https://doi.org/10.1000/arctic"


def test_fetch_openalex_abstract_reconstructed():
    with patch("urllib.request.urlopen") as mock_open:
        mock_open.return_value = _mock_urlopen(FAKE_OPENALEX_RESPONSE)
        papers = _fetch_openalex("arctic", 5)
    assert "amplification" in papers[0].abstract


def test_fetch_openalex_max_papers_respected():
    with patch("urllib.request.urlopen") as mock_open:
        mock_open.return_value = _mock_urlopen(FAKE_OPENALEX_RESPONSE)
        papers = _fetch_openalex("arctic", 1)
    assert len(papers) <= 1


# ── ReportScanner ──────────────────────────────────────────────────────────────

def test_scanner_returns_scan_result():
    scanner = ReportScanner()
    with patch("modules.climate_analysis.report_scanner._fetch_openalex") as mock_fetch:
        mock_fetch.return_value = [_make_paper()]
        result = scanner.scan("Arctic amplification")
    assert isinstance(result, ScanResult)
    assert len(result.summary) > 0


def test_scanner_no_llm_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    scanner = ReportScanner()
    with patch("modules.climate_analysis.report_scanner._fetch_openalex") as mock_fetch:
        mock_fetch.return_value = [_make_paper()]
        result = scanner.scan("test")
    assert result.used_llm is False


def test_scanner_empty_result_on_no_papers():
    scanner = ReportScanner()
    with patch("modules.climate_analysis.report_scanner._fetch_openalex") as mock_fetch:
        mock_fetch.return_value = []
        result = scanner.scan("xyzabcunknown123")
    assert len(result.papers) == 0
    assert len(result.summary) > 0  # Fehlermeldung


def test_scanner_result_has_topic():
    scanner = ReportScanner()
    with patch("modules.climate_analysis.report_scanner._fetch_openalex") as mock_fetch:
        mock_fetch.return_value = [_make_paper()]
        result = scanner.scan("Arktische Erwärmung")
    assert result.topic == "Arktische Erwärmung"


def test_scanner_result_has_papers():
    scanner = ReportScanner()
    with patch("modules.climate_analysis.report_scanner._fetch_openalex") as mock_fetch:
        mock_fetch.return_value = [_make_paper(), _make_paper(title="Paper 2")]
        result = scanner.scan("test")
    assert len(result.papers) == 2


# ── API Router ─────────────────────────────────────────────────────────────────

def test_scan_topics_endpoint():
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    from services.api.routers.admin import router

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    resp = client.get("/api/v1/admin/scan-topics")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "topics" in data
    assert len(data["topics"]) > 0


def test_scan_reports_endpoint():
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    from services.api.routers import admin

    app = FastAPI()
    app.include_router(admin.router)
    client = TestClient(app)

    with patch.object(admin._scanner, "scan") as mock_scan:
        mock_scan.return_value = ScanResult(
            topic="Arctic amplification",
            summary="Test summary [Artikel 1].",
            papers=[_make_paper()],
            used_llm=False,
        )
        resp = client.post("/api/v1/admin/scan-reports", json={
            "topic": "Arctic amplification",
            "max_papers": 3,
        })

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["topic"] == "Arctic amplification"
    assert "summary" in data
    assert "papers" in data
    assert data["used_llm"] is False


def test_scan_reports_empty_topic_rejected():
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    from services.api.routers.admin import router

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    resp = client.post("/api/v1/admin/scan-reports", json={"topic": "   "})
    assert resp.status_code == 400
