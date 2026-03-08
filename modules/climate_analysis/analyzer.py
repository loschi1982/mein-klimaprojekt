"""
Climate Analysis Module – Statistische Analyse
Team-Branch: team/climate-analysis

Verantwortlich für: Trend-Erkennung, Anomalie-Detektion, Statistiken
"""
import csv
import math
from dataclasses import dataclass, field
from pathlib import Path


PROCESSED_DIR = Path(__file__).parent.parent.parent / "data" / "processed"
RAW_DIR = Path(__file__).parent.parent.parent / "data" / "raw"


# ── Datenstrukturen ───────────────────────────────────────────────────────────

@dataclass
class TrendResult:
    slope: float             # Anstieg pro Jahr (Einheit/Jahr)
    intercept: float
    r_squared: float         # Bestimmtheitsmaß (0–1)
    p_value: float | None    # Signifikanz
    unit: str = ""
    interpretation: str = ""


@dataclass
class AnomalyResult:
    date: str
    value: float
    z_score: float
    is_anomaly: bool
    severity: str            # "normal" | "warning" | "critical"


@dataclass
class SeriesStats:
    count: int
    mean: float
    median: float
    std: float
    min: float
    max: float
    min_date: str
    max_date: str
    unit: str = ""


@dataclass
class AnalysisResult:
    source: str
    unit: str
    stats: SeriesStats
    trend: TrendResult
    anomalies: list[AnomalyResult] = field(default_factory=list)


# ── Laden ─────────────────────────────────────────────────────────────────────

def load_series(csv_path: Path) -> list[tuple[str, float]]:
    """Lädt eine normalisierte CSV als Liste von (date, value)-Tupeln."""
    rows = []
    with open(csv_path, newline="") as f:
        for row in csv.DictReader(f):
            try:
                rows.append((row["date"], float(row["value"])))
            except (KeyError, ValueError):
                continue
    return sorted(rows, key=lambda r: r[0])


def annual_means(series: list[tuple[str, float]]) -> list[tuple[str, float]]:
    """Berechnet Jahresmittelwerte aus einer Monatsserie."""
    by_year: dict[str, list[float]] = {}
    for date, value in series:
        year = date[:4]
        by_year.setdefault(year, []).append(value)
    return sorted(
        [(year, sum(vals) / len(vals)) for year, vals in by_year.items()],
        key=lambda r: r[0],
    )


# ── Statistik ─────────────────────────────────────────────────────────────────

def compute_stats(series: list[tuple[str, float]], unit: str = "") -> SeriesStats:
    """Berechnet deskriptive Statistiken."""
    if not series:
        raise ValueError("Leere Zeitreihe – keine Statistik möglich")

    values = [v for _, v in series]
    n = len(values)
    mean = sum(values) / n
    sorted_v = sorted(values)
    median = sorted_v[n // 2] if n % 2 else (sorted_v[n // 2 - 1] + sorted_v[n // 2]) / 2
    variance = sum((v - mean) ** 2 for v in values) / n
    std = math.sqrt(variance)

    min_val = min(values)
    max_val = max(values)
    min_date = next(d for d, v in series if v == min_val)
    max_date = next(d for d, v in series if v == max_val)

    return SeriesStats(
        count=n, mean=round(mean, 3), median=round(median, 3),
        std=round(std, 3), min=round(min_val, 3), max=round(max_val, 3),
        min_date=min_date, max_date=max_date, unit=unit,
    )


# ── Trend ─────────────────────────────────────────────────────────────────────

def compute_trend(series: list[tuple[str, float]], unit: str = "") -> TrendResult:
    """
    Lineare Regression (OLS) ohne externe Bibliotheken.
    Gibt Steigung, Achsenabschnitt und R² zurück.
    """
    if len(series) < 2:
        raise ValueError("Mindestens 2 Datenpunkte für Trend-Berechnung erforderlich")

    # X = Index (0, 1, 2, ...), Y = Werte
    n = len(series)
    xs = list(range(n))
    ys = [v for _, v in series]

    x_mean = sum(xs) / n
    y_mean = sum(ys) / n

    ss_xy = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    ss_xx = sum((x - x_mean) ** 2 for x in xs)
    ss_yy = sum((y - y_mean) ** 2 for y in ys)

    slope = ss_xy / ss_xx if ss_xx != 0 else 0.0
    intercept = y_mean - slope * x_mean
    r_squared = (ss_xy ** 2 / (ss_xx * ss_yy)) if ss_xx != 0 and ss_yy != 0 else 0.0

    # Steigung in Einheit/Jahr (angenommen: Monatsdaten → ×12)
    slope_per_year = slope * 12

    interpretation = _interpret_trend(slope_per_year, unit)

    return TrendResult(
        slope=round(slope_per_year, 4),
        intercept=round(intercept, 4),
        r_squared=round(r_squared, 4),
        p_value=None,
        unit=unit,
        interpretation=interpretation,
    )


def _interpret_trend(slope_per_year: float, unit: str) -> str:
    if unit == "ppm":
        if slope_per_year > 2.5:
            return f"Starker Anstieg: +{slope_per_year:.2f} ppm/Jahr (über globalem Durchschnitt)"
        elif slope_per_year > 1.0:
            return f"Moderater Anstieg: +{slope_per_year:.2f} ppm/Jahr"
        elif slope_per_year > 0:
            return f"Leichter Anstieg: +{slope_per_year:.2f} ppm/Jahr"
        else:
            return f"Rückgang: {slope_per_year:.2f} ppm/Jahr"
    return f"Trend: {slope_per_year:+.4f} {unit}/Jahr"


# ── Anomalie-Detektion ────────────────────────────────────────────────────────

def detect_anomalies(
    series: list[tuple[str, float]],
    z_threshold: float = 2.5,
) -> list[AnomalyResult]:
    """
    Z-Score-basierte Anomalie-Detektion.
    Werte mit |z| > z_threshold gelten als Anomalie.
    """
    if len(series) < 3:
        return []

    values = [v for _, v in series]
    mean = sum(values) / len(values)
    std = math.sqrt(sum((v - mean) ** 2 for v in values) / len(values))

    if std == 0:
        return []

    results = []
    for date, value in series:
        z = (value - mean) / std
        is_anomaly = abs(z) > z_threshold
        severity = (
            "critical" if abs(z) > 4.0
            else "warning" if abs(z) > z_threshold
            else "normal"
        )
        if is_anomaly:
            results.append(AnomalyResult(
                date=date, value=round(value, 3),
                z_score=round(z, 3),
                is_anomaly=True,
                severity=severity,
            ))

    return results


# ── Vollständige Analyse ──────────────────────────────────────────────────────

def analyze_co2(from_date: str | None = None, to_date: str | None = None) -> AnalysisResult:
    """Vollständige CO₂-Analyse: Statistik + Trend + Anomalien."""
    co2_file = RAW_DIR / "co2_mauna_loa.csv"
    if not co2_file.exists():
        raise FileNotFoundError(
            "CO₂-Daten nicht gefunden. Bitte zuerst POST /api/v1/ingest aufrufen."
        )

    series = load_series(co2_file)

    if from_date:
        series = [(d, v) for d, v in series if d >= from_date]
    if to_date:
        series = [(d, v) for d, v in series if d <= to_date]

    if not series:
        raise ValueError("Keine Daten im angegebenen Zeitraum")

    stats = compute_stats(series, unit="ppm")
    trend = compute_trend(series, unit="ppm")
    anomalies = detect_anomalies(series)

    # Ergebnisse speichern
    _save_result(stats, trend, anomalies)

    return AnalysisResult(
        source="esrl_mauna_loa",
        unit="ppm",
        stats=stats,
        trend=trend,
        anomalies=anomalies,
    )


def _save_result(stats: SeriesStats, trend: TrendResult, anomalies: list[AnomalyResult]) -> None:
    """Speichert Analyseergebnisse in data/processed/."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out = PROCESSED_DIR / "co2_analysis.csv"
    with open(out, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["metric", "value", "unit"])
        writer.writerow(["mean", stats.mean, stats.unit])
        writer.writerow(["median", stats.median, stats.unit])
        writer.writerow(["std", stats.std, stats.unit])
        writer.writerow(["min", stats.min, stats.unit])
        writer.writerow(["max", stats.max, stats.unit])
        writer.writerow(["trend_slope_per_year", trend.slope, f"{stats.unit}/Jahr"])
        writer.writerow(["trend_r_squared", trend.r_squared, ""])
        writer.writerow(["anomaly_count", len(anomalies), ""])
