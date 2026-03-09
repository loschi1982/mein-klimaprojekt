# API-Verträge

Alle APIs folgen diesem einheitlichen Standard.

## Antwort-Format

```json
{
  "data": {},
  "meta": {
    "timestamp": "ISO8601",
    "version": "1.0.0"
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

## System

### `GET /api/v1/health`
Gibt den Server-Status zurück.

**Response (200):**
```json
{
  "data": { "status": "ok", "version": "1.0.0" },
  "meta": { "timestamp": "2026-03-09T00:00:00Z", "version": "1.0.0" }
}
```

---

## Data Ingestion

### `GET /api/v1/datasets`
Listet alle importierten Datensätze auf.

**Response (200):**
```json
{
  "data": [
    { "id": "co2_mauna_loa", "file": "co2_mauna_loa.csv", "rows": 816, "updated": "2026-03-09T00:00:00Z" }
  ],
  "meta": { "timestamp": "2026-03-09T00:00:00Z", "version": "1.0.0" }
}
```

### `POST /api/v1/ingest`
Startet einen neuen Datenabruf.

**Request:**
```json
{ "source": "co2_mauna_loa" }
```

**Response (200):**
```json
{
  "data": { "source": "co2_mauna_loa", "status": "done", "rows": 816 },
  "meta": { "timestamp": "2026-03-09T00:00:00Z", "version": "1.0.0" }
}
```

---

## Climate Analysis

### `GET /api/v1/analysis/series`
Gibt eine Zeitreihe für eine Datenquelle zurück.

**Query-Parameter:** `?source=co2_mauna_loa`

Verfügbare `source`-Werte: `co2_mauna_loa`, `esrl_co2_global`, `esrl_ch4`, `berkeley_earth_global`, `csiro_sea_level`, `nasa_giss_global`

**Response (200):**
```json
{
  "data": {
    "source": "nasa_giss_global",
    "unit": "°C",
    "baseline": "1951–1980",
    "series": [
      { "date": "1880-01", "value": -0.16 }
    ]
  },
  "meta": { "timestamp": "2026-03-09T00:00:00Z", "version": "1.0.0" }
}
```

> **Hinweis:** Das Feld `baseline` ist nur vorhanden, wenn die Quelle Anomalie-Werte liefert (NASA GISS, Berkeley Earth, CSIRO).

### `GET /api/v1/analysis/zones`
Gibt zonale Temperaturdaten (NASA GISS Zonal) zurück.

**Query-Parameter:** `?source=nasa_giss_zonal`

**Response (200):**
```json
{
  "data": {
    "source": "nasa_giss_zonal",
    "zones": { "64N-90N": [...], "44N-64N": [...] },
    "years": [1880, 1881, "..."]
  },
  "meta": { "timestamp": "2026-03-09T00:00:00Z", "version": "1.0.0" }
}
```

---

## Visualization

### `GET /api/v1/charts/{chart_id}`
Gibt Chart-Konfiguration zurück.

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
  "meta": { "timestamp": "2026-03-09T00:00:00Z", "version": "1.0.0" }
}
```

---

## Simulation

### `GET /api/v1/scenarios`
Listet verfügbare Klimaszenarien auf.

### `POST /api/v1/simulate`
Startet eine Klimasimulation.

**Request:**
```json
{
  "scenario": "rcp45",
  "years": 50,
  "parameters": { "co2_growth_rate": 1.5 }
}
```

---

## Knowledge Base

### `GET /api/v1/knowledge/{topic}`
Gibt Wissen zu einem Thema zurück.

**Beispiel:** `GET /api/v1/knowledge/co2_greenhouse_effect`

**Response (200):**
```json
{
  "data": {
    "id": "co2_greenhouse_effect",
    "title": "CO₂ als Treibhausgas",
    "content": "...",
    "facts": ["..."],
    "sources": ["IPCC AR6"],
    "tags": ["co2"]
  },
  "meta": { "timestamp": "2026-03-09T00:00:00Z", "version": "1.0.0" }
}
```

---

## AI Explanation

### `POST /api/v1/explain`
Generiert eine Claude-basierte Erklärung für einen Datenpunkt.

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
    "explanation": "Der CO₂-Wert von 421.5 ppm...",
    "confidence": "high",
    "sources": ["ESRL Mauna Loa"]
  },
  "meta": { "timestamp": "2026-03-09T00:00:00Z", "version": "1.0.0" }
}
```

### `POST /api/v1/chat`
KI-Chat mit Klimakontext (Claude claude-sonnet-4-6).

**Request:**
```json
{
  "message": "Warum erwärmt sich die Nordhalbkugel schneller?",
  "history": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ]
}
```

**Response (200):**
```json
{
  "data": { "reply": "Die Nordhalbkugel erwärmt sich schneller, weil..." },
  "meta": { "timestamp": "2026-03-09T00:00:00Z", "version": "1.0.0" }
}
```

---

## Admin

### `GET /api/v1/admin/sources`
Listet alle verfügbaren Importquellen auf.

**Response (200):**
```json
{
  "data": {
    "sources": [
      { "id": "co2_mauna_loa", "name": "ESRL/GML Mauna Loa CO₂", "url": "..." }
    ]
  },
  "meta": { "timestamp": "2026-03-09T00:00:00Z", "version": "1.0.0" }
}
```

### `POST /api/v1/admin/import`
Importiert eine Datenquelle manuell.

**Request:**
```json
{ "source_id": "nasa_giss_global" }
```

### `GET /api/v1/admin/scan-topics`
Gibt vordefinierte Literatur-Scan-Themen zurück.

**Response (200):**
```json
{
  "data": {
    "topics": [
      { "label": "Arktische Verstärkung (Arctic Amplification)", "query": "Arctic amplification Northern Hemisphere..." }
    ]
  },
  "meta": { "timestamp": "2026-03-09T00:00:00Z", "version": "1.0.0" }
}
```

### `POST /api/v1/admin/scan-reports`
Startet einen Literatur-Scan via OpenAlex und generiert einen deutschen KI-Bericht.

**Request:**
```json
{ "topic": "Arctic amplification Northern Hemisphere", "max_papers": 5 }
```

**Response (200):**
```json
{
  "data": {
    "topic": "Arctic amplification...",
    "summary": "## Wissenschaftlicher Überblick...",
    "used_llm": true,
    "scanned_at": "2026-03-09T00:00:00Z",
    "papers": [
      {
        "title": "Arctic Amplification Study",
        "authors": ["Jane Smith"],
        "year": 2022,
        "url": "https://doi.org/...",
        "doi": "https://doi.org/...",
        "abstract": "..."
      }
    ]
  },
  "meta": { "timestamp": "2026-03-09T00:00:00Z", "version": "1.0.0" }
}
```

> **Hinweis:** `used_llm: true` wenn `ANTHROPIC_API_KEY` gesetzt ist, sonst regelbasierte deutsche Zusammenfassung.
