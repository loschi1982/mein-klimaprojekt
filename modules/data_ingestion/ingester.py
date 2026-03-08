"""
Data Ingestion Module – Kernlogik
Team-Branch: team/data-ingestion

Verantwortlich für: Datenabruf, Normalisierung, Speicherung
"""
import csv
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from .sources import SOURCES, get_source
from .validator import validate_csv, ValidationResult

RAW_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "raw"


# ── Download ──────────────────────────────────────────────────────────────────

def download_source(source_id: str, output_path: Path | None = None) -> Path:
    """Lädt Rohdaten einer bekannten Datenquelle herunter."""
    source = get_source(source_id)
    if output_path is None:
        output_path = RAW_DATA_DIR / f"{source_id}_raw.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(source.url, output_path)
    return output_path


def download_co2_mauna_loa(output_path: Path | None = None) -> Path:
    """Lädt CO₂-Monatsmittelwerte vom ESRL/Mauna Loa herunter."""
    return download_source("esrl_mauna_loa", output_path)


# ── Normalisierung ────────────────────────────────────────────────────────────

def _parse_esrl_csv(raw_path: Path, source_id: str) -> list[dict]:
    """
    Parst ESRL-CSV-Dateien (Kommentare mit #, Komma-getrennt).
    Schema: year, month, decimal_date, average, ...
    """
    rows = []
    ingested_at = datetime.now(timezone.utc).isoformat()
    source = get_source(source_id)

    with open(raw_path, newline="") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.strip().split(",")
            if len(parts) < 4:
                continue
            try:
                year = int(parts[0])
                month = int(parts[1])
                value = float(parts[3])
                if value < 0:
                    continue  # fehlende Werte (-99.99 o.ä.)
                rows.append({
                    "date": f"{year:04d}-{month:02d}-01",
                    "value": value,
                    "unit": source.unit,
                    "source": source_id,
                    "ingested_at": ingested_at,
                })
            except (ValueError, IndexError):
                continue
    return rows


def normalize_co2_mauna_loa(raw_path: Path, output_path: Path | None = None) -> Path:
    """Normalisiert die ESRL Mauna Loa CSV auf das Standard-Schema."""
    return _normalize_esrl(raw_path, "esrl_mauna_loa", output_path)


def _normalize_esrl(raw_path: Path, source_id: str, output_path: Path | None = None) -> Path:
    """Generischer Normalisierer für ESRL-Quellen."""
    if output_path is None:
        output_path = RAW_DATA_DIR / f"{source_id}.csv"

    rows = _parse_esrl_csv(raw_path, source_id)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["date", "value", "unit", "source", "ingested_at"]
        )
        writer.writeheader()
        writer.writerows(rows)

    return output_path


# ── Pipeline ──────────────────────────────────────────────────────────────────

def run_pipeline(source_id: str) -> dict:
    """
    Führt die vollständige Ingestion-Pipeline aus:
    Download → Normalisierung → Validierung
    Gibt ein Status-Dictionary zurück.
    """
    result = {
        "source": source_id,
        "status": "error",
        "raw_file": None,
        "normalized_file": None,
        "rows": 0,
        "validation": None,
        "errors": [],
    }

    try:
        raw = download_source(source_id)
        result["raw_file"] = raw.name

        normalized = _normalize_esrl(raw, source_id)
        result["normalized_file"] = normalized.name

        validation: ValidationResult = validate_csv(normalized)
        result["validation"] = {
            "valid": validation.valid,
            "rows": validation.row_count,
            "errors": validation.errors,
            "warnings": validation.warnings,
        }
        result["rows"] = validation.row_count

        if validation.valid:
            result["status"] = "done"
        else:
            result["status"] = "validation_failed"
            result["errors"] = validation.errors

    except Exception as e:
        result["errors"].append(str(e))

    return result


# ── Abfragen ──────────────────────────────────────────────────────────────────

def list_datasets() -> list[dict]:
    """Listet alle verfügbaren normalisierten Datensätze in data/raw/ auf."""
    if not RAW_DATA_DIR.exists():
        return []

    datasets = []
    for file in sorted(RAW_DATA_DIR.glob("*.csv")):
        if file.stem.endswith("_raw"):
            continue  # Rohdateien ausblenden
        row_count = max(sum(1 for _ in open(file)) - 1, 0)
        datasets.append({
            "id": file.stem,
            "file": file.name,
            "rows": row_count,
            "updated": datetime.fromtimestamp(
                file.stat().st_mtime, tz=timezone.utc
            ).isoformat(),
        })
    return datasets


def list_available_sources() -> list[dict]:
    """Listet alle konfigurierten Datenquellen auf."""
    return [
        {
            "id": s.id,
            "name": s.name,
            "format": s.format,
            "unit": s.unit,
            "description": s.description,
        }
        for s in SOURCES.values()
    ]
