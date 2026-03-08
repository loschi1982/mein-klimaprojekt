"""
ExplanationAgent – erklärt Klimadaten in einfacher Sprache via Claude API.
Fällt bei fehlendem API-Key auf regelbasierte Erklärungen zurück.
Team-Branch: team/ai-explanation
"""
import os
from dataclasses import dataclass, field


@dataclass
class ExplanationResult:
    explanation: str
    confidence: str = "high"
    sources: list[str] = field(default_factory=list)
    used_llm: bool = False


class ExplanationAgent:
    AUDIENCES = {
        "beginner": "Erkläre einfach und verständlich, ohne Fachbegriffe. Nutze Alltagsvergleiche.",
        "expert": "Erkläre präzise und wissenschaftlich. Nutze Fachterminologie.",
    }

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")

    def explain(
        self,
        data_point: dict,
        question: str,
        audience: str = "beginner",
    ) -> ExplanationResult:
        """
        Erklärt einen Klimadatenpunkt.
        audience: "beginner" | "expert"
        """
        if audience not in self.AUDIENCES:
            audience = "beginner"

        if self.api_key:
            try:
                text = self._llm_explain(data_point, question, audience)
                return ExplanationResult(
                    explanation=text,
                    confidence="high",
                    sources=self._sources(data_point),
                    used_llm=True,
                )
            except Exception:
                pass

        return ExplanationResult(
            explanation=self._rule_explain(data_point, question),
            confidence="medium",
            sources=self._sources(data_point),
            used_llm=False,
        )

    def _llm_explain(self, data_point: dict, question: str, audience: str) -> str:
        import anthropic
        style = self.AUDIENCES[audience]
        prompt = (
            f"Du bist ein Klimawissenschaftler. {style}\n\n"
            f"Datenpunkt: {data_point}\n"
            f"Frage: {question}\n\n"
            "Antworte in 2–3 Sätzen."
        )
        client = anthropic.Anthropic(api_key=self.api_key)
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text

    def _rule_explain(self, data_point: dict, question: str) -> str:
        dtype = data_point.get("type", "")
        value = data_point.get("value")
        date = data_point.get("date", "")

        if dtype == "co2" and value is not None:
            context = ""
            if value > 420:
                context = (
                    f"Dieser Wert von {value} ppm liegt deutlich über der vorindustriellen "
                    f"Konzentration von ~280 ppm und überschreitet die als sicher geltende "
                    f"Grenze von 350 ppm um {value - 350:.1f} ppm."
                )
            elif value > 350:
                context = (
                    f"Mit {value} ppm liegt die CO₂-Konzentration über der Sicherheitsgrenze "
                    f"von 350 ppm, aber noch deutlich unter dem heutigen Niveau (>420 ppm)."
                )
            else:
                context = (
                    f"Ein CO₂-Wert von {value} ppm liegt nahe oder unter der als sicher "
                    f"geltenden Grenze von 350 ppm."
                )
            date_str = f" im Messzeitraum {date}" if date else ""
            return f"CO₂-Konzentration{date_str}: {value} ppm. {context}"

        # Generischer Fallback
        parts = [f"{k}: {v}" for k, v in data_point.items()]
        return (
            f"Der Datenpunkt ({', '.join(parts)}) zeigt einen Messwert im Klimadatensystem. "
            f"Zur Frage '{question}': Ohne detailliertere Kontextdaten ist eine präzise "
            f"regelbasierte Erklärung nicht möglich. "
            f"Bitte ANTHROPIC_API_KEY setzen für eine KI-gestützte Erklärung."
        )

    def _sources(self, data_point: dict) -> list[str]:
        dtype = data_point.get("type", "")
        if dtype == "co2":
            return ["NOAA ESRL – Mauna Loa Observatory"]
        return []
