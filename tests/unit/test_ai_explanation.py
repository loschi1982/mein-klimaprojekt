"""Unit Tests für das AI Explanation Module"""
import os
import pytest

from modules.ai_explanation.explainer import ExplanationAgent, ExplanationResult
from modules.ai_explanation.article_ideas import ArticleIdeaAgent, ArticleIdea


# ── Fixtures ──────────────────────────────────────────────────────────────────

CO2_DATA_POINT = {"type": "co2", "value": 421.5, "date": "2024-03"}
GENERIC_DATA_POINT = {"type": "temperature", "value": 1.2, "unit": "°C", "date": "2023"}

SAMPLE_SUMMARY = {
    "slope": 2.1,
    "mean": 390.5,
    "max_value": 428.6,
    "anomaly_count": 3,
    "min_date": "1958-03-01",
    "max_date": "2026-01-01",
}


# ── ExplanationAgent ohne API-Key ─────────────────────────────────────────────

def test_explain_returns_result(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    agent = ExplanationAgent()
    result = agent.explain(CO2_DATA_POINT, "Was bedeutet dieser Wert?")
    assert isinstance(result, ExplanationResult)


def test_explain_no_api_key_uses_rule(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    agent = ExplanationAgent()
    result = agent.explain(CO2_DATA_POINT, "Warum so hoch?")
    assert result.used_llm is False


def test_explain_co2_contains_ppm(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    agent = ExplanationAgent()
    result = agent.explain(CO2_DATA_POINT, "Was ist ppm?")
    assert "ppm" in result.explanation or "CO₂" in result.explanation


def test_explain_co2_high_value_context(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    agent = ExplanationAgent()
    result = agent.explain({"type": "co2", "value": 425.0}, "Einordnung?")
    assert "350" in result.explanation or "420" in result.explanation


def test_explain_co2_medium_value(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    agent = ExplanationAgent()
    result = agent.explain({"type": "co2", "value": 380.0}, "Einordnung?")
    assert "ppm" in result.explanation


def test_explain_co2_low_value(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    agent = ExplanationAgent()
    result = agent.explain({"type": "co2", "value": 340.0}, "Einordnung?")
    assert "350" in result.explanation


def test_explain_generic_type(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    agent = ExplanationAgent()
    result = agent.explain(GENERIC_DATA_POINT, "Was bedeutet das?")
    assert len(result.explanation) > 10


def test_explain_result_has_confidence(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    agent = ExplanationAgent()
    result = agent.explain(CO2_DATA_POINT, "Frage?")
    assert result.confidence in ("high", "medium", "low")


def test_explain_result_sources_co2(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    agent = ExplanationAgent()
    result = agent.explain(CO2_DATA_POINT, "Quelle?")
    assert len(result.sources) > 0
    assert any("Mauna" in s or "NOAA" in s for s in result.sources)


def test_explain_result_sources_generic(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    agent = ExplanationAgent()
    result = agent.explain(GENERIC_DATA_POINT, "Quelle?")
    assert isinstance(result.sources, list)


def test_explain_invalid_audience_fallback(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    agent = ExplanationAgent()
    result = agent.explain(CO2_DATA_POINT, "Test?", audience="invalid_audience")
    assert isinstance(result, ExplanationResult)


def test_explain_expert_audience(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    agent = ExplanationAgent()
    result = agent.explain(CO2_DATA_POINT, "Erklärung?", audience="expert")
    assert isinstance(result, ExplanationResult)


def test_audiences_dict_has_beginner_and_expert():
    assert "beginner" in ExplanationAgent.AUDIENCES
    assert "expert" in ExplanationAgent.AUDIENCES


# ── ArticleIdeaAgent ──────────────────────────────────────────────────────────

def test_article_ideas_returns_list(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    agent = ArticleIdeaAgent()
    ideas = agent.generate(SAMPLE_SUMMARY, count=3)
    assert isinstance(ideas, list)


def test_article_ideas_count(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    agent = ArticleIdeaAgent()
    ideas = agent.generate(SAMPLE_SUMMARY, count=3)
    assert len(ideas) == 3


def test_article_ideas_default_count(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    agent = ArticleIdeaAgent()
    ideas = agent.generate(SAMPLE_SUMMARY)
    assert len(ideas) == 5


def test_article_ideas_type(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    agent = ArticleIdeaAgent()
    ideas = agent.generate(SAMPLE_SUMMARY, count=2)
    assert all(isinstance(i, ArticleIdea) for i in ideas)


def test_article_idea_has_title(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    agent = ArticleIdeaAgent()
    ideas = agent.generate(SAMPLE_SUMMARY, count=1)
    assert all(len(i.title) > 0 for i in ideas)


def test_article_idea_has_hook(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    agent = ArticleIdeaAgent()
    ideas = agent.generate(SAMPLE_SUMMARY, count=2)
    assert all(len(i.hook) > 0 for i in ideas)


def test_article_idea_has_key_points(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    agent = ArticleIdeaAgent()
    ideas = agent.generate(SAMPLE_SUMMARY, count=2)
    assert all(len(i.key_points) > 0 for i in ideas)


def test_article_idea_has_target_audience(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    agent = ArticleIdeaAgent()
    ideas = agent.generate(SAMPLE_SUMMARY, count=2)
    assert all(len(i.target_audience) > 0 for i in ideas)


def test_article_ideas_uses_slope(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    agent = ArticleIdeaAgent()
    ideas = agent.generate({"slope": 3.5, "max_value": 430.0, "anomaly_count": 5,
                             "mean": 400.0, "min_date": "1958-01-01", "max_date": "2026-01-01"})
    titles = " ".join(i.title for i in ideas)
    assert "3.5" in titles or "430" in titles


def test_article_ideas_missing_keys_no_crash(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    agent = ArticleIdeaAgent()
    # Fehlende Keys → Defaults verwenden, kein Crash
    ideas = agent.generate({}, count=2)
    assert len(ideas) == 2
