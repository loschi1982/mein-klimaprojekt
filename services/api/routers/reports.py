"""
Router: Öffentliche Berichte
Gibt nur veröffentlichte Berichte zurück (kein Admin-Auth erforderlich).
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException

from models.schemas import ApiResponse, Meta

router = APIRouter(prefix="/api/v1/reports", tags=["Berichte"])

REPORTS_DIR = Path(__file__).parent.parent.parent.parent / "data" / "reports"


def _meta() -> Meta:
    return Meta(timestamp=datetime.now(timezone.utc).isoformat())


@router.get("", response_model=ApiResponse, summary="Veröffentlichte Berichte auflisten")
def list_published_reports():
    """Listet alle veröffentlichten Berichte (Metadaten, ohne Inhalt)."""
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    reports = []
    for path in sorted(REPORTS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            data = json.loads(path.read_text())
            if not data.get("published", False):
                continue
            reports.append({
                "id": data["id"],
                "title": data["title"],
                "tags": data.get("tags", []),
                "created_at": data["created_at"],
                "updated_at": data.get("updated_at", data["created_at"]),
            })
        except Exception:
            continue
    return ApiResponse(data={"count": len(reports), "reports": reports}, meta=_meta())


@router.get("/{report_id}", response_model=ApiResponse, summary="Einzelnen veröffentlichten Bericht laden")
def get_published_report(report_id: str):
    """Gibt einen veröffentlichten Bericht mit vollem Inhalt zurück."""
    path = REPORTS_DIR / f"{report_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Bericht nicht gefunden"})
    data = json.loads(path.read_text())
    if not data.get("published", False):
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Bericht nicht veröffentlicht"})
    return ApiResponse(data=data, meta=_meta())
