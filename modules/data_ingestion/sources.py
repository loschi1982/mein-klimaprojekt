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
    source_url: str = ""  # Link zur Quell-Website (für Frontend)
    parser: str = "esrl"  # "esrl" | "giss"


SOURCES: dict[str, DataSource] = {
    "esrl_mauna_loa": DataSource(
        id="esrl_mauna_loa",
        name="ESRL Mauna Loa CO₂",
        url="https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_mlo.csv",
        format="csv",
        unit="ppm",
        description="Monatliche CO₂-Konzentration (Mauna Loa Observatory, Hawaii)",
        source_url="https://gml.noaa.gov/ccgg/trends/",
        parser="esrl",
    ),
    "esrl_co2_global": DataSource(
        id="esrl_co2_global",
        name="ESRL Globaler CO₂-Mittelwert",
        url="https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_mm_gl.csv",
        format="csv",
        unit="ppm",
        description="Globaler monatlicher CO₂-Mittelwert (marine surface)",
        source_url="https://gml.noaa.gov/ccgg/trends/gl_data.html",
        parser="esrl",
    ),
    "esrl_ch4": DataSource(
        id="esrl_ch4",
        name="ESRL Methan (CH₄)",
        url="https://gml.noaa.gov/webdata/ccgg/trends/ch4/ch4_mm_gl.csv",
        format="csv",
        unit="ppb",
        description="Globaler monatlicher Methan-Mittelwert",
        source_url="https://gml.noaa.gov/ccgg/trends_ch4/",
        parser="esrl",
    ),
    "nasa_giss_global": DataSource(
        id="nasa_giss_global",
        name="NASA GISS – Globale Temperaturanomalie",
        url="https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv",
        format="csv",
        unit="°C",
        description="Monatliche globale Oberflächentemperatur-Anomalie (1880–heute, Referenz 1951–1980)",
        source_url="https://data.giss.nasa.gov/gistemp/",
        parser="giss",
    ),
    "nasa_giss_zonal": DataSource(
        id="nasa_giss_zonal",
        name="NASA GISS – Zonale Temperaturanomalien",
        url="https://data.giss.nasa.gov/gistemp/tabledata_v4/ZonAnn.Ts+dSST.csv",
        format="csv",
        unit="°C",
        description="Jährliche Temperaturanomalien nach Breitengradzone (1880–heute, Referenz 1951–1980)",
        source_url="https://data.giss.nasa.gov/gistemp/",
        parser="giss_zonal",
    ),
}


def get_source(source_id: str) -> DataSource:
    if source_id not in SOURCES:
        raise ValueError(f"Unbekannte Datenquelle: '{source_id}'. Verfügbar: {list(SOURCES.keys())}")
    return SOURCES[source_id]
