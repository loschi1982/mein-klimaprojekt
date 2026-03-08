# Team-Guide: Data Ingestion

## Dein Branch
`team/data-ingestion`

## Aufgabe
Du holst Klimadaten von externen Quellen, normalisierst sie und speicherst sie in `data/raw/`.

## WICHTIGE REGELN
1. Arbeite NUR in deinem Branch: `team/data-ingestion`
2. Erstelle Feature-Branches nach Schema: `feature/data-ingestion/[feature]`
3. Committe regelmäßig mit aussagekräftigen Messages
4. Dokumentiere alle Erkenntnisse in `memory/team_logs/data-ingestion.log`
5. Aktualisiere `project_memory.json` nach jedem Meilenstein
6. Öffne Pull Requests nach `develop`, NICHT nach `main`

## Phase 1 – Aufgaben

### 1. CO₂-Daten von ESRL/Mauna Loa
```bash
git checkout -b feature/data-ingestion/co2-mauna-loa
```
- URL: https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_mlo.csv
- Speichere in: `data/raw/co2_mauna_loa.csv`
- Normalisiere auf Schema: `date (ISO8601), value (float), unit (ppm)`

### 2. API-Endpunkte implementieren
- `POST /api/v1/ingest` – Datenabruf starten
- `GET /api/v1/datasets` – Datensätze auflisten

## Datenquellen

| Quelle | URL | Format |
|---|---|---|
| ESRL Mauna Loa CO₂ | https://gml.noaa.gov/ccgg/trends/ | CSV |
| NOAA NCEI Temperatur | https://www.ncei.noaa.gov/access/search/data-search/global-summary-of-the-month | REST/JSON |
| NSIDC Arktis-Eis | https://nsidc.org/data/seaice_index/ | CSV/NetCDF |
| Copernicus ERA5 | https://cds.climate.copernicus.eu/ | REST/NetCDF |

## Datei-Schema (`data/raw/`)

Alle Rohdaten werden als CSV mit diesen Pflichtfeldern gespeichert:
```
date,value,unit,source,ingested_at
2024-03-01,421.5,ppm,esrl_mauna_loa,2026-03-08T00:00:00Z
```

## Fortschritt melden
```bash
python scripts/update_memory.py --team data-ingestion --task "co2-download" --status done
git add memory/ && git commit -m "memory: update data-ingestion progress"
```
