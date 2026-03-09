"""
ReportScanner: Durchsucht wissenschaftliche Literatur via OpenAlex API
und generiert streng quellenbasierte KI-Berichte.
"""
from __future__ import annotations

import os
import json
import urllib.request
import urllib.parse
from dataclasses import dataclass, field
from datetime import datetime, timezone


# ── Datenmodelle ──────────────────────────────────────────────────────────────

@dataclass
class ScientificPaper:
    title: str
    authors: list[str]
    year: int | None
    abstract: str
    url: str
    doi: str | None = None


@dataclass
class ScanResult:
    topic: str
    summary: str
    papers: list[ScientificPaper]
    used_llm: bool = False
    scanned_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


# ── Vordefinierte Suchthemen ──────────────────────────────────────────────────

PRESET_TOPICS = [
    {
        "label": "Arktische Verstärkung (Arctic Amplification)",
        "query": "Arctic amplification Northern Hemisphere warming faster polar",
    },
    {
        "label": "Nordhalbkugel – Land-Ozean-Erwärmungsunterschied",
        "query": "Northern Hemisphere land ocean warming asymmetry temperature anomaly",
    },
    {
        "label": "Polarer Jet-Stream und Klimawandel",
        "query": "polar vortex jet stream climate change Northern Hemisphere",
    },
    {
        "label": "Hemisphärische Temperaturasymmetrie",
        "query": "hemispheric warming asymmetry Northern Southern temperature difference",
    },
    {
        "label": "Permafrost und Rückkopplungseffekte",
        "query": "permafrost thaw Arctic feedback climate warming Northern Hemisphere",
    },
]


# ── OpenAlex Suche ─────────────────────────────────────────────────────────────

OPENALEX_BASE = "https://api.openalex.org/works"
_CONTACT = "klimadashboard@research.example.com"  # Polite pool


def _reconstruct_abstract(inverted_index: dict | None) -> str:
    """Rekonstruiert Abstract aus dem OpenAlex Inverted-Index-Format."""
    if not inverted_index:
        return ""
    positions: dict[int, str] = {}
    for word, pos_list in inverted_index.items():
        for pos in pos_list:
            positions[pos] = word
    return " ".join(positions[i] for i in sorted(positions.keys()))


def _fetch_openalex(query: str, max_papers: int) -> list[ScientificPaper]:
    params = {
        "search": query,
        "filter": "type:article,has_abstract:true",
        "sort": "cited_by_count:desc",
        "per_page": min(max_papers, 10),
        "select": (
            "title,authorships,publication_year,doi,"
            "abstract_inverted_index,primary_location,open_access"
        ),
    }
    url = f"{OPENALEX_BASE}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": f"KlimaDashboard/1.0 (mailto:{_CONTACT})"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read())

    papers: list[ScientificPaper] = []
    for work in data.get("results", []):
        title = (work.get("title") or "").strip()
        if not title:
            continue

        authors = [
            a["author"]["display_name"]
            for a in work.get("authorships", [])
            if a.get("author", {}).get("display_name")
        ][:6]

        year = work.get("publication_year")
        abstract = _reconstruct_abstract(work.get("abstract_inverted_index"))
        if not abstract:
            continue  # Abstracts sind Pflicht

        doi_raw = work.get("doi") or ""
        doi = doi_raw if doi_raw.startswith("http") else (
            f"https://doi.org/{doi_raw}" if doi_raw else None
        )
        loc = work.get("primary_location") or {}
        landing = loc.get("landing_page_url") or ""
        paper_url = doi or landing or ""

        papers.append(ScientificPaper(
            title=title,
            authors=authors,
            year=year,
            abstract=abstract,
            url=paper_url,
            doi=doi,
        ))

    return papers[:max_papers]


# ── Zusammenfassung ────────────────────────────────────────────────────────────

def _rule_summary(papers: list[ScientificPaper], topic: str) -> str:
    """Regelbasierte Zusammenfassung ohne LLM."""
    lines = [
        f"## Wissenschaftlicher Überblick: {topic}\n",
        f"Basierend auf {len(papers)} wissenschaftlichen Fachartikeln "
        f"(Quelle: OpenAlex / zitiert nach Häufigkeit sortiert):\n",
    ]
    for i, p in enumerate(papers, 1):
        authors_str = ", ".join(p.authors[:3])
        if len(p.authors) > 3:
            authors_str += " et al."
        year_str = str(p.year) if p.year else "k.J."
        lines.append(f"### [Artikel {i}] {p.title} ({year_str})")
        lines.append(f"**Autoren:** {authors_str or 'unbekannt'}")
        if p.url:
            lines.append(f"**Quelle:** {p.url}")
        snippet = p.abstract[:500] + "…" if len(p.abstract) > 500 else p.abstract
        lines.append(f"\n{snippet}\n")
    return "\n".join(lines)


def _llm_summary(papers: list[ScientificPaper], topic: str, api_key: str) -> str:
    """Streng quellenbasierter KI-Bericht via Claude."""
    import anthropic

    articles_block = ""
    for i, p in enumerate(papers, 1):
        authors_str = ", ".join(p.authors) if p.authors else "Unbekannt"
        year_str = str(p.year) if p.year else "k.J."
        articles_block += (
            f"\n--- Artikel {i} ---\n"
            f"Titel: {p.title}\n"
            f"Jahr: {year_str}\n"
            f"Hauptautoren: {authors_str}\n"
            f"Link: {p.url or 'kein Link verfügbar'}\n"
            f"Kurzfassung (Abstract):\n{p.abstract[:2000]}\n"
        )

    system = (
        "Du bist ein Wissenschaftsjournalist. Du schreibst ausschließlich auf Deutsch. "
        "Du verwendest NUR Informationen aus den dir bereitgestellten Abstracts – "
        "keine eigenen Kenntnisse, keine Ergänzungen, keine Vermutungen. "
        "Jede Aussage muss mit [Artikel N] belegt sein."
    )

    user = (
        f"Thema: {topic}\n\n"
        f"Hier sind {len(papers)} wissenschaftliche Fachartikel:\n"
        f"{articles_block}\n\n"
        "Schreibe einen verständlichen Bericht in einfacher Sprache (ca. 400–550 Wörter).\n\n"
        "STRENGE REGELN:\n"
        "1. Nur Informationen aus den obigen Abstracts – keine eigenen Ergänzungen.\n"
        "2. Jede inhaltliche Aussage mit [Artikel N] im Text belegen.\n"
        "3. Fachbegriffe sofort in Klammern erklären.\n"
        "4. Schreibe klar und verständlich für ein breites Publikum.\n"
        "5. Gliedere in: Einleitung → Haupterkenntnisse → Fazit → Quellenverzeichnis.\n\n"
        "Quellenverzeichnis am Ende (Markdown-Format):\n"
        "**Quellen**\n"
        "1. Titel (Jahr) – Autoren – [DOI/Link](URL)\n"
        "...\n\n"
        "Beginne direkt mit dem Bericht ohne Präambel."
    )

    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1800,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return msg.content[0].text


# ── Haupt-Klasse ──────────────────────────────────────────────────────────────

class ReportScanner:
    def __init__(self) -> None:
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")

    def scan(self, topic: str, max_papers: int = 5) -> ScanResult:
        """Sucht Fachartikel und generiert einen quellenbasierten Bericht."""
        papers = _fetch_openalex(topic, max_papers)

        if not papers:
            return ScanResult(
                topic=topic,
                summary=(
                    "Es konnten keine wissenschaftlichen Artikel mit Abstract "
                    f'für das Thema "{topic}" gefunden werden. '
                    "Bitte einen anderen Suchbegriff (vorzugsweise Englisch) verwenden."
                ),
                papers=[],
                used_llm=False,
            )

        used_llm = False
        if self.api_key:
            try:
                summary = _llm_summary(papers, topic, self.api_key)
                used_llm = True
            except Exception:
                summary = _rule_summary(papers, topic)
        else:
            summary = _rule_summary(papers, topic)

        return ScanResult(
            topic=topic,
            summary=summary,
            papers=papers,
            used_llm=used_llm,
        )
