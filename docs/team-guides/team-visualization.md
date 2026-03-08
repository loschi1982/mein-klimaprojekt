# Team-Guide: Visualization

## Dein Branch
`team/visualization`

## Aufgabe
Du erstellst interaktive Charts und React-Komponenten zur Visualisierung der Klimadaten.

## WICHTIGE REGELN
1. Arbeite NUR in deinem Branch: `team/visualization`
2. Erstelle Feature-Branches nach Schema: `feature/visualization/[feature]`
3. Dokumentiere Erkenntnisse in `memory/team_logs/visualization.log`

## Phase 1 – Aufgaben

### 1. Erste CO₂-Zeitreihengrafik
```bash
git checkout -b feature/visualization/co2-timeseries
```

- Daten holen von: `GET /api/v1/analysis/co2`
- Bibliothek: Chart.js oder Plotly
- Komponente: `services/frontend/src/components/Co2Chart.jsx`

## Starten (React-Frontend)
```bash
cd services/frontend
npm install
npm run dev
```

Frontend: http://localhost:5173
