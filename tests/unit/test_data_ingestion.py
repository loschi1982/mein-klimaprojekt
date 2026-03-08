"""Unit Tests für das Data Ingestion Module"""
import csv
import tempfile
from pathlib import Path

import pytest

from modules.data_ingestion.ingester import normalize_co2_mauna_loa, list_datasets


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


def test_normalize_co2_skips_comments():
    raw = make_raw_file(SAMPLE_RAW_CSV)
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "co2.csv"
        result = normalize_co2_mauna_loa(raw, out)
        rows = list(csv.DictReader(open(result)))
    # Kommentarzeilen und fehlende Werte (-99.99) müssen übersprungen werden
    assert all(float(r["value"]) > 0 for r in rows)


def test_normalize_co2_correct_schema():
    raw = make_raw_file(SAMPLE_RAW_CSV)
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "co2.csv"
        normalize_co2_mauna_loa(raw, out)
        rows = list(csv.DictReader(open(out)))

    assert len(rows) == 2  # Zeile mit -99.99 und Kommentare übersprungen
    assert rows[0]["date"] == "1958-04-01"
    assert rows[0]["unit"] == "ppm"
    assert rows[0]["source"] == "esrl_mauna_loa"
    assert rows[1]["date"] == "2024-03-01"
    assert float(rows[1]["value"]) == pytest.approx(421.50)


def test_normalize_co2_filters_missing_values():
    raw = make_raw_file(SAMPLE_RAW_CSV)
    with tempfile.TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "co2.csv"
        normalize_co2_mauna_loa(raw, out)
        rows = list(csv.DictReader(open(out)))
    dates = [r["date"] for r in rows]
    assert "1958-03-01" not in dates  # -99.99 muss gefiltert werden


def test_list_datasets_empty_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        import modules.data_ingestion.ingester as ing
        original = ing.RAW_DATA_DIR
        ing.RAW_DATA_DIR = Path(tmpdir)
        result = list_datasets()
        ing.RAW_DATA_DIR = original
    assert result == []


def test_list_datasets_with_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "test.csv").write_text("date,value\n2024-01-01,400\n")
        import modules.data_ingestion.ingester as ing
        original = ing.RAW_DATA_DIR
        ing.RAW_DATA_DIR = Path(tmpdir)
        result = list_datasets()
        ing.RAW_DATA_DIR = original
    assert len(result) == 1
    assert result[0]["id"] == "test"
    assert result[0]["rows"] == 1
