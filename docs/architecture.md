# Systemarchitektur

## Übersicht

```
[Externe Datenquellen]
        ↓
[Data Ingestion Module]  →  [data/raw/]
        ↓
[Climate Analysis Module]  →  [data/processed/]
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
- **Dateien:** `modules/data_ingestion/ingester.py`, `modules/data_ingestion/sources.py`
- **Verantwortlichkeiten:** Datenabruf, Normalisierung, CSV-Validierung
- **Datenquellen (7):**

| ID | Quelle | Format | Besonderheit |
|---|---|---|---|
| `co2_mauna_loa` | ESRL/GML Mauna Loa | CSV | |
| `esrl_co2_global` | ESRL Globales CO₂ | CSV | |
| `esrl_ch4` | ESRL Methan CH₄ | CSV | |
| `berkeley_earth_global` | Berkeley Earth | CSV | Anomalie, Basis 1951–1980 |
| `csiro_sea_level` | CSIRO Meeresspiegel | CSV | GitHub-Mirror, Basis 1990 |
| `nasa_giss_global` | NASA GISS Global | CSV | Anomalie, Basis 1951–1980 |
| `nasa_giss_zonal` | NASA GISS Zonal | **JSON** | Anomalie, Basis 1951–1980 |

> **Achtung:** `nasa_giss_zonal` wird als `.json` gespeichert – `validate_csv()` wird dafür übersprungen.

- **APIs:** `POST /api/v1/ingest`, `GET /api/v1/datasets`
- **Admin-APIs:** `GET /api/v1/admin/sources`, `POST /api/v1/admin/import`

### 2. Climate Analysis Module
- **Branch:** `team/climate-analysis`
- **Dateien:** `modules/climate_analysis/analyzer.py`, `modules/climate_analysis/report_scanner.py`
- **Verantwortlichkeiten:** Zeitreihen, Zonen-Daten, Literatur-Scan
- **APIs:**
  - `GET /api/v1/analysis/series?source=` – Zeitreihe (alle Quellen außer zonal)
  - `GET /api/v1/analysis/zones?source=nasa_giss_zonal` – Zonale Daten
  - `GET /api/v1/admin/scan-topics` – Literatur-Scan-Themen
  - `POST /api/v1/admin/scan-reports` – Literatur-Scan starten

#### ReportScanner
- Sucht Fachartikel via **OpenAlex API** (kostenlos, kein Auth)
- Mit `ANTHROPIC_API_KEY`: Claude claude-sonnet-4-6 generiert deutschen Bericht, streng quellenbasiert
- Ohne API-Key: Regelbasierter Fallback – extrahiert Kernsätze, rahmt auf Deutsch ein
- 5 voreingestellte Themen zur Nordhalbkugel-Erwärmung

### 3. Visualization Engine
- **Branch:** `team/visualization`
- **Dateien:** `services/frontend/src/components/`
- **Komponenten:**
  - `ClimateSeriesChart` – universeller Zeitreihen-Chart
  - `TemperatureChart` – NASA GISS globale Anomalien
  - `GlobeView` – 3D-Globus mit zonaler Heatmap
- **GlobeView-Besonderheit:** Verwendet `getCentroidLat()` zur Lat-Berechnung aus GeoJSON-Polygonen, da das vasturiano-GeoJSON keine `LABEL_Y`/`LAT`-Properties hat
- **Anomalie-Anzeige:** Bezugszeitraum (Baseline) wird dynamisch aus API-Antwort gelesen
- **API:** `GET /api/v1/charts/{chart_id}`

### 4. Simulation Engine
- **Branch:** `team/simulation`
- **APIs:** `POST /api/v1/simulate`, `GET /api/v1/scenarios`

### 5. Knowledge Base
- **Branch:** `team/knowledge-base`
- **Datei:** `memory/knowledge_base.json`
- **Einträge:** co2_greenhouse_effect, mauna_loa_observatory, rcp_scenarios, co2_350ppm_safety
- **API:** `GET /api/v1/knowledge/{topic}`

### 6. AI Explanation System
- **Branch:** `team/ai-explanation`
- **Verantwortlichkeiten:** Datenpunkt-Erklärungen, KI-Chat
- **Modell:** `claude-sonnet-4-6`
- **APIs:**
  - `POST /api/v1/explain` – Erklärung für Datenpunkt
  - `POST /api/v1/chat` – Chat mit Klimakontext

### 7. REST API (Backend)
- **Branch:** `team/api`
- **Technologie:** FastAPI + uvicorn + SQLite
- **Port:** `8001`
- **Start:** `cd services/api && uvicorn main:app --host 0.0.0.0 --port 8001 --reload`
- **Docs:** `http://localhost:8001/docs`
- **Umgebungsvariablen:** `ANTHROPIC_API_KEY` (in `.env`, geladen via `python-dotenv`)

### 8. Frontend
- **Branch:** `team/frontend`
- **Technologie:** React 19 + Vite
- **Port:** `5173`
- **Start:** `cd services/frontend && npm run dev`
- **Admin-Panel-Tabs:**
  - Datenquellen (Import)
  - Berichte (gespeicherte Scans)
  - KI-Chat (ChatWidget)
  - Literatur-Scan (ReportScanner)

---

## LLM-Agenten

| Agent | Aufgabe | Endpunkt |
|---|---|---|
| ExplanationAgent | Erklärt Datenpunkte in einfacher Sprache | `POST /api/v1/explain` |
| ChatAgent | Klimaassistent mit Datenbankkontext | `POST /api/v1/chat` |
| ReportScanner | Literatursuche + deutscher KI-Bericht | `POST /api/v1/admin/scan-reports` |

---

## Git-Workflow

```
feature/* → develop (squash merge) → main (squash merge)
```

- Feature-Branches: `feature/[team]/[name]` oder `fix/[name]`
- Kein direkter Push auf `main` oder `develop`
- Branch-Protection wird für Merges temporär deaktiviert
