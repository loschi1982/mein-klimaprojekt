"""
Router: AI Explanation (Claude API)
Team-Branch: team/api  (Integration – Logik von team/ai-explanation)
"""
import os
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from models.schemas import ApiResponse, ExplainRequest, ExplainResponse, Meta

router = APIRouter(prefix="/api/v1", tags=["AI Explanation"])


def meta() -> Meta:
    return Meta(timestamp=datetime.now(timezone.utc).isoformat())


@router.post("/explain", response_model=ApiResponse, summary="Datenpunkt erklären (Claude)")
def explain(request: ExplainRequest):
    """Erklärt einen Klimadatenpunkt in verständlicher Sprache via Claude API."""
    try:
        import anthropic
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail={"code": "PROCESSING_ERROR", "message": "anthropic-Paket nicht installiert."},
        )

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail={"code": "AUTH_REQUIRED", "message": "ANTHROPIC_API_KEY nicht gesetzt."},
        )

    client = anthropic.Anthropic(api_key=api_key)
    prompt = (
        "Du bist ein Klimawissenschaftler, der Daten einfach und verständlich erklärt.\n"
        f"Datenpunkt: {request.data_point}\n"
        f"Frage: {request.question}\n"
        "Erkläre in 2-3 Sätzen, verständlich für Anfänger ohne Fachkenntnisse."
    )
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )
    return ApiResponse(
        data=ExplainResponse(explanation=message.content[0].text),
        meta=meta(),
    )
