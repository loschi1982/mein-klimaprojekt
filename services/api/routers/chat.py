"""
Router: KI-Chat
POST /api/v1/chat – kontextbewusste Fragen zu Klimadaten
"""
from datetime import datetime, timezone
from fastapi import APIRouter
from pydantic import BaseModel

from models.schemas import ApiResponse, Meta
from modules.climate_analysis.chat import ClimateChat, ChatContext

router = APIRouter(prefix="/api/v1", tags=["Chat"])
_chat = ClimateChat()


def _meta() -> Meta:
    return Meta(timestamp=datetime.now(timezone.utc).isoformat())


class ChatMessageItem(BaseModel):
    role: str   # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    context: dict = {}
    history: list[ChatMessageItem] = []
    use_llm: bool = False


@router.post("/chat", response_model=ApiResponse, summary="KI-Klimadaten-Chat")
def chat(req: ChatRequest):
    """
    Beantwortet Fragen zu Klimadaten im Kontext des aktuell angezeigten Datensatzes.
    Regelbasiert oder optional via Claude (use_llm=true + ANTHROPIC_API_KEY).
    """
    ctx_data = req.context
    ctx = ChatContext(
        source_id=ctx_data.get("source_id", ""),
        current_value=ctx_data.get("current_value"),
        unit=ctx_data.get("unit", ""),
        from_year=int(ctx_data.get("from_year", 1960)),
        to_year=int(ctx_data.get("to_year", 2024)),
        view_label=ctx_data.get("view_label", ""),
    )
    history = [{"role": m.role, "content": m.content} for m in req.history]
    response = _chat.respond(req.message, ctx, history=history, use_llm=req.use_llm)

    return ApiResponse(
        data={
            "answer": response.answer,
            "used_llm": response.used_llm,
            "suggestions": response.suggestions,
        },
        meta=_meta(),
    )
