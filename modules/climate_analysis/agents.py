"""
LLM-Agenten für Climate Analysis
Team-Branch: team/climate-analysis

DataAnalystAgent  – analysiert Datensätze, erkennt Anomalien
TrendDetectorAgent – identifiziert Langzeit- und Kurzzeit-Trends
"""
import os
from dataclasses import dataclass

from .analyzer import (
    AnalysisResult,
    AnomalyResult,
    TrendResult,
    analyze_co2,
)


@dataclass
class AgentReport:
    agent: str
    summary: str
    findings: list[str]
    recommendations: list[str]
    raw_response: str = ""


# ── DataAnalystAgent ──────────────────────────────────────────────────────────

class DataAnalystAgent:
    """
    Analysiert einen Klimadatensatz und erkennt Anomalien.
    Gibt einen strukturierten Report zurück.
    Nutzt Claude API wenn ANTHROPIC_API_KEY gesetzt ist,
    sonst regelbasierte Analyse.
    """

    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm and bool(os.getenv("ANTHROPIC_API_KEY"))

    def run(self, result: AnalysisResult) -> AgentReport:
        findings = self._rule_based_findings(result)
        summary = self._build_summary(result, findings)

        if self.use_llm:
            llm_summary = self._llm_enrich(result, findings)
            return AgentReport(
                agent="DataAnalystAgent",
                summary=llm_summary,
                findings=findings,
                recommendations=self._recommendations(result),
                raw_response=llm_summary,
            )

        return AgentReport(
            agent="DataAnalystAgent",
            summary=summary,
            findings=findings,
            recommendations=self._recommendations(result),
        )

    def _rule_based_findings(self, result: AnalysisResult) -> list[str]:
        findings = []
        s = result.stats
        t = result.trend

        findings.append(
            f"Analysezeitraum: {s.min_date} bis {s.max_date} ({s.count} Messpunkte)"
        )
        findings.append(
            f"Mittelwert: {s.mean} {s.unit} | Min: {s.min} ({s.min_date}) | Max: {s.max} ({s.max_date})"
        )
        findings.append(f"Trend: {t.interpretation} (R²={t.r_squared})")

        if t.r_squared > 0.95:
            findings.append("Sehr hohe Linearität des Trends (R² > 0.95) – stabiler, anhaltender Anstieg")
        elif t.r_squared > 0.8:
            findings.append("Starke Linearität (R² > 0.80) – klarer Trend erkennbar")

        if result.anomalies:
            critical = [a for a in result.anomalies if a.severity == "critical"]
            findings.append(
                f"{len(result.anomalies)} Anomalien erkannt"
                + (f", davon {len(critical)} kritisch" if critical else "")
            )
        else:
            findings.append("Keine statistischen Anomalien erkannt (Z-Score < 2.5)")

        return findings

    def _build_summary(self, result: AnalysisResult, findings: list[str]) -> str:
        return (
            f"DataAnalystAgent-Report: CO₂-Analyse abgeschlossen. "
            f"{result.stats.count} Messwerte ausgewertet. "
            f"Trend: {result.trend.slope:+.2f} {result.unit}/Jahr. "
            f"{len(result.anomalies)} Anomalien gefunden."
        )

    def _recommendations(self, result: AnalysisResult) -> list[str]:
        recs = []
        if result.trend.slope > 2.0:
            recs.append("CO₂-Anstieg überschreitet 2 ppm/Jahr – Emissionsreduktion dringend erforderlich")
        if result.stats.max > 420:
            recs.append("CO₂-Konzentration über 420 ppm – historischer Höchstwert überschritten")
        if result.trend.r_squared > 0.9:
            recs.append("Trendstabilität sehr hoch – ohne Gegenmaßnahmen setzt sich Anstieg fort")
        if not recs:
            recs.append("Monitoring fortsetzen – monatliche Aktualisierung empfohlen")
        return recs

    def _llm_enrich(self, result: AnalysisResult, findings: list[str]) -> str:
        try:
            import anthropic
            client = anthropic.Anthropic()
            prompt = (
                "Du bist ein erfahrener Klimadatenwissenschaftler.\n"
                f"Analysiere diese Klimadaten-Auswertung und fasse sie in 3–4 Sätzen zusammen:\n\n"
                f"Quelle: {result.source}\n"
                f"Messwerte: {result.stats.count}\n"
                f"Zeitraum: {result.stats.min_date} – {result.stats.max_date}\n"
                f"Mittelwert: {result.stats.mean} {result.unit}\n"
                f"Trend: {result.trend.slope:+.2f} {result.unit}/Jahr (R²={result.trend.r_squared})\n"
                f"Anomalien: {len(result.anomalies)}\n\n"
                "Befunde:\n" + "\n".join(f"- {f}" for f in findings) + "\n\n"
                "Schreibe eine klare, sachliche Zusammenfassung für ein wissenschaftliches Publikum."
            )
            msg = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text
        except Exception:
            return self._build_summary(result, findings)


# ── TrendDetectorAgent ────────────────────────────────────────────────────────

class TrendDetectorAgent:
    """
    Identifiziert Langzeit- und Kurzzeit-Trends in Klimadaten.
    Vergleicht 10-Jahres- und 30-Jahres-Trends.
    """

    def __init__(self, use_llm: bool = True):
        self.use_llm = use_llm and bool(os.getenv("ANTHROPIC_API_KEY"))

    def run(
        self,
        full_result: AnalysisResult,
        recent_result: AnalysisResult | None = None,
    ) -> AgentReport:
        findings = self._detect(full_result, recent_result)
        summary = self._build_summary(full_result, recent_result)

        if self.use_llm:
            llm_summary = self._llm_enrich(full_result, recent_result, findings)
            return AgentReport(
                agent="TrendDetectorAgent",
                summary=llm_summary,
                findings=findings,
                recommendations=self._recommendations(full_result, recent_result),
                raw_response=llm_summary,
            )

        return AgentReport(
            agent="TrendDetectorAgent",
            summary=summary,
            findings=findings,
            recommendations=self._recommendations(full_result, recent_result),
        )

    def _detect(
        self,
        full: AnalysisResult,
        recent: AnalysisResult | None,
    ) -> list[str]:
        findings = [
            f"Langzeit-Trend (gesamter Zeitraum): {full.trend.slope:+.4f} {full.unit}/Jahr",
            f"Bestimmtheitsmaß R²={full.trend.r_squared} – "
            + ("sehr starke Linearität" if full.trend.r_squared > 0.95 else "moderate Linearität"),
        ]
        if recent:
            diff = recent.trend.slope - full.trend.slope
            findings.append(
                f"Kurzzeit-Trend (letzte 10 Jahre): {recent.trend.slope:+.4f} {full.unit}/Jahr"
            )
            if diff > 0.1:
                findings.append(
                    f"Beschleunigung erkannt: Kurzzeit-Trend {diff:+.4f} {full.unit}/Jahr "
                    f"schneller als Langzeit-Trend"
                )
            elif diff < -0.1:
                findings.append(
                    f"Verlangsamung erkannt: Kurzzeit-Trend {diff:+.4f} {full.unit}/Jahr "
                    f"langsamer als Langzeit-Trend"
                )
            else:
                findings.append("Trend ist stabil – keine signifikante Beschleunigung oder Verlangsamung")
        return findings

    def _build_summary(
        self, full: AnalysisResult, recent: AnalysisResult | None
    ) -> str:
        base = (
            f"TrendDetectorAgent-Report: Langzeit-Trend {full.trend.slope:+.2f} {full.unit}/Jahr "
            f"(R²={full.trend.r_squared})."
        )
        if recent:
            base += f" Kurzzeit-Trend: {recent.trend.slope:+.2f} {full.unit}/Jahr."
        return base

    def _recommendations(
        self, full: AnalysisResult, recent: AnalysisResult | None
    ) -> list[str]:
        recs = []
        if recent and recent.trend.slope > full.trend.slope + 0.1:
            recs.append("Trend beschleunigt sich – Ursachenanalyse empfohlen")
        if full.trend.r_squared > 0.95:
            recs.append("Hochlinearer Trend – Projektion für 2030/2050 sinnvoll")
        if not recs:
            recs.append("Trendüberwachung mit 5-Jahres-Vergleichen fortsetzen")
        return recs

    def _llm_enrich(
        self,
        full: AnalysisResult,
        recent: AnalysisResult | None,
        findings: list[str],
    ) -> str:
        try:
            import anthropic
            client = anthropic.Anthropic()
            recent_info = ""
            if recent:
                recent_info = (
                    f"\nKurzzeit-Trend (letzte 10 Jahre): {recent.trend.slope:+.4f} {full.unit}/Jahr"
                )
            prompt = (
                "Du bist ein Klimawissenschaftler, spezialisiert auf Trendanalyse.\n"
                f"Analysiere diese Trenddaten und erkläre ihre Bedeutung in 3–4 Sätzen:\n\n"
                f"Langzeit-Trend: {full.trend.slope:+.4f} {full.unit}/Jahr"
                f"{recent_info}\n"
                f"R²={full.trend.r_squared}\n\n"
                "Befunde:\n" + "\n".join(f"- {f}" for f in findings) + "\n\n"
                "Erkläre die klimatische Bedeutung dieser Trends verständlich."
            )
            msg = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text
        except Exception:
            return self._build_summary(full, recent)
