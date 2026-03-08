"""
ArticleIdeaAgent – generiert Artikelideen aus Klimaanalysedaten.
Team-Branch: team/ai-explanation
"""
import os
from dataclasses import dataclass, field


@dataclass
class ArticleIdea:
    title: str
    hook: str
    key_points: list[str]
    target_audience: str = "Allgemein"


class ArticleIdeaAgent:
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")

    def generate(self, analysis_summary: dict, count: int = 5) -> list[ArticleIdea]:
        """
        Generiert Artikelideen aus einem Analyse-Zusammenfassung-Dict.
        Erwartet Felder: slope, mean, max_value, anomaly_count, min_date, max_date
        """
        if self.api_key:
            try:
                return self._llm_generate(analysis_summary, count)
            except Exception:
                pass
        return self._rule_generate(analysis_summary, count)

    def _rule_generate(self, summary: dict, count: int) -> list[ArticleIdea]:
        slope = summary.get("slope", 2.0)
        max_val = summary.get("max_value", 425.0)
        anomaly_count = summary.get("anomaly_count", 0)
        mean = summary.get("mean", 390.0)
        min_date = summary.get("min_date", "1958")[:4]
        max_date = summary.get("max_date", "2026")[:4]

        templates: list[ArticleIdea] = [
            ArticleIdea(
                title=f"CO₂-Rekord: Was {max_val:.1f} ppm für unser Klima bedeuten",
                hook=f"Die CO₂-Konzentration hat {max_val:.1f} ppm erreicht – ein historischer Höchstwert.",
                key_points=[
                    f"Vorindustrieller Wert: ~280 ppm",
                    f"Aktueller Rekord: {max_val:.1f} ppm",
                    "Sicherheitsgrenze 350 ppm längst überschritten",
                    "Auswirkungen auf Meeresspiegel und Extremwetter",
                ],
                target_audience="Allgemein",
            ),
            ArticleIdea(
                title=f"Der Mauna-Loa-Trend: {slope:.2f} ppm pro Jahr – und kein Ende in Sicht",
                hook=f"Seit {min_date} steigt CO₂ im Schnitt um {slope:.2f} ppm jährlich.",
                key_points=[
                    f"Trendanalyse {min_date}–{max_date}",
                    f"Durchschnittlicher Anstieg: {slope:.2f} ppm/Jahr",
                    "Vergleich mit den 1960er Jahren",
                    "Was passiert, wenn der Trend anhält?",
                ],
                target_audience="Schüler & Studierende",
            ),
            ArticleIdea(
                title="Klimadaten lesen: So verstehst du die Keeling-Kurve",
                hook="Eine der wichtigsten Kurven der Wissenschaft – und so liest du sie.",
                key_points=[
                    "Was misst Mauna Loa genau?",
                    "Warum schwanken die Werte saisonal?",
                    f"Mittelwert der Messreihe: {mean:.1f} ppm",
                    "Bedeutung für den Klimawandel",
                ],
                target_audience="Einsteiger",
            ),
            ArticleIdea(
                title=f"Klimaanomalien: {anomaly_count} auffällige Messwerte unter der Lupe",
                hook=f"Unsere Analyse hat {anomaly_count} statistische Ausreißer entdeckt – was steckt dahinter?",
                key_points=[
                    "Was ist eine Klimaanomalie?",
                    "Z-Score-Methode einfach erklärt",
                    f"{anomaly_count} Ausreißer in der Mauna-Loa-Messreihe",
                    "Natürliche vs. menschengemachte Ursachen",
                ],
                target_audience="Interessierte Laien",
            ),
            ArticleIdea(
                title="RCP-Szenarien: Drei mögliche Klimazukünfte bis 2100",
                hook="Je nachdem, was wir jetzt tun, sieht 2100 sehr unterschiedlich aus.",
                key_points=[
                    "RCP 2.6: Starke Reduktion – ~450 ppm",
                    "RCP 4.5: Moderate Maßnahmen – ~550 ppm",
                    "RCP 8.5: Business as Usual – >900 ppm",
                    "Was müssen wir heute tun?",
                ],
                target_audience="Allgemein",
            ),
        ]
        return templates[:count]

    def _llm_generate(self, summary: dict, count: int) -> list[ArticleIdea]:
        import anthropic
        import json
        client = anthropic.Anthropic(api_key=self.api_key)
        prompt = (
            f"Du bist ein Wissenschaftsjournalist. Generiere {count} Artikelideen "
            f"basierend auf diesen Klimadaten:\n{json.dumps(summary, ensure_ascii=False)}\n\n"
            f"Antworte als JSON-Array mit Objekten: "
            f"{{title, hook, key_points: [str], target_audience}}"
        )
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = msg.content[0].text
        # JSON aus Antwort extrahieren
        start = raw.find("[")
        end = raw.rfind("]") + 1
        ideas_raw = json.loads(raw[start:end])
        return [ArticleIdea(**idea) for idea in ideas_raw[:count]]
