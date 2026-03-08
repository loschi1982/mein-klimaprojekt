"""
ClimateChat – Kontextbewusster KI-Chat für Klimadaten.
Regelbasiert mit optionalem Claude-LLM-Backend.
"""
import os
from dataclasses import dataclass, field


@dataclass
class ChatContext:
    source_id: str = ""
    current_value: float | None = None
    unit: str = ""
    from_year: int = 1960
    to_year: int = 2024
    view_label: str = ""


@dataclass
class ChatResponse:
    answer: str
    used_llm: bool = False
    suggestions: list[str] = field(default_factory=list)


# ── Regelbasierte Antworten ────────────────────────────────────────────────────

_SOURCE_CONTEXT = {
    "esrl_mauna_loa": {
        "label": "CO₂ (Mauna Loa)",
        "unit": "ppm",
        "safe_limit": 350,
        "preindustrial": 280,
        "institution": "NOAA/ESRL, Mauna Loa Observatory, Hawaii",
    },
    "esrl_co2_global": {
        "label": "Globaler CO₂-Mittelwert",
        "unit": "ppm",
        "safe_limit": 350,
        "preindustrial": 280,
        "institution": "NOAA/ESRL",
    },
    "esrl_ch4": {
        "label": "Methan (CH₄)",
        "unit": "ppb",
        "preindustrial": 722,
        "institution": "NOAA/ESRL",
    },
    "nasa_giss_global": {
        "label": "Globale Temperaturanomalie",
        "unit": "°C",
        "paris_15": 1.5,
        "paris_20": 2.0,
        "baseline": "1951–1980",
        "institution": "NASA GISS",
    },
    "berkeley_earth_global": {
        "label": "Globale Temperaturanomalie (Berkeley Earth)",
        "unit": "°C",
        "paris_15": 1.5,
        "paris_20": 2.0,
        "baseline": "1951–1980",
        "institution": "Berkeley Earth",
    },
    "csiro_sea_level": {
        "label": "Globaler Meeresspiegel",
        "unit": "mm",
        "baseline": "1990",
        "institution": "CSIRO (Church & White 2011)",
    },
    "nasa_giss_zonal": {
        "label": "Zonale Temperaturanomalien",
        "unit": "°C",
        "institution": "NASA GISS",
    },
}

_SUGGESTIONS = {
    "co2": [
        "Wie entwickelt sich der CO₂-Wert seit 1960?",
        "Was bedeutet die 350-ppm-Grenze?",
        "Wann wurde 400 ppm überschritten?",
    ],
    "temp": [
        "Was ist das Paris-Ziel?",
        "Welche Zone erwärmt sich am stärksten?",
        "Was bedeutet Temperaturanomalie?",
    ],
    "sea": [
        "Wie stark steigt der Meeresspiegel pro Jahr?",
        "Seit wann wird der Meeresspiegel gemessen?",
        "Was sind die Ursachen des Meeresspiegelanstiegs?",
    ],
    "ch4": [
        "Warum ist Methan gefährlich?",
        "Wie verhält sich CH₄ im Vergleich zu CO₂?",
        "Wo kommt Methan her?",
    ],
    "general": [
        "Was zeigt dieses Dashboard?",
        "Welche Datenquellen werden verwendet?",
        "Was ist der Treibhauseffekt?",
    ],
}


def _get_suggestions(source_id: str) -> list[str]:
    if "co2" in source_id or source_id in ("esrl_mauna_loa", "esrl_co2_global"):
        return _SUGGESTIONS["co2"]
    if "giss" in source_id or "berkeley" in source_id:
        return _SUGGESTIONS["temp"]
    if "sea_level" in source_id:
        return _SUGGESTIONS["sea"]
    if "ch4" in source_id:
        return _SUGGESTIONS["ch4"]
    return _SUGGESTIONS["general"]


def _rule_respond(message: str, ctx: ChatContext) -> str:  # noqa: C901 (allowed complexity)
    msg = message.lower().strip()
    sc = _SOURCE_CONTEXT.get(ctx.source_id, {})
    val = ctx.current_value
    unit = sc.get("unit", ctx.unit)
    label = sc.get("label", ctx.view_label or ctx.source_id)

    # ── Spezifische Themen zuerst (vor allgemeinen Catchalls) ─────────────────
    if any(w in msg for w in ("paris", "1,5 grad", "1.5 grad", "2 grad", "klimaziel")):
        return (
            "Das Pariser Abkommen (2015) hat das Ziel, die globale Erwärmung auf "
            "möglichst 1,5 °C – mindestens aber unter 2,0 °C – gegenüber dem vorindustriellen "
            "Niveau zu begrenzen. Stand 2024 liegt die globale Anomalie (NASA GISS) bei ca. "
            "+1,2–1,5 °C. Die Referenzperiode ist 1951–1980."
        )

    if any(w in msg for w in ("treibhauseffekt", "treibhausgas", "klimawandel", "global warming")):
        return (
            "Der Treibhauseffekt: Sonnenstrahlung trifft die Erde, wird als Wärme abgestrahlt "
            "und von Treibhausgasen (CO₂, CH₄, N₂O, H₂O) in der Atmosphäre zurückgehalten. "
            "CO₂ hat sich seit der Industrialisierung von ~280 ppm auf über 420 ppm erhöht – "
            "das verstärkt den Treibhauseffekt und erhöht die globale Durchschnittstemperatur."
        )

    if any(w in msg for w in ("quellen", "datenquellen", "woher", "institution")):
        return (
            "Die Daten stammen aus verifizierten wissenschaftlichen Quellen: "
            "NOAA GML/ESRL (CO₂, CH₄), NASA GISS (Temperatur), "
            "Berkeley Earth (Temperatur, unabhängig), CSIRO (Meeresspiegel). "
            "Alle Quellen sind öffentlich zugänglich und werden regelmäßig aktualisiert."
        )

    # ── Allgemeine Dashboard-Fragen ──────────────────────────────────────────
    if any(w in msg for w in ("was ist das", "was zeigt", "wofür", "erkläre das dashboard")):
        return (
            "Dieses Dashboard visualisiert Klimadaten aus wissenschaftlichen Quellen: "
            "CO₂- und Methan-Konzentrationen (NOAA/ESRL), globale Temperaturanomalien "
            "(NASA GISS, Berkeley Earth), zonale Temperaturkarten (3D-Globus) und "
            "den rekonstruierten Meeresspiegel (CSIRO). "
            "Im Menü kannst du zwischen den Datensätzen wechseln, den Zeitraum anpassen "
            "und im Admin-Bereich Berichte erstellen."
        )

    # ── CO₂-spezifische Fragen ───────────────────────────────────────────────
    if any(w in msg for w in ("350", "sicherheitsgrenze", "safe limit")):
        return (
            "350 ppm CO₂ gilt als wissenschaftliche Sicherheitsgrenze (James Hansen, 2008) – "
            "der Wert, bei dem das Klimasystem auf lange Sicht stabil bleibt. "
            "Diese Grenze wurde um 1988 überschritten. Heute liegen wir bei über 420 ppm."
        )

    if any(w in msg for w in ("400", "wann wurde 400")):
        return (
            "Die 400-ppm-Marke wurde erstmals im Mai 2013 an der Mauna Loa Station überschritten. "
            "Seitdem ist der CO₂-Wert weiter gestiegen und lag 2024 bei ca. 422–424 ppm."
        )

    if any(w in msg for w in ("vorindustriell", "preindustrial", "vor industrialisierung")):
        return (
            "Der vorindustrielle CO₂-Wert (vor 1750) lag bei ca. 280 ppm. "
            "Methan (CH₄) lag bei ~722 ppb. "
            "Heute sind CO₂ bei >420 ppm (+50%) und CH₄ bei >1900 ppb (+160%) – "
            "die höchsten Werte seit mindestens 800.000 Jahren (Eisbohrkerne)."
        )

    if any(w in msg for w in ("keeling", "keeling curve", "kurve")):
        return (
            "Die Keeling-Kurve, benannt nach Charles David Keeling, zeigt die CO₂-Konzentration "
            "seit 1958 an der Mauna Loa Station. Sie ist das längste kontinuierliche CO₂-Messprotokoll "
            "der Welt und zeigt sowohl den stetigen Anstieg als auch die jährliche Saisonalität "
            "(CO₂-Senke im Sommer durch Pflanzenwachstum der Nordhalbkugel)."
        )

    # ── Methan-spezifische Fragen ────────────────────────────────────────────
    if any(w in msg for w in ("methan", "ch4", "methane")):
        ch4_val = f" (aktuell: {val:.1f} ppb)" if val and "ch4" in ctx.source_id else ""
        return (
            f"Methan (CH₄){ch4_val} ist nach CO₂ das wichtigste langlebige Treibhausgas. "
            "Über 20 Jahre wirkt es ~80× stärker als CO₂, über 100 Jahre ~30×. "
            "Quellen: Rinderhaltung (~30%), fossile Brennstoffe (~30%), Nassreisanbau, Mülldeponien, Feuchtgebiete. "
            f"Der vorindustrielle Wert lag bei ~722 ppb, heute bei >1900 ppb."
        )

    # ── Temperatur-spezifische Fragen ────────────────────────────────────────
    if any(w in msg for w in ("anomalie", "temperaturanomalie", "was ist eine anomalie")):
        baseline = sc.get("baseline", "1951–1980")
        return (
            f"Eine Temperaturanomalie ist die Abweichung vom Referenzdurchschnitt ({baseline}). "
            "Ein Wert von +1,2 °C bedeutet: Die Temperatur liegt 1,2 °C über dem Mittelwert "
            f"der Referenzperiode {baseline}. Positive Werte = wärmer als Referenz, "
            "negative = kälter. Diese Darstellung ermöglicht globale Vergleiche."
        )

    if any(w in msg for w in ("erwärmt sich am stärksten", "arkti", "pol", "nord")):
        return (
            "Die Arktis (Zone 64N–90N) erwärmt sich 3–4× schneller als der globale Durchschnitt – "
            "ein Phänomen namens 'Arctic Amplification'. Ursachen: schmelzendes Meereis "
            "reduziert die Rückstrahlung (Albedo-Effekt), auftauender Permafrost setzt CH₄ frei. "
            "Im 3D-Globus-Modus sind die arktischen Zonen daher oft am stärksten rot eingefärbt."
        )

    if any(w in msg for w in ("nasa giss", "berkeley earth", "unterschied", "vergleich")):
        return (
            "NASA GISS und Berkeley Earth sind unabhängige Temperatur-Rekonstruktionen. "
            "Beide zeigen sehr ähnliche Trends, unterscheiden sich aber in Methodik und Stationsabdeckung. "
            "Berkeley Earth verwendet mehr Wetterstationen, NASA GISS integriert Meeresoberflächentemperaturen. "
            "Die Übereinstimmung beider Datensätze stärkt das wissenschaftliche Vertrauen."
        )

    # ── Meeresspiegel-spezifische Fragen ────────────────────────────────────
    if any(w in msg for w in ("meeresspiegel", "sea level", "anstieg pro jahr")):
        return (
            "Der globale Meeresspiegel steigt derzeit um ca. 3,6 mm/Jahr (Satellitenmessungen). "
            "Im 20. Jahrhundert waren es ~1,4 mm/Jahr – die Rate hat sich beschleunigt. "
            "Ursachen: Wärmeausdehnung des Wassers (~40%), schmelzende Gletscher (~40%), "
            "Grönland- und Antarktis-Eisschilde (~20%). "
            "Die CSIRO-Daten (Tide-Gauge-Messungen) zeigen den Anstieg seit 1880."
        )

    if any(w in msg for w in ("ursache", "warum steigt", "warum steigen")):
        return (
            "Der Meeresspiegelanstieg hat zwei Hauptursachen: "
            "1) Wärmeausdehnung – wärmeres Wasser nimmt mehr Volumen ein. "
            "2) Schmelzwasser – von Gletschern, dem Grönländischen und Antarktischen Eisschild. "
            "Beide Effekte werden durch den CO₂-bedingten Temperaturanstieg verstärkt. "
            "Bei +2 °C werden bis 2100 Anstiege von 0,3–1,0 m erwartet (IPCC AR6)."
        )

    # ── Aktueller Wert ───────────────────────────────────────────────────────
    if any(w in msg for w in ("aktuell", "jetzt", "heute", "letzter wert", "aktueller wert", "was ist der wert")):
        if val is not None:
            return (
                f"Der zuletzt geladene Wert für {label} beträgt {val:.2f} {unit} "
                f"(Zeitraum: {ctx.from_year}–{ctx.to_year}). "
                + _value_context(ctx.source_id, val, sc)
            )
        return (
            f"Du schaust dir gerade den Datensatz \"{label}\" an. "
            "Ein konkreter Datenpunkt ist in diesem Kontext nicht verfügbar. "
            "Bitte wähle einen Datenpunkt direkt im Chart aus."
        )

    if any(w in msg for w in ("was bedeutet", "was heißt", "bedeutung")):
        if val is not None:
            return (
                f"{label}: {val:.2f} {unit}. " + _value_context(ctx.source_id, val, sc)
            )

    # ── Zeitraum ─────────────────────────────────────────────────────────────
    if any(w in msg for w in ("zeitraum", "von wann", "seit wann", "wie lange")):
        inst = sc.get("institution", "")
        return (
            f"Der Datensatz \"{label}\" ({inst}) deckt im aktuell gewählten "
            f"Zeitraum {ctx.from_year}–{ctx.to_year} ab. "
            f"Die Gesamtaufzeichnung reicht je nach Quelle bis 1880 zurück."
        )

    # ── Fallback ─────────────────────────────────────────────────────────────
    inst = sc.get("institution", "")
    val_str = f" (zuletzt: {val:.2f} {unit})" if val is not None else ""
    return (
        f"Ich bin ein regelbasierter Klimachat und antworte auf Fragen zu: "
        f"CO₂, Methan, Temperaturanomalien, Meeresspiegel, Paris-Ziel, Treibhauseffekt. "
        f"Aktuell angezeigt: {label}{val_str}. "
        f"Stelle eine konkretere Frage oder setze ANTHROPIC_API_KEY für KI-Antworten."
    )


def _value_context(source_id: str, val: float, sc: dict) -> str:
    """Erzeugt eine kontextuelle Einordnung für einen Messwert."""
    if "co2" in source_id or source_id in ("esrl_mauna_loa", "esrl_co2_global"):
        pre = sc.get("preindustrial", 280)
        safe = sc.get("safe_limit", 350)
        increase = val - pre
        if val > 420:
            return (
                f"Das ist {increase:.0f} ppm über dem vorindustriellen Niveau (~{pre} ppm) "
                f"und {val - safe:.0f} ppm über der Sicherheitsgrenze ({safe} ppm)."
            )
        if val > 350:
            return f"Das überschreitet die Sicherheitsgrenze von {safe} ppm, liegt aber unter 420 ppm."
        return f"Das liegt nahe oder unter der Sicherheitsgrenze von {safe} ppm."

    if "giss" in source_id or "berkeley" in source_id:
        p15 = sc.get("paris_15", 1.5)
        p20 = sc.get("paris_20", 2.0)
        if val >= p20:
            return f"Das überschreitet das Paris-Ziel von +{p20} °C deutlich."
        if val >= p15:
            return f"Das liegt am oder über dem strengeren Paris-Ziel von +{p15} °C."
        if val > 0:
            return f"Das liegt unter dem Paris-Ziel ({p15} °C), zeigt aber eine Erwärmung."
        return "Negative Anomalie – kühler als die Referenzperiode."

    if "sea_level" in source_id:
        baseline = sc.get("baseline", "1990")
        if val > 0:
            return f"Der Meeresspiegel liegt {val:.0f} mm über dem {baseline}-Mittel."
        return f"Der Meeresspiegel liegt {abs(val):.0f} mm unter dem {baseline}-Mittel."

    if "ch4" in source_id:
        pre = sc.get("preindustrial", 722)
        increase = val - pre
        return f"Das ist {increase:.0f} ppb über dem vorindustriellen Niveau (~{pre} ppb)."

    return ""


# ── ClimateChat ────────────────────────────────────────────────────────────────

class ClimateChat:
    """Kontextbewusster Klimadaten-Chat. Regelbasiert oder LLM-gestützt."""

    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")

    def respond(
        self,
        message: str,
        context: ChatContext,
        history: list[dict] | None = None,
        use_llm: bool = False,
    ) -> ChatResponse:
        if use_llm and self.api_key:
            try:
                answer = self._llm_respond(message, context, history or [])
                return ChatResponse(
                    answer=answer,
                    used_llm=True,
                    suggestions=_get_suggestions(context.source_id),
                )
            except Exception:
                pass  # Fallback auf regelbasiert

        return ChatResponse(
            answer=_rule_respond(message, context),
            used_llm=False,
            suggestions=_get_suggestions(context.source_id),
        )

    def _llm_respond(self, message: str, ctx: ChatContext, history: list[dict]) -> str:
        import anthropic

        sc = _SOURCE_CONTEXT.get(ctx.source_id, {})
        system = (
            "Du bist ein freundlicher Klimaexperte auf einem Klimadaten-Dashboard. "
            "Beantworte Fragen auf Deutsch, präzise und in 2–4 Sätzen. "
            f"Aktuell angezeigter Datensatz: {sc.get('label', ctx.source_id)} "
            f"({sc.get('institution', '')}). "
            f"Zeitraum: {ctx.from_year}–{ctx.to_year}. "
            + (f"Letzter Messwert: {ctx.current_value:.2f} {sc.get('unit', ctx.unit)}. "
               if ctx.current_value is not None else "")
        )

        messages = []
        for h in (history or [])[-6:]:  # max. 6 Nachrichten Verlauf
            if h.get("role") in ("user", "assistant"):
                messages.append({"role": h["role"], "content": h["content"]})
        messages.append({"role": "user", "content": message})

        client = anthropic.Anthropic(api_key=self.api_key)
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            system=system,
            messages=messages,
        )
        return msg.content[0].text
