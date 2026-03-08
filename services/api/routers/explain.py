"""
Router: AI Explanation
Team-Branch: team/ai-explanation
"""
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from models.schemas import ApiResponse, ExplainRequest, ExplainResponse, Meta
from modules.ai_explanation.explainer import ExplanationAgent
from modules.ai_explanation.article_ideas import ArticleIdeaAgent

router = APIRouter(prefix="/api/v1", tags=["AI Explanation"])


def meta() -> Meta:
    return Meta(timestamp=datetime.now(timezone.utc).isoformat())


class ArticleIdeasRequest(BaseModel):
    analysis_summary: dict
    count: int = 5


@router.get("/explain/audiences", response_model=ApiResponse, summary="Verfügbare Zielgruppen")
def list_audiences():
    """Gibt die verfügbaren Zielgruppen für Erklärungen zurück."""
    return ApiResponse(
        data={"audiences": list(ExplanationAgent.AUDIENCES.keys())},
        meta=meta(),
    )


@router.post("/explain", response_model=ApiResponse, summary="Datenpunkt erklären")
def explain(
    request: ExplainRequest,
    audience: str = Query("beginner", description="Zielgruppe: beginner | expert"),
):
    """
    Erklärt einen Klimadatenpunkt in verständlicher Sprache.
    Nutzt Claude API wenn ANTHROPIC_API_KEY gesetzt, sonst regelbasiert.
    """
    agent = ExplanationAgent()
    result = agent.explain(request.data_point, request.question, audience)
    return ApiResponse(
        data=ExplainResponse(
            explanation=result.explanation,
            confidence=result.confidence,
            sources=result.sources,
        ),
        meta=meta(),
    )


@router.post("/explain/article-ideas", response_model=ApiResponse, summary="Artikelideen generieren")
def article_ideas(request: ArticleIdeasRequest):
    """
    Generiert Artikelideen aus einem Analyse-Zusammenfassungs-Dict.
    Erwartet: slope, mean, max_value, anomaly_count, min_date, max_date
    """
    if request.count < 1 or request.count > 10:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_PARAMS", "message": "count muss zwischen 1 und 10 liegen"},
        )
    agent = ArticleIdeaAgent()
    ideas = agent.generate(request.analysis_summary, request.count)
    return ApiResponse(
        data=[
            {
                "title": idea.title,
                "hook": idea.hook,
                "key_points": idea.key_points,
                "target_audience": idea.target_audience,
            }
            for idea in ideas
        ],
        meta=meta(),
    )
