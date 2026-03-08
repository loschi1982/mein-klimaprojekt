"""
Data Ingestion Module
Team-Branch: team/data-ingestion

Verantwortlich für: Datenabruf, Normalisierung, Speicherung
"""
import csv
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


RAW_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "raw"


def download_co2_mauna_loa(output_path: Path | None = None) -> Path:
    """
    Lädt CO₂-Monatsmittelwerte vom ESRL/Mauna Loa herunter.
    Quelle: https://gml.noaa.gov/ccgg/trends/
    """
    url = "https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_mlo.csv"
    if output_path is None:
        output_path = RAW_DATA_DIR / "co2_mauna_loa_raw.csv"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, output_path)
    return output_path


def normalize_co2_mauna_loa(raw_path: Path, output_path: Path | None = None) -> Path:
    """
    Normalisiert die ESRL-CSV auf das Standard-Schema:
    date (ISO8601), value (float), unit (str), source (str), ingested_at (ISO8601)
    """
    if output_path is None:
        output_path = RAW_DATA_DIR / "co2_mauna_loa.csv"

    rows = []
    ingested_at = datetime.now(timezone.utc).isoformat()

    with open(raw_path, newline="") as f:
        for line in f:
            # Kommentarzeilen überspringen
            if line.startswith("#"):
                continue
            parts = line.strip().split(",")
            if len(parts) < 4:
                continue
            try:
                year = int(parts[0])
                month = int(parts[1])
                value = float(parts[3])  # monatlicher Mittelwert
                if value < 0:
                    continue  # fehlende Werte markiert mit -99.99
                date = f"{year:04d}-{month:02d}-01"
                rows.append({
                    "date": date,
                    "value": value,
                    "unit": "ppm",
                    "source": "esrl_mauna_loa",
                    "ingested_at": ingested_at,
                })
            except (ValueError, IndexError):
                continue

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["date", "value", "unit", "source", "ingested_at"])
        writer.writeheader()
        writer.writerows(rows)

    return output_path


def list_datasets() -> list[dict]:
    """Listet alle verfügbaren Rohdatensätze in data/raw/ auf."""
    datasets = []
    if not RAW_DATA_DIR.exists():
        return datasets

    for file in RAW_DATA_DIR.glob("*.csv"):
        row_count = sum(1 for _ in open(file)) - 1  # Header abziehen
        datasets.append({
            "id": file.stem,
            "file": file.name,
            "rows": max(row_count, 0),
            "updated": datetime.fromtimestamp(file.stat().st_mtime, tz=timezone.utc).isoformat(),
        })
    return datasets
