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

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


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


# ── ESRL Parser ───────────────────────────────────────────────────────────────

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


def normalize_co2_mauna_loa(raw_path: Path, output_path: Path | None = None) -> Path:
    """Normalisiert die ESRL Mauna Loa CSV auf das Standard-Schema."""
    return _normalize_esrl(raw_path, "esrl_mauna_loa", output_path)


# ── NASA GISS Parser ──────────────────────────────────────────────────────────

def _parse_giss_csv(raw_path: Path, source_id: str) -> list[dict]:
    """
    Parst NASA GISS Temperatur-CSV.
    Format: Jahr-Zeilen mit monatlichen Anomalie-Werten (Hunderstel-Grad).
    Fehlende Werte: '***'
    """
    rows = []
    ingested_at = datetime.now(timezone.utc).isoformat()
    source = get_source(source_id)
    divide_by_100 = False
    header_found = False

    with open(raw_path, newline="") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue

            # Prüfe ob Werte durch 100 geteilt werden müssen
            if "Divide by 100" in stripped or "divide by 100" in stripped:
                divide_by_100 = True
                continue

            # Header-Zeile mit Monatsnamen finden
            if stripped.startswith("Year") and "Jan" in stripped:
                header_found = True
                continue

            if not header_found:
                continue

            parts = [p.strip() for p in stripped.split(",")]
            if len(parts) < 13:
                continue

            try:
                year = int(parts[0])
            except ValueError:
                continue

            for month_idx, month_str in enumerate(MONTHS, start=1):
                raw_val = parts[month_idx] if month_idx < len(parts) else "***"
                if raw_val in ("***", "", "nan"):
                    continue
                try:
                    value = float(raw_val)
                    if divide_by_100:
                        value = round(value / 100, 4)
                    rows.append({
                        "date": f"{year:04d}-{month_idx:02d}-01",
                        "value": value,
                        "unit": source.unit,
                        "source": source_id,
                        "ingested_at": ingested_at,
                    })
                except ValueError:
                    continue

    return rows


def _normalize_giss(raw_path: Path, source_id: str, output_path: Path | None = None) -> Path:
    """Normalisierer für NASA GISS-Quellen."""
    if output_path is None:
        output_path = RAW_DATA_DIR / f"{source_id}.csv"

    rows = _parse_giss_csv(raw_path, source_id)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["date", "value", "unit", "source", "ingested_at"]
        )
        writer.writeheader()
        writer.writerows(rows)

    return output_path


# ── NASA GISS Zonal Parser ────────────────────────────────────────────────────

# Zonen-Spalten in der ZonAnn.Ts+dSST.csv
GISS_ZONES = ["Glob", "NHem", "SHem", "24N-90N", "24S-24N", "90S-24S",
              "64N-90N", "44N-64N", "24N-44N", "EQU-24N", "24S-EQU",
              "44S-24S", "64S-44S", "90S-64S"]


def _parse_giss_zonal_csv(raw_path: Path) -> list[dict]:
    """
    Parst NASA GISS ZonAnn.Ts+dSST.csv.
    Gibt pro Jahr ein Dict mit allen Zonenwerten zurück.
    Werte in Hunderstel-Grad → Division durch 100.
    """
    rows = []
    divide_by_100 = False
    header_found = False
    zone_indices: list[int] = []

    with open(raw_path, newline="") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            if "Divide by 100" in stripped or "divide by 100" in stripped:
                divide_by_100 = True
                continue
            if stripped.startswith("Year") and "Glob" in stripped:
                header_found = True
                parts = [p.strip() for p in stripped.split(",")]
                zone_indices = [i for i, p in enumerate(parts) if p in GISS_ZONES]
                zone_names = [parts[i] for i in zone_indices]
                continue
            if not header_found:
                continue
            parts = [p.strip() for p in stripped.split(",")]
            try:
                year = int(parts[0])
            except ValueError:
                continue
            row = {"year": year}
            for idx, zone in zip(zone_indices, zone_names):
                raw_val = parts[idx] if idx < len(parts) else "***"
                if raw_val in ("***", "", "nan"):
                    row[zone] = None
                else:
                    try:
                        v = float(raw_val)
                        row[zone] = round(v / 100, 4) if divide_by_100 else round(v, 4)
                    except ValueError:
                        row[zone] = None
            rows.append(row)
    return rows


def _normalize_giss_zonal(raw_path: Path, output_path: Path | None = None) -> Path:
    """Normalisierer für NASA GISS Zonaldaten – speichert als JSON."""
    import json
    if output_path is None:
        output_path = RAW_DATA_DIR / "nasa_giss_zonal.json"

    rows = _parse_giss_zonal_csv(raw_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump({"zones": GISS_ZONES, "data": rows}, f, separators=(",", ":"))

    return output_path


# ── Berkeley Earth Parser ────────────────────────────────────────────────────

def _parse_berkeley_earth(raw_path: Path, source_id: str) -> list[dict]:
    """
    Parst Berkeley Earth Land+Ocean Complete.
    Format: %-Kommentare, Leerzeichen-getrennt: Year Month Anomaly Uncertainty ...
    Fehlende Werte: NaN
    """
    rows = []
    ingested_at = datetime.now(timezone.utc).isoformat()
    source = get_source(source_id)
    header_passed = False

    with open(raw_path, newline="", encoding="utf-8", errors="replace") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("%"):
                if "Year" in stripped and "Month" in stripped:
                    header_passed = True
                continue
            if not header_passed:
                continue
            parts = stripped.split()
            if len(parts) < 3:
                continue
            try:
                year = int(parts[0])
                month = int(parts[1])
                value_str = parts[2]
                if value_str.lower() == "nan":
                    continue
                value = float(value_str)
                rows.append({
                    "date": f"{year:04d}-{month:02d}-01",
                    "value": round(value, 4),
                    "unit": source.unit,
                    "source": source_id,
                    "ingested_at": ingested_at,
                })
            except (ValueError, IndexError):
                continue
    return rows


def _normalize_berkeley_earth(raw_path: Path, source_id: str, output_path: Path | None = None) -> Path:
    """Normalisierer für Berkeley Earth Temperatur-Daten."""
    if output_path is None:
        output_path = RAW_DATA_DIR / f"{source_id}.csv"

    rows = _parse_berkeley_earth(raw_path, source_id)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["date", "value", "unit", "source", "ingested_at"]
        )
        writer.writeheader()
        writer.writerows(rows)

    return output_path


# ── CSIRO Sea Level Parser ────────────────────────────────────────────────────

def _parse_sea_level(raw_path: Path, source_id: str) -> list[dict]:
    """
    Parst CSIRO Church & White globalen Meeresspiegel.
    Format: Semikolon-getrennt, Dezimaljahr; GMSL (mm)
    Kommentare: Zeilen die nicht mit Ziffer beginnen.
    """
    rows = []
    ingested_at = datetime.now(timezone.utc).isoformat()
    source = get_source(source_id)

    with open(raw_path, newline="", encoding="utf-8", errors="replace") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            # Kommentar- und Header-Zeilen überspringen
            if not stripped[0].isdigit():
                continue
            # Trennzeichen: Semikolon oder Komma
            sep = ";" if ";" in stripped else ","
            parts = [p.strip() for p in stripped.split(sep)]
            if len(parts) < 2:
                continue
            try:
                decimal_year = float(parts[0])
                value = float(parts[1])
                # Dezimaljahr → Kalendermonat
                year = int(decimal_year)
                month = max(1, min(12, int((decimal_year - year) * 12) + 1))
                rows.append({
                    "date": f"{year:04d}-{month:02d}-01",
                    "value": round(value, 2),
                    "unit": source.unit,
                    "source": source_id,
                    "ingested_at": ingested_at,
                })
            except (ValueError, IndexError):
                continue
    return rows


def _normalize_sea_level(raw_path: Path, source_id: str, output_path: Path | None = None) -> Path:
    """Normalisierer für CSIRO Meeresspiegel-Daten."""
    if output_path is None:
        output_path = RAW_DATA_DIR / f"{source_id}.csv"

    rows = _parse_sea_level(raw_path, source_id)
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
        source = get_source(source_id)
        raw = download_source(source_id)
        result["raw_file"] = raw.name

        if source.parser == "giss":
            normalized = _normalize_giss(raw, source_id)
        elif source.parser == "giss_zonal":
            normalized = _normalize_giss_zonal(raw)
        elif source.parser == "berkeley_earth":
            normalized = _normalize_berkeley_earth(raw, source_id)
        elif source.parser == "sea_level":
            normalized = _normalize_sea_level(raw, source_id)
        else:
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
            continue
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
            "source_url": s.source_url,
        }
        for s in SOURCES.values()
    ]
