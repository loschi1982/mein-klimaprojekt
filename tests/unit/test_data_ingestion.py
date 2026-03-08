"""Unit Tests für das Data Ingestion Module"""
import csv
import tempfile
from pathlib import Path

import pytest

from modules.data_ingestion.ingester import (
    normalize_co2_mauna_loa,
    list_datasets,
    list_available_sources,
    _parse_esrl_csv,
)
from modules.data_ingestion.sources import get_source, SOURCES
from modules.data_ingestion.validator import validate_csv, _valid_date


# ── Fixtures ──────────────────────────────────────────────────────────────────

SAMPLE_RAW_CSV = """\
# This file contains a record length of 8 fields separated by whitespace.
# Field 1: year
# Field 2: month
# ...
year,month,decimal_date,average,average_unc,trend,trend_unc,#days
1958,3,1958.2055,-99.99,-9.99,314.44,-0.20,-1
1958,4,1958.2877,317.45,0.13,315.16,0.12,25
2024,3,2024.2055,421.50,0.10,419.30,0.10,28
"""


def make_raw_file(content: str) -> Path:
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False)
    tmp.write(content)
    tmp.flush()
    return Path(tmp.name)


# ── Normalisierung ────────────────────────────────────────────────────────────

def test_normalize_co2_skips_comments():
    raw = make_raw_file(SAMPLE_RAW_CSV)
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "co2.csv"
        normalize_co2_mauna_loa(raw, out)
        rows = list(csv.DictReader(open(out)))
    assert all(float(r["value"]) > 0 for r in rows)


def test_normalize_co2_correct_schema():
    raw = make_raw_file(SAMPLE_RAW_CSV)
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "co2.csv"
        normalize_co2_mauna_loa(raw, out)
        rows = list(csv.DictReader(open(out)))
    assert len(rows) == 2
    assert rows[0]["date"] == "1958-04-01"
    assert rows[0]["unit"] == "ppm"
    assert rows[0]["source"] == "esrl_mauna_loa"
    assert float(rows[1]["value"]) == pytest.approx(421.50)


def test_normalize_co2_filters_missing_values():
    raw = make_raw_file(SAMPLE_RAW_CSV)
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "co2.csv"
        normalize_co2_mauna_loa(raw, out)
        rows = list(csv.DictReader(open(out)))
    dates = [r["date"] for r in rows]
    assert "1958-03-01" not in dates


def test_normalize_co2_date_format():
    raw = make_raw_file(SAMPLE_RAW_CSV)
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "co2.csv"
        normalize_co2_mauna_loa(raw, out)
        rows = list(csv.DictReader(open(out)))
    for row in rows:
        parts = row["date"].split("-")
        assert len(parts) == 3
        assert len(parts[0]) == 4  # YYYY
        assert len(parts[1]) == 2  # MM
        assert len(parts[2]) == 2  # DD


def test_normalize_co2_ingested_at_present():
    raw = make_raw_file(SAMPLE_RAW_CSV)
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "co2.csv"
        normalize_co2_mauna_loa(raw, out)
        rows = list(csv.DictReader(open(out)))
    assert all(r["ingested_at"] for r in rows)


# ── Parser ────────────────────────────────────────────────────────────────────

def test_parse_esrl_csv_skips_empty_lines():
    content = "\n\nyear,month,decimal_date,average\n1958,4,1958.2877,317.45\n\n"
    raw = make_raw_file(content)
    rows = _parse_esrl_csv(raw, "esrl_mauna_loa")
    assert len(rows) == 1


def test_parse_esrl_csv_handles_malformed_lines():
    # "bad line" hat zu wenige Felder → wird übersprungen
    # "1958,4,malformed,317.45" → Felder 0,1,3 sind valide → wird akzeptiert
    content = "year,month,decimal_date,average\n1958,4,malformed,317.45\nbad line\n1960,1,1960.0,315.0\n"
    raw = make_raw_file(content)
    rows = _parse_esrl_csv(raw, "esrl_mauna_loa")
    assert len(rows) == 2
    assert rows[0]["date"] == "1958-04-01"
    assert rows[1]["date"] == "1960-01-01"


# ── Datenquellen ──────────────────────────────────────────────────────────────

def test_sources_not_empty():
    assert len(SOURCES) >= 1


def test_get_source_known():
    source = get_source("esrl_mauna_loa")
    assert source.id == "esrl_mauna_loa"
    assert source.unit == "ppm"
    assert source.url.startswith("https://")


def test_get_source_unknown():
    with pytest.raises(ValueError, match="Unbekannte Datenquelle"):
        get_source("nicht_vorhanden")


def test_list_available_sources():
    sources = list_available_sources()
    assert len(sources) >= 1
    assert all("id" in s and "name" in s and "unit" in s for s in sources)


# ── Datensätze auflisten ──────────────────────────────────────────────────────

def test_list_datasets_empty_dir():
    with tempfile.TemporaryDirectory() as d:
        import modules.data_ingestion.ingester as ing
        original = ing.RAW_DATA_DIR
        ing.RAW_DATA_DIR = Path(d)
        result = list_datasets()
        ing.RAW_DATA_DIR = original
    assert result == []


def test_list_datasets_with_file():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "test.csv").write_text("date,value\n2024-01-01,400\n")
        import modules.data_ingestion.ingester as ing
        original = ing.RAW_DATA_DIR
        ing.RAW_DATA_DIR = Path(d)
        result = list_datasets()
        ing.RAW_DATA_DIR = original
    assert len(result) == 1
    assert result[0]["id"] == "test"
    assert result[0]["rows"] == 1


def test_list_datasets_excludes_raw_files():
    with tempfile.TemporaryDirectory() as d:
        (Path(d) / "co2.csv").write_text("date,value\n2024-01-01,400\n")
        (Path(d) / "co2_raw.csv").write_text("raw,data\n1,2\n")
        import modules.data_ingestion.ingester as ing
        original = ing.RAW_DATA_DIR
        ing.RAW_DATA_DIR = Path(d)
        result = list_datasets()
        ing.RAW_DATA_DIR = original
    ids = [r["id"] for r in result]
    assert "co2" in ids
    assert "co2_raw" not in ids


# ── Validator ─────────────────────────────────────────────────────────────────

def test_validate_csv_valid():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "ok.csv"
        p.write_text(
            "date,value,unit,source,ingested_at\n"
            "2024-01-01,421.5,ppm,esrl_mauna_loa,2026-03-08T00:00:00Z\n"
        )
        result = validate_csv(p)
    assert result.valid
    assert result.row_count == 1
    assert result.errors == []


def test_validate_csv_missing_column():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "bad.csv"
        p.write_text("date,value\n2024-01-01,421.5\n")
        result = validate_csv(p)
    assert not result.valid
    assert any("Fehlende Pflichtfelder" in e for e in result.errors)


def test_validate_csv_invalid_date():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "bad_date.csv"
        p.write_text(
            "date,value,unit,source,ingested_at\n"
            "2024-13-01,421.5,ppm,src,2026-01-01T00:00:00Z\n"
        )
        result = validate_csv(p)
    assert not result.valid
    assert any("Datum" in e for e in result.errors)


def test_validate_csv_non_numeric_value():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "bad_val.csv"
        p.write_text(
            "date,value,unit,source,ingested_at\n"
            "2024-01-01,NOT_A_NUMBER,ppm,src,2026-01-01T00:00:00Z\n"
        )
        result = validate_csv(p)
    assert not result.valid


def test_validate_csv_file_not_found():
    result = validate_csv(Path("/tmp/does_not_exist_xyz.csv"))
    assert not result.valid
    assert any("nicht gefunden" in e for e in result.errors)


# ── Datums-Hilfsfunktion ──────────────────────────────────────────────────────

@pytest.mark.parametrize("date,expected", [
    ("2024-01-01", True),
    ("1958-04-01", True),
    ("2100-12-31", True),
    ("2024-13-01", False),   # Monat 13
    ("2024-00-01", False),   # Monat 0
    ("2024-01-32", False),   # Tag 32
    ("24-01-01", False),     # Kurzes Jahr
    ("not-a-date", False),
    ("", False),
])
def test_valid_date(date, expected):
    assert _valid_date(date) == expected
