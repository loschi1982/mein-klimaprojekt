# Systemarchitektur

## Übersicht

```
[Externe Datenquellen]
        ↓
[Data Ingestion Module]  →  [Raw Data Store / data/raw/]
        ↓
[Climate Analysis Module]  →  [Processed Data / data/processed/]
        ↓
[Knowledge Base]  ←→  [AI Explanation System]
        ↓
[Simulation Engine]  ←→  [Visualization Engine]
        ↓
[Frontend (React)]  ←→  [REST API (FastAPI)]
        ↓
[Nutzer / Browser]
```

---

## Komponenten

### 1. Data Ingestion Module
- **Branch:** `team/data-ingestion`
- **Verantwortlichkeiten:** Datenabruf von externen Quellen, Normalisierung, Speicherung
- **Input:** URLs, CSV-Dateien, APIs (NOAA, Copernicus, ESRL)
- **Output:** Standardisierte JSON/CSV in `data/raw/`
- **APIs:**
  - `POST /api/v1/ingest` – Neuen Datenabruf starten
  - `GET /api/v1/datasets` – Verfügbare Datensätze auflisten

### 2. Climate Analysis Module
- **Branch:** `team/climate-analysis`
- **Verantwortlichkeiten:** Statistische Analyse, Trend-Erkennung, Anomalie-Detektion
- **Input:** Rohdaten aus `data/raw/`
- **Output:** Analyseergebnisse in `data/processed/`
- **APIs:**
  - `GET /api/v1/analysis/temperature` – Temperaturdaten
  - `GET /api/v1/analysis/co2` – CO₂-Trenddaten

### 3. Visualization Engine
- **Branch:** `team/visualization`
- **Verantwortlichkeiten:** Interaktive Charts, Karten, UI-Komponenten
- **Input:** Verarbeitete Daten aus `data/processed/`
- **Output:** React-Komponenten, Chart-Konfigurationen
- **APIs:**
  - `GET /api/v1/charts/{chart_id}` – Chart-Daten abrufen

### 4. Simulation Engine
- **Branch:** `team/simulation`
- **Verantwortlichkeiten:** Klimaszenario-Simulationen
- **Input:** Klimaparameter, Szenarien
- **Output:** Simulationsergebnisse als JSON
- **APIs:**
  - `POST /api/v1/simulate` – Simulation starten
  - `GET /api/v1/scenarios` – Verfügbare Szenarien

### 5. Knowledge Base
- **Branch:** `team/knowledge-base`
- **Verantwortlichkeiten:** Strukturiertes Wissen speichern und abrufen
- **Input:** Analyseergebnisse, Simulationsdaten
- **Output:** Strukturiertes Wissen in `memory/knowledge_base.json`
- **APIs:**
  - `GET /api/v1/knowledge/{topic}` – Wissensbeitrag abrufen

### 6. AI Explanation System
- **Branch:** `team/ai-explanation`
- **Verantwortlichkeiten:** Natürlichsprachliche Erklärungen via Claude API
- **Input:** Komplexe Datenpunkte, Nutzerfragen
- **Output:** Erklärungen als Text
- **APIs:**
  - `POST /api/v1/explain` – Erklärung generieren

### 7. REST API (Backend)
- **Branch:** `team/api`
- **Verantwortlichkeiten:** FastAPI-Routing, Auth, Datenbankzugriff
- **Technologie:** FastAPI + uvicorn + SQLite

### 8. Frontend
- **Branch:** `team/frontend`
- **Verantwortlichkeiten:** Gesamte React-App, Routing, State Management
- **Technologie:** React + Vite + Chart.js/Plotly

---

## LLM-Agenten

| Agent | Aufgabe | Branch |
|---|---|---|
| DataAnalystAgent | Analysiert neue Datensätze, erkennt Anomalien | team/climate-analysis |
| TrendDetectorAgent | Identifiziert Langzeit- und Kurzzeit-Trends | team/climate-analysis |
| ArticleIdeaAgent | Generiert Inhaltsideen aus Analyseergebnissen | team/ai-explanation |
| ExplanationAgent | Erklärt Datenpunkte in einfacher Sprache | team/ai-explanation |
