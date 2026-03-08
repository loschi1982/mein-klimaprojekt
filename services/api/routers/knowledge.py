"""
Router: Knowledge Base
Team-Branch: team/knowledge-base
"""
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query

from models.schemas import ApiResponse, Meta
from modules.knowledge_base.store import KnowledgeStore

router = APIRouter(prefix="/api/v1/knowledge", tags=["Knowledge Base"])
_store: KnowledgeStore | None = None


def get_store() -> KnowledgeStore:
    global _store
    if _store is None:
        _store = KnowledgeStore()
    return _store


def meta() -> Meta:
    return Meta(timestamp=datetime.now(timezone.utc).isoformat())


@router.get("/", response_model=ApiResponse, summary="Alle Topics auflisten")
def list_topics():
    """Gibt alle verfügbaren Wissens-Topics zurück."""
    store = get_store()
    return ApiResponse(data={"topics": store.list_topics(), "count": len(store.list_topics())}, meta=meta())


@router.get("/search", response_model=ApiResponse, summary="Wissen durchsuchen")
def search_knowledge(q: str = Query(..., description="Suchbegriff")):
    """Durchsucht Titel, Inhalt und Tags aller Einträge."""
    store = get_store()
    results = store.search(q)
    return ApiResponse(
        data={"query": q, "count": len(results), "results": [
            {"topic": e.topic, "title": e.title, "tags": e.tags}
            for e in results
        ]},
        meta=meta(),
    )


@router.get("/{topic}", response_model=ApiResponse, summary="Wissenseintrag abrufen")
def get_knowledge(topic: str):
    """Gibt den vollständigen Wissenseintrag für ein Topic zurück."""
    store = get_store()
    entry = store.get(topic)
    if entry is None:
        raise HTTPException(
            status_code=404,
            detail={"code": "DATA_NOT_FOUND", "message": f"Topic '{topic}' nicht gefunden."},
        )
    from dataclasses import asdict
    return ApiResponse(data=asdict(entry), meta=meta())
