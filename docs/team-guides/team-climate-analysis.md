# Team-Guide: Climate Analysis

## Dein Branch
`team/climate-analysis`

## Aufgabe
Du analysierst die Rohdaten statistisch, erkennst Trends und Anomalien und stellst die Ergebnisse bereit.

## WICHTIGE REGELN
1. Arbeite NUR in deinem Branch: `team/climate-analysis`
2. Erstelle Feature-Branches nach Schema: `feature/climate-analysis/[feature]`
3. Dokumentiere Erkenntnisse in `memory/team_logs/climate-analysis.log`

## LLM-Agenten in diesem Team

### DataAnalystAgent
- Analysiert neue Datensätze in `data/raw/`
- Erkennt Ausreißer und Anomalien
- Speichert Ergebnisse in `data/processed/`

### TrendDetectorAgent
- Berechnet Langzeit-Trends (z.B. CO₂-Anstieg pro Jahr)
- Identifiziert saisonale Muster
- Output: Trend-JSON mit Slope, R², Konfidenzintervall

## Phase 2 – Aufgaben
- Temperatur-Trend-Analyse (1880–heute)
- CO₂-Korrelationsanalyse
- Anomalie-Detektion mit Z-Score
