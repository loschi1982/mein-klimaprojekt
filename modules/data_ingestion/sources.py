"""
Datenquellen-Definitionen für das Data Ingestion Module.
Team-Branch: team/data-ingestion
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class DataSource:
    id: str
    name: str
    url: str
    format: str          # "csv" | "json" | "netcdf"
    unit: str
    description: str


SOURCES: dict[str, DataSource] = {
    "esrl_mauna_loa": DataSource(
        id="esrl_mauna_loa",
        name="ESRL Mauna Loa CO₂",
        url="https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_mlo.csv",
        format="csv",
        unit="ppm",
        description="Monatliche CO₂-Konzentration (Mauna Loa Observatory, Hawaii)",
    ),
    "esrl_co2_global": DataSource(
        id="esrl_co2_global",
        name="ESRL Globaler CO₂-Mittelwert",
        url="https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_gl.csv",
        format="csv",
        unit="ppm",
        description="Globaler monatlicher CO₂-Mittelwert",
    ),
    "esrl_ch4": DataSource(
        id="esrl_ch4",
        name="ESRL Methan (CH₄)",
        url="https://gml.noaa.gov/webdata/ccgg/trends/ch4/ch4_mm_gl.csv",
        format="csv",
        unit="ppb",
        description="Globaler monatlicher Methan-Mittelwert",
    ),
}


def get_source(source_id: str) -> DataSource:
    if source_id not in SOURCES:
        raise ValueError(f"Unbekannte Datenquelle: '{source_id}'. Verfügbar: {list(SOURCES.keys())}")
    return SOURCES[source_id]
