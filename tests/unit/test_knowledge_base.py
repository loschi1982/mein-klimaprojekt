"""Unit Tests für das Knowledge Base Module"""
import json
import tempfile
from dataclasses import asdict
from pathlib import Path

import pytest

from modules.knowledge_base.store import KnowledgeEntry, KnowledgeStore
from modules.knowledge_base.builder import build_from_analysis, enrich_store


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_store(entries: dict | None = None) -> tuple[KnowledgeStore, Path]:
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    payload = {"entries": entries or {}}
    Path(tmp.name).write_text(json.dumps(payload), encoding="utf-8")
    return KnowledgeStore(Path(tmp.name)), Path(tmp.name)


def sample_entry(topic: str = "test_topic") -> KnowledgeEntry:
    return KnowledgeEntry(
        id=topic, topic=topic,
        title="Test Titel",
        content="Test Inhalt über CO₂ und Klima.",
        facts=["Fakt 1", "Fakt 2"],
        sources=["Quelle A"],
        tags=["test", "co2"],
    )


def make_analysis_result():
    from modules.climate_analysis.analyzer import AnalysisResult, SeriesStats, TrendResult
    stats = SeriesStats(
        count=816, mean=390.5, median=389.0, std=15.2,
        min=313.0, max=430.0,
        min_date="1958-03-01", max_date="2026-01-01", unit="ppm",
    )
    trend = TrendResult(
        slope=1.85, intercept=310.0, r_squared=0.98,
        p_value=None, unit="ppm",
        interpretation="Moderater Anstieg: +1.85 ppm/Jahr",
    )
    return AnalysisResult(
        source="esrl_mauna_loa", unit="ppm",
        stats=stats, trend=trend, anomalies=[],
    )


# ── KnowledgeStore: _load ─────────────────────────────────────────────────────

def test_store_loads_empty_file():
    store, _ = make_store({})
    assert store.list_topics() == []


def test_store_loads_entries():
    entries = {
        "topic_a": asdict(sample_entry("topic_a")),
        "topic_b": asdict(sample_entry("topic_b")),
    }
    store, _ = make_store(entries)
    assert len(store.list_topics()) == 2


def test_store_missing_file():
    store = KnowledgeStore(Path("/tmp/nonexistent_xyz_kb.json"))
    assert store.list_topics() == []


# ── KnowledgeStore: get ───────────────────────────────────────────────────────

def test_get_existing_entry():
    entries = {"co2": asdict(sample_entry("co2"))}
    store, _ = make_store(entries)
    entry = store.get("co2")
    assert entry is not None
    assert entry.topic == "co2"
    assert entry.title == "Test Titel"


def test_get_unknown_topic_returns_none():
    store, _ = make_store({})
    assert store.get("nicht_vorhanden") is None


def test_get_returns_knowledge_entry_type():
    entries = {"co2": asdict(sample_entry("co2"))}
    store, _ = make_store(entries)
    entry = store.get("co2")
    assert isinstance(entry, KnowledgeEntry)


# ── KnowledgeStore: list_topics ───────────────────────────────────────────────

def test_list_topics_sorted():
    entries = {k: asdict(sample_entry(k)) for k in ["zebra", "apfel", "mango"]}
    store, _ = make_store(entries)
    topics = store.list_topics()
    assert topics == sorted(topics)


def test_list_topics_count():
    entries = {k: asdict(sample_entry(k)) for k in ["a", "b", "c"]}
    store, _ = make_store(entries)
    assert len(store.list_topics()) == 3


# ── KnowledgeStore: search ────────────────────────────────────────────────────

def test_search_finds_by_title():
    entries = {"co2_topic": asdict(sample_entry("co2_topic"))}
    store, _ = make_store(entries)
    results = store.search("Test Titel")
    assert len(results) == 1


def test_search_finds_by_tag():
    entries = {"co2_topic": asdict(sample_entry("co2_topic"))}
    store, _ = make_store(entries)
    results = store.search("co2")
    assert len(results) == 1


def test_search_finds_by_content():
    entries = {"co2_topic": asdict(sample_entry("co2_topic"))}
    store, _ = make_store(entries)
    results = store.search("Klima")
    assert len(results) == 1


def test_search_case_insensitive():
    entries = {"co2_topic": asdict(sample_entry("co2_topic"))}
    store, _ = make_store(entries)
    assert len(store.search("CO2")) == len(store.search("co2"))


def test_search_no_match():
    entries = {"co2_topic": asdict(sample_entry("co2_topic"))}
    store, _ = make_store(entries)
    assert store.search("xyznotfound123") == []


def test_search_multiple_results():
    entries = {k: asdict(sample_entry(k)) for k in ["a", "b", "c"]}
    store, _ = make_store(entries)
    # Alle haben "Test" im Titel
    results = store.search("Test")
    assert len(results) == 3


# ── KnowledgeStore: upsert ────────────────────────────────────────────────────

def test_upsert_adds_new_entry():
    store, path = make_store({})
    store.upsert(sample_entry("new_topic"))
    assert store.get("new_topic") is not None


def test_upsert_updates_existing():
    entries = {"co2": asdict(sample_entry("co2"))}
    store, _ = make_store(entries)
    updated = KnowledgeEntry(
        id="co2", topic="co2", title="Neuer Titel",
        content="Neuer Inhalt", facts=[], sources=[], tags=[],
    )
    store.upsert(updated)
    assert store.get("co2").title == "Neuer Titel"


def test_upsert_persists_to_disk():
    store, path = make_store({})
    store.upsert(sample_entry("persistent"))
    store2 = KnowledgeStore(path)
    assert store2.get("persistent") is not None


def test_upsert_sets_updated_at():
    store, _ = make_store({})
    entry = sample_entry("ts_topic")
    entry.updated_at = ""
    store.upsert(entry)
    saved = store.get("ts_topic")
    assert saved.updated_at != ""


# ── Vordefinierte Einträge in knowledge_base.json ─────────────────────────────

def test_default_knowledge_base_has_entries():
    store = KnowledgeStore()
    assert len(store.list_topics()) >= 4


def test_default_entry_co2_greenhouse():
    store = KnowledgeStore()
    entry = store.get("co2_greenhouse_effect")
    assert entry is not None
    assert "CO₂" in entry.title


def test_default_entry_mauna_loa():
    store = KnowledgeStore()
    entry = store.get("mauna_loa_observatory")
    assert entry is not None
    assert len(entry.facts) > 0


def test_default_entry_rcp_scenarios():
    store = KnowledgeStore()
    entry = store.get("rcp_scenarios")
    assert entry is not None
    assert any("RCP" in f for f in entry.facts)


def test_default_entry_350ppm():
    store = KnowledgeStore()
    entry = store.get("co2_350ppm_safety")
    assert entry is not None
    assert len(entry.sources) > 0


# ── Builder ───────────────────────────────────────────────────────────────────

def test_build_from_analysis_returns_entry():
    result = make_analysis_result()
    entry = build_from_analysis(result)
    assert isinstance(entry, KnowledgeEntry)


def test_build_from_analysis_has_facts():
    result = make_analysis_result()
    entry = build_from_analysis(result)
    assert len(entry.facts) >= 4


def test_build_from_analysis_contains_trend():
    result = make_analysis_result()
    entry = build_from_analysis(result)
    assert any("Trend" in f for f in entry.facts)


def test_build_from_analysis_source_in_tags():
    result = make_analysis_result()
    entry = build_from_analysis(result)
    assert "esrl_mauna_loa" in entry.tags


def test_enrich_store_adds_entry():
    store, _ = make_store({})
    result = make_analysis_result()
    entry = enrich_store(store, result)
    assert store.get(entry.topic) is not None


def test_enrich_store_returns_entry():
    store, _ = make_store({})
    result = make_analysis_result()
    entry = enrich_store(store, result)
    assert isinstance(entry, KnowledgeEntry)
