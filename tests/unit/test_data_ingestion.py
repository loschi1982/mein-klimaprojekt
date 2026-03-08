"""Unit Tests für das Data Ingestion Module"""
import csv
import json
import tempfile
from pathlib import Path

import pytest

from modules.data_ingestion.ingester import (
    normalize_co2_mauna_loa,
    list_datasets,
    list_available_sources,
    _parse_esrl_csv,
    _parse_giss_csv,
    _parse_giss_zonal_csv,
    _normalize_giss_zonal,
    GISS_ZONES,
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


# ── Pipeline ──────────────────────────────────────────────────────────────────

def test_run_pipeline_unknown_source():
    from modules.data_ingestion.ingester import run_pipeline
    result = run_pipeline("nicht_vorhanden")
    assert result["status"] == "error"
    assert len(result["errors"]) > 0


def test_run_pipeline_structure():
    from modules.data_ingestion.ingester import run_pipeline
    result = run_pipeline("nicht_vorhanden")
    assert "source" in result
    assert "status" in result
    assert "errors" in result
    assert "rows" in result


def test_normalize_esrl_creates_file():
    raw = make_raw_file(SAMPLE_RAW_CSV)
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "output.csv"
        from modules.data_ingestion.ingester import _normalize_esrl
        result = _normalize_esrl(raw, "esrl_mauna_loa", out)
        assert result.exists()
        assert result.stat().st_size > 0


def test_normalize_esrl_row_count():
    raw = make_raw_file(SAMPLE_RAW_CSV)
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "output.csv"
        from modules.data_ingestion.ingester import _normalize_esrl
        _normalize_esrl(raw, "esrl_mauna_loa", out)
        rows = list(csv.DictReader(open(out)))
    assert len(rows) == 2  # -99.99 und Kommentare herausgefiltert


# ── NASA GISS Parser ──────────────────────────────────────────────────────────

SAMPLE_GISS_CSV = """\
Global-mean monthly, seasonal, and annual means, 1880-present
Divide by 100 to convert to degrees Celsius
Year,Jan,Feb,Mar,Apr,May,Jun,Jul,Aug,Sep,Oct,Nov,Dec,J-D,D-N,DJF,MAM,JJA,SON
2020, 138, 188, 194, 146, 120, 123, 107, 113, 106, 118, 148, 150, 138, ***,  ***,  153,  114,  124
2021, 102,  90,  87,  74,  95,  73,  91, 109, 104, 114, 128, 158,  94, 102,  146,   85,   91,  115
"""

SAMPLE_GISS_ZONAL_CSV = """\
GISS Surface Temperature Analysis (GISTEMP v4)
Divide by 100 to convert to degrees Celsius
Year,Glob,NHem,SHem,24N-90N,24S-24N,90S-24S,64N-90N,44N-64N,24N-44N,EQU-24N,24S-EQU,44S-24S,64S-44S,90S-64S
2020,102,125,79,155,82,58,210,140,120,75,70,55,50,40
2021,94,118,70,148,76,51,200,132,112,68,63,48,43,33
"""


def test_parse_giss_csv_divide_by_100():
    raw = make_raw_file(SAMPLE_GISS_CSV)
    rows = _parse_giss_csv(raw, "nasa_giss_global")
    # 2020 hat 12 gültige Monate, 2021 hat 12 gültige Monate
    assert len(rows) == 24
    jan2020 = next(r for r in rows if r["date"] == "2020-01-01")
    assert jan2020["value"] == pytest.approx(1.38)


def test_parse_giss_csv_unit():
    raw = make_raw_file(SAMPLE_GISS_CSV)
    rows = _parse_giss_csv(raw, "nasa_giss_global")
    assert all(r["unit"] == "°C" for r in rows)


def test_parse_giss_csv_source():
    raw = make_raw_file(SAMPLE_GISS_CSV)
    rows = _parse_giss_csv(raw, "nasa_giss_global")
    assert all(r["source"] == "nasa_giss_global" for r in rows)


def test_parse_giss_csv_date_format():
    raw = make_raw_file(SAMPLE_GISS_CSV)
    rows = _parse_giss_csv(raw, "nasa_giss_global")
    for r in rows:
        parts = r["date"].split("-")
        assert len(parts) == 3


def test_parse_giss_csv_skips_missing():
    content = (
        "Divide by 100 to convert to degrees Celsius\n"
        "Year,Jan,Feb,Mar,Apr,May,Jun,Jul,Aug,Sep,Oct,Nov,Dec\n"
        "2020, ***, 100, ***, 100, 100, 100, 100, 100, 100, 100, 100, 100\n"
    )
    raw = make_raw_file(content)
    rows = _parse_giss_csv(raw, "nasa_giss_global")
    dates = [r["date"] for r in rows]
    assert "2020-01-01" not in dates
    assert "2020-02-01" in dates


# ── NASA GISS Zonal Parser ─────────────────────────────────────────────────────

def test_giss_zones_list():
    assert "Glob" in GISS_ZONES
    assert "64N-90N" in GISS_ZONES
    assert "90S-64S" in GISS_ZONES
    assert len(GISS_ZONES) == 14


def test_parse_giss_zonal_csv_row_count():
    raw = make_raw_file(SAMPLE_GISS_ZONAL_CSV)
    rows = _parse_giss_zonal_csv(raw)
    assert len(rows) == 2


def test_parse_giss_zonal_csv_year():
    raw = make_raw_file(SAMPLE_GISS_ZONAL_CSV)
    rows = _parse_giss_zonal_csv(raw)
    years = [r["year"] for r in rows]
    assert 2020 in years
    assert 2021 in years


def test_parse_giss_zonal_csv_divide_by_100():
    raw = make_raw_file(SAMPLE_GISS_ZONAL_CSV)
    rows = _parse_giss_zonal_csv(raw)
    row2020 = next(r for r in rows if r["year"] == 2020)
    assert row2020["Glob"] == pytest.approx(1.02)
    assert row2020["64N-90N"] == pytest.approx(2.10)


def test_parse_giss_zonal_csv_all_zones_present():
    raw = make_raw_file(SAMPLE_GISS_ZONAL_CSV)
    rows = _parse_giss_zonal_csv(raw)
    row = rows[0]
    for zone in ["Glob", "NHem", "SHem", "64N-90N", "90S-64S"]:
        assert zone in row


def test_parse_giss_zonal_csv_missing_value():
    content = (
        "Divide by 100 to convert to degrees Celsius\n"
        "Year,Glob,NHem,SHem,24N-90N,24S-24N,90S-24S,64N-90N,44N-64N,24N-44N,EQU-24N,24S-EQU,44S-24S,64S-44S,90S-64S\n"
        "2020,102,***,79,155,82,58,210,140,120,75,70,55,50,40\n"
    )
    raw = make_raw_file(content)
    rows = _parse_giss_zonal_csv(raw)
    assert rows[0]["NHem"] is None
    assert rows[0]["Glob"] == pytest.approx(1.02)


def test_normalize_giss_zonal_creates_json():
    raw = make_raw_file(SAMPLE_GISS_ZONAL_CSV)
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "zonal.json"
        result = _normalize_giss_zonal(raw, out)
        assert result.exists()
        data = json.loads(result.read_text())
    assert "zones" in data
    assert "data" in data
    assert len(data["data"]) == 2


def test_normalize_giss_zonal_zones_list():
    raw = make_raw_file(SAMPLE_GISS_ZONAL_CSV)
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "zonal.json"
        _normalize_giss_zonal(raw, out)
        data = json.loads(out.read_text())
    assert data["zones"] == GISS_ZONES


def test_normalize_giss_zonal_default_output_path(tmp_path, monkeypatch):
    import modules.data_ingestion.ingester as ing
    monkeypatch.setattr(ing, "RAW_DATA_DIR", tmp_path)
    raw = make_raw_file(SAMPLE_GISS_ZONAL_CSV)
    result = _normalize_giss_zonal(raw)
    assert result.name == "nasa_giss_zonal.json"
    assert result.exists()


def test_nasa_giss_zonal_source_in_sources():
    source = get_source("nasa_giss_zonal")
    assert source.parser == "giss_zonal"
    assert source.unit == "°C"


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
