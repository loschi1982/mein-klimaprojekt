"""Unit Tests für ClimateChat Agent und /api/v1/chat Endpunkt"""
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "services" / "api"))

from modules.climate_analysis.chat import ClimateChat, ChatContext, ChatResponse, _rule_respond


# ── ChatContext ────────────────────────────────────────────────────────────────

def test_chat_context_defaults():
    ctx = ChatContext()
    assert ctx.source_id == ""
    assert ctx.current_value is None
    assert ctx.from_year == 1960
    assert ctx.to_year == 2024


def test_chat_context_custom():
    ctx = ChatContext(source_id="esrl_mauna_loa", current_value=421.5, unit="ppm")
    assert ctx.source_id == "esrl_mauna_loa"
    assert ctx.current_value == pytest.approx(421.5)
    assert ctx.unit == "ppm"


# ── Regelbasierte Antworten ────────────────────────────────────────────────────

def _ctx(source_id="esrl_mauna_loa", val=421.5):
    return ChatContext(source_id=source_id, current_value=val, unit="ppm")


def test_rule_respond_co2_current():
    answer = _rule_respond("Was ist der aktuelle CO₂-Wert?", _ctx())
    assert "421" in answer or "ppm" in answer.lower()


def test_rule_respond_co2_350():
    answer = _rule_respond("Was bedeutet die 350-ppm-Grenze?", _ctx())
    assert "350" in answer


def test_rule_respond_co2_400():
    answer = _rule_respond("Wann wurde 400 ppm überschritten?", _ctx())
    assert "400" in answer or "2013" in answer


def test_rule_respond_preindustrial():
    answer = _rule_respond("Was war der vorindustrielle CO₂-Wert?", _ctx())
    assert "280" in answer


def test_rule_respond_paris():
    answer = _rule_respond("Was ist das Paris-Ziel?", _ctx())
    assert "1,5" in answer or "1.5" in answer or "Paris" in answer


def test_rule_respond_treibhauseffekt():
    answer = _rule_respond("Erkläre den Treibhauseffekt", _ctx())
    assert "Treibhaus" in answer or "CO₂" in answer


def test_rule_respond_dashboard():
    answer = _rule_respond("Was zeigt dieses Dashboard?", _ctx())
    assert "Dashboard" in answer or "Klimadaten" in answer


def test_rule_respond_quellen():
    answer = _rule_respond("Woher stammen die Daten?", _ctx())
    assert "NOAA" in answer or "NASA" in answer or "Quelle" in answer


def test_rule_respond_ch4():
    ctx = ChatContext(source_id="esrl_ch4", current_value=1923.5, unit="ppb")
    answer = _rule_respond("Was ist Methan?", ctx)
    assert "Methan" in answer or "CH₄" in answer


def test_rule_respond_temp_anomalie():
    ctx = ChatContext(source_id="nasa_giss_global", current_value=1.2, unit="°C")
    answer = _rule_respond("Was bedeutet Temperaturanomalie?", ctx)
    assert "Anomalie" in answer or "Referenz" in answer


def test_rule_respond_sea_level():
    ctx = ChatContext(source_id="csiro_sea_level", current_value=68.0, unit="mm")
    answer = _rule_respond("Wie stark steigt der Meeresspiegel pro Jahr?", ctx)
    assert "mm" in answer or "Meeresspiegel" in answer


def test_rule_respond_arctic():
    answer = _rule_respond("Welche Zone erwärmt sich am stärksten?", _ctx("nasa_giss_global", 1.2))
    assert "Arktis" in answer or "64N" in answer or "Amplification" in answer


def test_rule_respond_keeling():
    answer = _rule_respond("Was ist die Keeling-Kurve?", _ctx())
    assert "Keeling" in answer or "Mauna Loa" in answer


def test_rule_respond_zeitraum():
    ctx = ChatContext(source_id="esrl_mauna_loa", from_year=1960, to_year=2020)
    answer = _rule_respond("Welchen Zeitraum zeigt der Chart?", ctx)
    assert "1960" in answer or "2020" in answer or "Zeitraum" in answer


def test_rule_respond_fallback():
    answer = _rule_respond("xyzabc123 unbekannte frage", _ctx())
    assert len(answer) > 20  # Fallback gibt immer etwas zurück


def test_rule_respond_returns_string():
    ctx = ChatContext()
    answer = _rule_respond("Hallo", ctx)
    assert isinstance(answer, str)
    assert len(answer) > 0


# ── ClimateChat ────────────────────────────────────────────────────────────────

def test_climatechat_respond_returns_response():
    chat = ClimateChat()
    ctx = ChatContext(source_id="esrl_mauna_loa", current_value=421.5)
    result = chat.respond("Was ist CO₂?", ctx)
    assert isinstance(result, ChatResponse)
    assert len(result.answer) > 0


def test_climatechat_no_llm_without_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    chat = ClimateChat()
    ctx = ChatContext(source_id="esrl_mauna_loa")
    result = chat.respond("Hallo", ctx)
    assert result.used_llm is False


def test_climatechat_suggestions_returned():
    chat = ClimateChat()
    ctx = ChatContext(source_id="esrl_mauna_loa", current_value=421.0)
    result = chat.respond("Was zeigt dieser Chart?", ctx)
    assert isinstance(result.suggestions, list)
    assert len(result.suggestions) > 0


def test_climatechat_suggestions_for_co2():
    chat = ClimateChat()
    ctx = ChatContext(source_id="esrl_mauna_loa")
    result = chat.respond("Hallo", ctx)
    assert any("CO₂" in s or "ppm" in s.lower() or "350" in s for s in result.suggestions)


def test_climatechat_suggestions_for_temp():
    chat = ClimateChat()
    ctx = ChatContext(source_id="nasa_giss_global")
    result = chat.respond("Hallo", ctx)
    assert any("Paris" in s or "Temperatur" in s or "Zone" in s for s in result.suggestions)


def test_climatechat_suggestions_for_sea():
    chat = ClimateChat()
    ctx = ChatContext(source_id="csiro_sea_level")
    result = chat.respond("Hallo", ctx)
    assert any("Meeresspiegel" in s or "Jahr" in s for s in result.suggestions)


# ── Chat Router ────────────────────────────────────────────────────────────────

def test_chat_router_returns_200():
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    from services.api.routers.chat import router

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    resp = client.post("/api/v1/chat", json={
        "message": "Was ist CO₂?",
        "context": {"source_id": "esrl_mauna_loa", "current_value": 421.5},
        "history": [],
    })
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "answer" in data
    assert "suggestions" in data
    assert "used_llm" in data


def test_chat_router_answer_nonempty():
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    from services.api.routers.chat import router

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    resp = client.post("/api/v1/chat", json={
        "message": "Paris-Ziel erklären",
        "context": {},
    })
    assert len(resp.json()["data"]["answer"]) > 20


def test_chat_router_with_history():
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    from services.api.routers.chat import router

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    resp = client.post("/api/v1/chat", json={
        "message": "Und was ist Methan?",
        "context": {"source_id": "esrl_ch4"},
        "history": [
            {"role": "user", "content": "Was ist CO₂?"},
            {"role": "assistant", "content": "CO₂ ist ein Treibhausgas."},
        ],
    })
    assert resp.status_code == 200
