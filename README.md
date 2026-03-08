# Klimadaten-Projekt

Ein KI-gestütztes Multi-Team-Projekt zur Analyse, Visualisierung und Erklärung von Klimadaten.

## Architektur

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

## Schnellstart

```bash
# 1. Repository klonen
git clone https://github.com/[user]/mein-klimaprojekt.git
cd mein-klimaprojekt

# 2. Setup-Skript ausführen
chmod +x scripts/setup.sh
./scripts/setup.sh

# 3. Alle Server starten
./scripts/run_dev.sh
```

Nach dem Start erreichbar:
- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API-Dokumentation:** http://localhost:8000/docs

## Teams & Branches

| Team | Branch | Aufgabe | Phase |
|---|---|---|---|
| Data Ingestion | `team/data-ingestion` | Datenabruf, Normalisierung | 1 |
| Climate Analysis | `team/climate-analysis` | Analyse, Statistik, Trends | 1 |
| Visualization | `team/visualization` | Charts, Karten, UI-Komponenten | 1 |
| Simulation | `team/simulation` | Szenario-Simulationen | 2 |
| Knowledge Base | `team/knowledge-base` | Wissensstruktur, Gedächtnis | 2 |
| AI Explanation | `team/ai-explanation` | Claude-Integration, Erklärungen | 2 |
| Frontend | `team/frontend` | Gesamte React-App, Routing | 1 |
| API | `team/api` | FastAPI, Endpunkte, Auth | 1 |

## Technologie-Stack

| Bereich | Technologie |
|---|---|
| Frontend | React + Vite |
| Backend | FastAPI (Python) |
| Datenpipeline | Python + Pandas |
| Datenanalyse | NumPy + SciPy |
| Visualisierung | Plotly + Chart.js |
| KI-Integration | Anthropic API (Claude) |
| Datenbank | SQLite → PostgreSQL |
| Testing | pytest + Jest |

## Weitere Dokumentation

- [Systemarchitektur](docs/architecture.md)
- [API-Verträge](docs/api-contracts.md)
- [Team-Anleitungen](docs/team-guides/)
