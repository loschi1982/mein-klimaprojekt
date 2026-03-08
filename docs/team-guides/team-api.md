# Team-Guide: API

## Dein Branch
`team/api`

## Aufgabe
Du baust das FastAPI-Backend: Routing, Datenbank-Zugriff, Authentifizierung und alle API-Endpunkte.

## WICHTIGE REGELN
1. Arbeite NUR in deinem Branch: `team/api`
2. Erstelle Feature-Branches nach Schema: `feature/api/[feature]`
3. Alle Endpunkte folgen dem Standard in `docs/api-contracts.md`
4. Dokumentiere Erkenntnisse in `memory/team_logs/api.log`

## Phase 1 – Aufgaben

### 1. FastAPI-Grundgerüst
```bash
git checkout -b feature/api/grundgeruest
```

Struktur unter `services/api/`:
```
services/api/
├── main.py          # FastAPI App
├── routers/         # Endpunkt-Router
├── models/          # Pydantic-Modelle
├── database.py      # SQLite-Verbindung
└── requirements.txt
```

### 2. Health-Check
- `GET /api/v1/health` → `{"status": "ok", "version": "1.0.0"}`

### 3. Erste Endpunkte (aus api-contracts.md)
- `GET /api/v1/datasets`
- `GET /api/v1/analysis/co2`

## Starten
```bash
cd services/api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API-Docs: http://localhost:8000/docs
