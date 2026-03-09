"""
Router: Admin – Berichte (CRUD)
Speichert KI-generierte Berichte als JSON in data/reports/.
"""
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from models.schemas import ApiResponse, Meta
from modules.climate_analysis.report_scanner import ReportScanner, PRESET_TOPICS

_scanner = ReportScanner()

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])

REPORTS_DIR = Path(__file__).parent.parent.parent.parent / "data" / "reports"


def _meta() -> Meta:
    return Meta(timestamp=datetime.now(timezone.utc).isoformat())


def _load_report(report_id: str) -> dict:
    path = REPORTS_DIR / f"{report_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": f"Bericht '{report_id}' nicht gefunden"})
    return json.loads(path.read_text())


# ── Schemas ───────────────────────────────────────────────────────────────────

class ScanRequest(BaseModel):
    topic: str
    max_papers: int = 5


class ReportSaveRequest(BaseModel):
    title: str
    content: str           # HTML aus WYSIWYG-Editor
    source_id: str = "esrl_mauna_loa"
    tags: list[str] = []


# ── Endpunkte ─────────────────────────────────────────────────────────────────

@router.get("/scan-topics", response_model=ApiResponse, summary="Vordefinierte Suchthemen")
def get_scan_topics():
    """Gibt die vordefinierten Literatur-Suchthemen zurück."""
    return ApiResponse(data={"topics": PRESET_TOPICS}, meta=_meta())


@router.post("/scan-reports", response_model=ApiResponse, summary="Wissenschaftliche Literatur scannen")
def scan_reports(req: ScanRequest):
    """
    Sucht via OpenAlex nach Fachartikeln und erstellt einen quellenbasierten KI-Bericht.
    Verwendet ausschließlich Informationen aus den gefundenen Abstracts.
    """
    if not req.topic.strip():
        raise HTTPException(status_code=400, detail={"code": "INVALID_PARAMS", "message": "Thema darf nicht leer sein"})
    result = _scanner.scan(req.topic.strip(), max(1, min(req.max_papers, 10)))
    return ApiResponse(
        data={
            "topic": result.topic,
            "summary": result.summary,
            "used_llm": result.used_llm,
            "scanned_at": result.scanned_at,
            "papers": [
                {
                    "title": p.title,
                    "authors": p.authors,
                    "year": p.year,
                    "url": p.url,
                    "doi": p.doi,
                    "abstract_snippet": p.abstract[:400] + "…" if len(p.abstract) > 400 else p.abstract,
                }
                for p in result.papers
            ],
        },
        meta=_meta(),
    )


@router.get("/reports", response_model=ApiResponse, summary="Alle Berichte auflisten")
def list_reports():
    """Listet alle gespeicherten Berichte (Metadaten, ohne Inhalt)."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    reports = []
    for path in sorted(REPORTS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(path.read_text())
            reports.append({
                "id": data["id"],
                "title": data["title"],
                "source_id": data.get("source_id", ""),
                "tags": data.get("tags", []),
                "created_at": data["created_at"],
                "updated_at": data.get("updated_at", data["created_at"]),
            })
        except Exception:
            continue
    return ApiResponse(data={"count": len(reports), "reports": reports}, meta=_meta())


@router.post("/reports", response_model=ApiResponse, summary="Bericht speichern")
def save_report(req: ReportSaveRequest):
    """Speichert einen neuen Bericht (HTML-Inhalt aus WYSIWYG-Editor)."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_id = str(uuid.uuid4())[:8]
    now = datetime.now(timezone.utc).isoformat()
    report = {
        "id": report_id,
        "title": req.title,
        "content": req.content,
        "source_id": req.source_id,
        "tags": req.tags,
        "created_at": now,
        "updated_at": now,
    }
    (REPORTS_DIR / f"{report_id}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
    return ApiResponse(data={"id": report_id, "created_at": now}, meta=_meta())


@router.get("/reports/{report_id}", response_model=ApiResponse, summary="Einzelnen Bericht laden")
def get_report(report_id: str):
    """Gibt einen einzelnen Bericht mit vollem Inhalt zurück."""
    report = _load_report(report_id)
    return ApiResponse(data=report, meta=_meta())


@router.put("/reports/{report_id}", response_model=ApiResponse, summary="Bericht aktualisieren")
def update_report(report_id: str, req: ReportSaveRequest):
    """Aktualisiert Titel, Inhalt und Tags eines bestehenden Berichts."""
    report = _load_report(report_id)
    report["title"] = req.title
    report["content"] = req.content
    report["source_id"] = req.source_id
    report["tags"] = req.tags
    report["updated_at"] = datetime.now(timezone.utc).isoformat()
    (REPORTS_DIR / f"{report_id}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
    return ApiResponse(data={"id": report_id, "updated_at": report["updated_at"]}, meta=_meta())


@router.delete("/reports/{report_id}", response_model=ApiResponse, summary="Bericht löschen")
def delete_report(report_id: str):
    """Löscht einen Bericht dauerhaft."""
    path = REPORTS_DIR / f"{report_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": f"Bericht '{report_id}' nicht gefunden"})
    path.unlink()
    return ApiResponse(data={"deleted": report_id}, meta=_meta())
