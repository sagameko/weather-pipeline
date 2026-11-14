import json
import logging
import sqlite3
from datetime import UTC, date, datetime
from pathlib import Path

from weather_pipeline.load.dimensions import date_key

logger = logging.getLogger(__name__)

RAIN_DAY_MIN_MM = 1.0


def read_clean(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_fct_daily_weather(
    con: sqlite3.Connection, clean_file: Path, start: date, end: date
) -> int:
    """Replace all fact rows for the date range with the rows from the clean file."""
    rows = read_clean(clean_file)

    # Lookup: (city, state) -> location_key
    location_keys = {
        (city, state): key
        for key, city, state in con.execute(
            "SELECT location_key, city, state FROM dim_location"
        )
    }

    loaded_at = datetime.now(UTC).isoformat()
    fact_rows = []
    for r in rows:
        key = location_keys.get((r["city"], r["state"]))
        if key is None:
            raise ValueError(
                f"No dim_location row for {r['city']}, {r['state']}. Load dimensions first."
            )
        fact_rows.append(
            (
                date_key(date.fromisoformat(r["date"])),
                key,
                r["weather_code"],
                r["temp_max_c"],
                r["temp_min_c"],
                r["precipitation_mm"],
                r["wind_speed_max_kmh"],
                1 if r["precipitation_mm"] >= RAIN_DAY_MIN_MM else 0,
                loaded_at,
            )
        )

    # Idempotent: remove what's already there for this range, then insert fresh rows
    deleted = con.execute(
        "DELETE FROM fct_daily_weather WHERE date_key BETWEEN ? AND ?",
        (date_key(start), date_key(end)),
    ).rowcount
    con.executemany(
        """
        INSERT INTO fct_daily_weather
            (date_key, location_key, weather_code, temp_max_c, temp_min_c,
             precipitation_mm, wind_speed_max_kmh, is_rain_day, loaded_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        fact_rows,
    )
    logger.info(
        "fct_daily_weather: replaced %d old rows with %d new rows for %s to %s",
        deleted,
        len(fact_rows),
        start,
        end,
    )
    return len(fact_rows)
