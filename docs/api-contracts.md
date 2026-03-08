# API-Verträge

Alle APIs folgen diesem einheitlichen Standard.

## Antwort-Format

```json
{
  "version": "v1",
  "endpoint": "/api/v1/[resource]",
  "method": "GET | POST | PUT | DELETE",
  "request": {
    "headers": { "Content-Type": "application/json" },
    "body": {}
  },
  "response": {
    "success": {
      "status": 200,
      "data": {},
      "meta": {
        "timestamp": "ISO8601",
        "version": "1.0.0"
      }
    },
    "error": {
      "status": 400,
      "error": {
        "code": "ERROR_CODE",
        "message": "Beschreibung",
        "details": {}
      }
    }
  }
}
```

## Fehlercodes

| Code | HTTP Status | Bedeutung |
|---|---|---|
| `DATA_NOT_FOUND` | 404 | Datensatz nicht gefunden |
| `INVALID_PARAMS` | 400 | Ungültige Parameter |
| `PROCESSING_ERROR` | 500 | Interner Verarbeitungsfehler |
| `RATE_LIMIT` | 429 | Zu viele Anfragen |
| `AUTH_REQUIRED` | 401 | Authentifizierung erforderlich |

---

## Endpunkte

### Data Ingestion (`team/data-ingestion`)

#### `POST /api/v1/ingest`
Startet einen neuen Datenabruf.

**Request:**
```json
{
  "source": "esrl_mauna_loa",
  "date_from": "2020-01-01",
  "date_to": "2024-12-31"
}
```

**Response (200):**
```json
{
  "data": { "job_id": "abc123", "status": "queued" },
  "meta": { "timestamp": "2026-03-08T00:00:00Z", "version": "1.0.0" }
}
```

#### `GET /api/v1/datasets`
Listet alle verfügbaren Datensätze auf.

**Response (200):**
```json
{
  "data": [
    { "id": "co2_mauna_loa", "source": "ESRL", "rows": 12000, "updated": "2026-03-08" }
  ],
  "meta": { "timestamp": "2026-03-08T00:00:00Z", "version": "1.0.0" }
}
```

---

### Climate Analysis (`team/climate-analysis`)

#### `GET /api/v1/analysis/co2`
Gibt CO₂-Trenddaten zurück.

**Query-Parameter:** `?from=2020-01-01&to=2024-12-31&interval=monthly`

**Response (200):**
```json
{
  "data": {
    "unit": "ppm",
    "series": [
      { "date": "2020-01", "value": 413.5 }
    ],
    "trend": { "slope": 2.4, "r_squared": 0.99 }
  },
  "meta": { "timestamp": "2026-03-08T00:00:00Z", "version": "1.0.0" }
}
```

#### `GET /api/v1/analysis/temperature`
Gibt globale Temperaturdaten zurück.

---

### Visualization (`team/visualization`)

#### `GET /api/v1/charts/{chart_id}`
Gibt Chart-Konfiguration und Daten zurück.

**Response (200):**
```json
{
  "data": {
    "chart_id": "co2_timeseries",
    "type": "line",
    "title": "CO₂-Konzentration (Mauna Loa)",
    "x_label": "Jahr",
    "y_label": "ppm",
    "series": []
  },
  "meta": { "timestamp": "2026-03-08T00:00:00Z", "version": "1.0.0" }
}
```

---

### Simulation (`team/simulation`)

#### `POST /api/v1/simulate`
Startet eine Klimasimulation.

**Request:**
```json
{
  "scenario": "rcp45",
  "years": 50,
  "parameters": { "co2_growth_rate": 1.5 }
}
```

#### `GET /api/v1/scenarios`
Listet verfügbare Szenarien auf.

---

### Knowledge Base (`team/knowledge-base`)

#### `GET /api/v1/knowledge/{topic}`
Gibt Wissen zu einem Thema zurück.

**Beispiel:** `GET /api/v1/knowledge/co2_greenhouse_effect`

---

### AI Explanation (`team/ai-explanation`)

#### `POST /api/v1/explain`
Generiert eine natürlichsprachliche Erklärung via Claude.

**Request:**
```json
{
  "data_point": { "type": "co2", "value": 421.5, "date": "2024-03" },
  "question": "Warum ist dieser Wert so hoch?"
}
```

**Response (200):**
```json
{
  "data": {
    "explanation": "Der CO₂-Wert von 421.5 ppm im März 2024...",
    "confidence": "high",
    "sources": ["ESRL Mauna Loa"]
  },
  "meta": { "timestamp": "2026-03-08T00:00:00Z", "version": "1.0.0" }
}
```
