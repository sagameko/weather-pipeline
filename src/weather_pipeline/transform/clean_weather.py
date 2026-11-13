import json
import logging
from datetime import date
from pathlib import Path

from weather_pipeline.config import Settings
from weather_pipeline.extract.weather_api import raw_path
from weather_pipeline.transform.validate import clean_rows

logger = logging.getLogger(__name__)

FIELD_MAP = {
    "weather_code": "weather_code",
    "temperature_2m_max": "temp_max_c",
    "temperature_2m_min": "temp_min_c",
    "precipitation_sum": "precipitation_mm",
    "wind_speed_10m_max": "wind_speed_max_kmh",
}


def read_raw(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def to_rows(record: dict) -> list[dict]:
    """Turn column-shaped API data into one dict per day."""
    location = record["location"]
    daily = record["payload"]["daily"]
    rows = []

    for i, day in enumerate(daily["time"]):
        row = {"city": location["city"], "state": location["state"], "date": day}
        for api_field, column in FIELD_MAP.items():
            values = daily.get(api_field) or []
            row[column] = values[i] if i < len(values) else None  # missing -> None
        rows.append(row)

    return rows


def clean_path(settings: Settings, start: date, end: date) -> Path:
    return settings.clean_dir / "daily_weather" / f"{start}_{end}.jsonl"


def save_clean(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.writelines(json.dumps(row) + "\n" for row in rows)
    tmp_path.replace(path)


def transform_all(settings: Settings, start: date, end: date) -> Path:
    """Read raw files for all locations, validate, and save one clean file."""
    all_rows = []
    for location in settings.locations:
        path = raw_path(settings, location, start, end)
        if not path.exists():
            raise FileNotFoundError(
                f"Raw file missing for {location.city}: {path}. Run extract first."
            )
        rows = to_rows(read_raw(path))
        logger.debug("Read %d rows for %s", len(rows), location.city)
        all_rows.extend(rows)

    logger.info(
        "Transforming %d raw rows from %d locations",
        len(all_rows),
        len(settings.locations),
    )
    clean = clean_rows(all_rows, settings.max_bad_ratio)

    out = clean_path(settings, start, end)
    save_clean(clean, out)
    logger.info("Saved %d clean rows to %s", len(clean), out)
    return out
