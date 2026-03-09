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

def _extract_key_sentences(abstract: str, max_chars: int = 300) -> str:
    """Extrahiert erste und letzte Sätze eines Abstracts als Kernerkenntnis."""
    sentences = [s.strip() for s in abstract.replace("\n", " ").split(". ") if s.strip()]
    if not sentences:
        return abstract[:max_chars]
    if len(sentences) == 1:
        return sentences[0][:max_chars]
    first = sentences[0]
    last = sentences[-1]
    combined = f"{first}. {last}"
    if len(combined) <= max_chars:
        return combined
    return first[:max_chars] + "…"


def _rule_summary(papers: list[ScientificPaper], topic: str) -> str:
    """Strukturierte deutschsprachige Zusammenfassung ohne LLM."""
    n = len(papers)
    year_range = ""
    years = [p.year for p in papers if p.year]
    if years:
        year_range = f" (Publikationszeitraum: {min(years)}–{max(years)})"

    lines = [
        f"## Wissenschaftlicher Überblick: {topic}\n",
        f"### Einleitung\n",
        f"Die folgende Übersicht basiert auf {n} wissenschaftlichen Fachartikeln{year_range}, "
        f"die nach Zitationshäufigkeit ausgewählt wurden (Quelle: OpenAlex). "
        f"Die Artikel untersuchen verschiedene Aspekte des Themas und liefern wichtige Erkenntnisse "
        f"für das Verständnis klimatischer Zusammenhänge.\n",
        f"### Haupterkenntnisse\n",
    ]

    for i, p in enumerate(papers, 1):
        authors_str = ", ".join(p.authors[:3])
        if len(p.authors) > 3:
            authors_str += " et al."
        year_str = str(p.year) if p.year else "k.J."
        key_finding = _extract_key_sentences(p.abstract, max_chars=400)
        lines.append(f"**[Artikel {i}]** {p.title} ({year_str})")
        lines.append(f"*{authors_str or 'Autoren unbekannt'}*\n")
        lines.append(f"{key_finding}\n")

    lines.append("### Fazit\n")
    lines.append(
        f"Die ausgewerteten {n} Studien beleuchten das Thema \"{topic}\" aus "
        f"unterschiedlichen wissenschaftlichen Perspektiven. "
        f"Die Artikel stammen aus begutachteten Fachzeitschriften und wurden nach "
        f"wissenschaftlicher Relevanz (Zitationshäufigkeit) ausgewählt. "
        f"Für eine vollständige deutschsprachige KI-Auswertung dieser Quellen "
        f"kann ein Anthropic API-Schlüssel (ANTHROPIC_API_KEY) konfiguriert werden.\n"
    )

    lines.append("**Quellen**")
    for i, p in enumerate(papers, 1):
        authors_str = ", ".join(p.authors[:2])
        if len(p.authors) > 2:
            authors_str += " et al."
        year_str = str(p.year) if p.year else "k.J."
        if p.url:
            lines.append(f"{i}. {p.title} ({year_str}) – {authors_str or 'unbekannt'} – [{p.url}]({p.url})")
        else:
            lines.append(f"{i}. {p.title} ({year_str}) – {authors_str or 'unbekannt'}")

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
        "Du bist ein Wissenschaftsjournalist. Dein Stil: sachlich, locker und direkt – "
        "wie ein spannender Artikel bei Spiegel Wissen oder Zeit Wissen. "
        "Du erklärst komplexe Forschung so, dass sie jeder versteht, der keine Vorkenntnisse hat. "
        "Kein Akademiker-Deutsch, keine langen Schachtelsätze, kein Passiv wo es vermeidbar ist. "
        "Du schreibst ausschließlich auf Deutsch. "
        "Du verwendest NUR Informationen aus den dir bereitgestellten Abstracts – "
        "keine eigenen Kenntnisse, keine Ergänzungen, keine Vermutungen. "
        "Jede inhaltliche Aussage muss mit [Artikel N] belegt sein."
    )

    user = (
        f"Thema: {topic}\n\n"
        f"Hier sind {len(papers)} wissenschaftliche Fachartikel:\n"
        f"{articles_block}\n\n"
        "Schreibe einen gut lesbaren Bericht (ca. 400–550 Wörter) für neugierige Menschen ohne Fachkenntnisse.\n\n"
        "AUFBAU (genau in dieser Reihenfolge):\n\n"
        "1. ## Auf einen Blick\n"
        "   Genau 3–4 Bullet-Points mit den wichtigsten Zahlenwerten oder Fakten direkt aus den Artikeln.\n"
        "   Format pro Zeile (exakt einhalten):\n"
        "   - {Emoji} **{Zahl oder Kurzwert}** – {kurze Erklärung, max. 8 Wörter}\n"
        "   Beispiele:\n"
        "   - 🌡️ **+4°C** – So viel wärmer ist die Arktis seit 1980\n"
        "   - 📉 **13 %** – Rückgang der Meereisfläche pro Jahrzehnt\n\n"
        "2. ## Was die Forschung zeigt\n"
        "   Einleitung: Worum geht es, warum ist das wichtig? (2–3 lockere Sätze, direkt ansprechend)\n\n"
        "3. ## Die wichtigsten Erkenntnisse\n"
        "   Hauptaussagen der Artikel mit [Artikel N] belegt, in einfacher, lebendiger Sprache.\n\n"
        "4. ## Fazit\n"
        "   Was bedeutet das konkret für uns? (2–3 Sätze, gern mit einem klaren Statement)\n\n"
        "5. **Quellen**\n"
        "   1. Titel (Jahr) – Autoren – [DOI/Link](URL)\n\n"
        "STRENGE REGELN:\n"
        "1. Nur Informationen aus den obigen Abstracts – keine eigenen Ergänzungen.\n"
        "2. Jede inhaltliche Aussage mit [Artikel N] belegen.\n"
        "3. Fachbegriffe sofort in Klammern einfach erklären.\n"
        "4. Zahlen und Fakten aus den Artikeln hervorheben.\n"
        "5. Kein Akademiker-Deutsch – schreib für neugierige Menschen ohne Fachkenntnisse.\n\n"
        "Beginne direkt mit '## Auf einen Blick'."
    )

    client = anthropic.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2200,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return msg.content[0].text


# ── Haupt-Klasse ──────────────────────────────────────────────────────────────

class ReportScanner:
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

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        used_llm = False
        if api_key:
            try:
                summary = _llm_summary(papers, topic, api_key)
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
