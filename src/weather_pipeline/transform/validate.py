"""Data quality checks for clean weather rows."""

import logging
from datetime import date

from weather_pipeline.utils.seeds import read_weather_codes

logger = logging.getLogger(__name__)

VALID_WEATHER_CODES = {code for code, _, _ in read_weather_codes()}

REQUIRED = [
    "city",
    "state",
    "date",
    "weather_code",
    "temp_max_c",
    "temp_min_c",
    "precipitation_mm",
    "wind_speed_max_kmh",
]


class DataQualityError(Exception):
    """Raised when too many rows fail the quality checks."""

    def __init__(self, bad: int, total: int, limit: float):
        self.bad, self.total, self.limit = bad, total, limit
        super().__init__(
            f"{bad} of {total} rows failed checks ({bad / total:.0%}), limit is {limit:.0%}"
        )


def validate_row(row: dict) -> list[str]:
    """Return a list of problems with this row. An empty list means the row is valid."""
    missing = [col for col in REQUIRED if row.get(col) is None]
    if missing:
        return [f"missing {', '.join(missing)}"]  # can't check values that don't exist

    errors = []
    try:
        date.fromisoformat(row["date"])
    except ValueError:
        errors.append(f"invalid date {row['date']!r}")
    if row["weather_code"] not in VALID_WEATHER_CODES:
        errors.append(f"unknown weather_code {row['weather_code']}")
    if not -30 <= row["temp_min_c"] <= 55 or not -30 <= row["temp_max_c"] <= 55:
        errors.append("temperature out of range")
    if row["temp_min_c"] > row["temp_max_c"]:
        errors.append("temp_min_c > temp_max_c")
    if not 0 <= row["precipitation_mm"] <= 1000:
        errors.append(f"precipitation out of range: {row['precipitation_mm']}")
    if not 0 <= row["wind_speed_max_kmh"] <= 400:
        errors.append(f"wind speed out of range: {row['wind_speed_max_kmh']}")
    return errors


def clean_rows(rows: list[dict], max_bad_ratio: float) -> list[dict]:
    """Keep valid rows, drop bad ones, and stop the pipeline if too many are bad."""
    total = len(rows)
    clean, bad = [], 0

    for row in rows:
        errors = validate_row(row)
        if errors:
            bad += 1
            logger.debug(
                "Dropping %s %s: %s",
                row.get("city"),
                row.get("date"),
                "; ".join(errors),
            )
        else:
            clean.append(row)

    if total and bad / total > max_bad_ratio:
        raise DataQualityError(bad, total, max_bad_ratio)
    if bad:
        logger.warning("Dropped %d of %d rows that failed checks", bad, total)
    logger.info("%d clean rows", len(clean))
    return clean
