# Team-Guide: AI Explanation

## Dein Branch
`team/ai-explanation`

## Aufgabe
Du integrierst die Anthropic Claude API, um Klimadaten in einfacher Sprache zu erklären.

## WICHTIGE REGELN
1. Arbeite NUR in deinem Branch: `team/ai-explanation`
2. Erstelle Feature-Branches nach Schema: `feature/ai-explanation/[feature]`
3. API-Key niemals ins Repository commiten! Nutze `.env`-Dateien.
4. Dokumentiere Erkenntnisse in `memory/team_logs/ai-explanation.log`

## LLM-Agenten in diesem Team

### ExplanationAgent
- Input: Datenpunkt + Nutzerfrage
- Output: Verständliche Erklärung via Claude API
- Endpunkt: `POST /api/v1/explain`

### ArticleIdeaAgent
- Input: Analyseergebnisse aus `data/processed/`
- Output: Ideen für Erklärungsartikel

## Umgebungsvariablen (`.env`)
```
ANTHROPIC_API_KEY=sk-ant-...
```

## Beispiel: Claude-Aufruf
```python
import anthropic

client = anthropic.Anthropic()

def explain_co2(value: float, date: str, question: str) -> str:
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"CO₂-Wert: {value} ppm ({date}). Frage: {question}"
            }
        ]
    )
    return message.content[0].text
```
