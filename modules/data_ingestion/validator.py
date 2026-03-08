"""
Datenvalidierung für normalisierte Klimadaten.
Team-Branch: team/data-ingestion
"""
import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ValidationResult:
    valid: bool
    row_count: int
    errors: list[str]
    warnings: list[str]

    def __bool__(self) -> bool:
        return self.valid


REQUIRED_COLUMNS = {"date", "value", "unit", "source", "ingested_at"}


def validate_csv(path: Path) -> ValidationResult:
    """
    Validiert eine normalisierte Klimadaten-CSV auf:
    - Pflichtfelder vorhanden
    - Datumformat (YYYY-MM-DD)
    - Numerische Werte
    - Keine negativen Werte (außer Temperatur-Anomalien)
    """
    errors: list[str] = []
    warnings: list[str] = []
    row_count = 0

    if not path.exists():
        return ValidationResult(valid=False, row_count=0, errors=[f"Datei nicht gefunden: {path}"], warnings=[])

    with open(path, newline="") as f:
        reader = csv.DictReader(f)

        # Pflichtfelder prüfen
        if reader.fieldnames is None:
            return ValidationResult(valid=False, row_count=0, errors=["Leere CSV-Datei"], warnings=[])

        missing = REQUIRED_COLUMNS - set(reader.fieldnames)
        if missing:
            errors.append(f"Fehlende Pflichtfelder: {missing}")
            return ValidationResult(valid=False, row_count=0, errors=errors, warnings=warnings)

        for i, row in enumerate(reader, start=2):  # Zeile 1 = Header
            row_count += 1

            # Datum prüfen
            date = row.get("date", "")
            if not _valid_date(date):
                errors.append(f"Zeile {i}: Ungültiges Datum '{date}' (erwartet YYYY-MM-DD)")

            # Wert prüfen
            try:
                value = float(row.get("value", ""))
                if value < 0:
                    warnings.append(f"Zeile {i}: Negativer Wert {value} (könnte Fehlmessung sein)")
            except ValueError:
                errors.append(f"Zeile {i}: Kein gültiger Zahlenwert '{row.get('value')}'")

            # Quelle prüfen
            if not row.get("source"):
                warnings.append(f"Zeile {i}: Kein Quellenfeld gesetzt")

    if row_count == 0:
        warnings.append("CSV enthält keine Datenzeilen")

    return ValidationResult(
        valid=len(errors) == 0,
        row_count=row_count,
        errors=errors,
        warnings=warnings,
    )


def _valid_date(date: str) -> bool:
    """Prüft YYYY-MM-DD Format."""
    if len(date) != 10:
        return False
    parts = date.split("-")
    if len(parts) != 3:
        return False
    try:
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        return 1800 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31
    except ValueError:
        return False
