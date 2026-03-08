"""
Knowledge Base Builder – erstellt Einträge aus Analyseergebnissen
Team-Branch: team/knowledge-base
"""
from datetime import datetime, timezone

from .store import KnowledgeEntry, KnowledgeStore


def build_from_analysis(result) -> KnowledgeEntry:
    """
    Erstellt automatisch einen KnowledgeEntry aus einem AnalysisResult.
    result: modules.climate_analysis.analyzer.AnalysisResult
    """
    topic = f"analysis_{result.source}_{result.stats.min_date[:4]}_{result.stats.max_date[:4]}"
    title = (
        f"CO₂-Analyse: {result.stats.min_date[:4]}–{result.stats.max_date[:4]}"
        f" ({result.stats.count} Messpunkte)"
    )
    content = (
        f"Automatisch generierter Analysebericht für {result.source}. "
        f"Zeitraum: {result.stats.min_date} bis {result.stats.max_date}. "
        f"Mittelwert: {result.stats.mean} {result.unit}. "
        f"Trend: {result.trend.slope:+.4f} {result.unit}/Jahr (R²={result.trend.r_squared}). "
        f"{result.trend.interpretation}"
    )
    facts = [
        f"Analysezeitraum: {result.stats.min_date} bis {result.stats.max_date}",
        f"Anzahl Messpunkte: {result.stats.count}",
        f"Mittelwert: {result.stats.mean} {result.unit}",
        f"Minimum: {result.stats.min} {result.unit} ({result.stats.min_date})",
        f"Maximum: {result.stats.max} {result.unit} ({result.stats.max_date})",
        f"Trend: {result.trend.slope:+.4f} {result.unit}/Jahr",
        f"R² (Linearität): {result.trend.r_squared}",
        f"Erkannte Anomalien: {len(result.anomalies)}",
    ]
    return KnowledgeEntry(
        id=topic,
        topic=topic,
        title=title,
        content=content,
        facts=facts,
        sources=[result.source],
        tags=["analyse", result.source, result.unit, "automatisch"],
        updated_at=datetime.now(timezone.utc).isoformat(),
    )


def enrich_store(store: KnowledgeStore, result) -> KnowledgeEntry:
    """Erstellt einen Eintrag aus result und speichert ihn im Store."""
    entry = build_from_analysis(result)
    store.upsert(entry)
    return entry
