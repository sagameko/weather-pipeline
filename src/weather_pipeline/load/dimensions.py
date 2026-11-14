import logging
import sqlite3
from datetime import date, timedelta

from weather_pipeline.config import PROJECT_ROOT, Location
from weather_pipeline.utils.seeds import read_weather_codes

logger = logging.getLogger(__name__)
WEATHER_CODE_SEEDS = PROJECT_ROOT / "seeds" / "weather_code.csv"


def load_dim_location(con: sqlite3.Connection, locations: list[Location]) -> int:
    """Insert new cities, update coordinates of existing ones (SCD Type 1)."""
    rows = [(loc.city, loc.state, loc.latitude, loc.longitude) for loc in locations]
    con.executemany(
        """
        INSERT INTO dim_location (city, state, latitude, longitude)
        VALUES (?, ?, ?, ?)
        ON CONFLICT (city, state) DO UPDATE SET
            latitude = excluded.latitude,
            longitude = excluded.longitude
        """,
        rows,
    )
    logger.info("dim_location: %d locations upserted", len(rows))
    return len(rows)


def load_dim_weather_code(con: sqlite3.Connection) -> int:
    """Load the WMO weather code lookup from the seed CSV."""
    rows = read_weather_codes()
    con.executemany(
        """
        INSERT INTO dim_weather_code (weather_code, description, category)
        VALUES (?, ?, ?)
        ON CONFLICT (weather_code) DO UPDATE SET
            description = excluded.description,
            category = excluded.category
        """,
        rows,
    )
    logger.info("dim_weather_code: %d codes upserted", len(rows))
    return len(rows)


def date_key(d: date) -> int:
    """2026-11-01 -> 20261101"""
    return int(d.strftime("%Y%m%d"))


def load_dim_date(con: sqlite3.Connection, start: date, end: date) -> int:
    """Generate one row per calendar day between start and end."""
    rows = []
    day = start
    while day <= end:
        rows.append(
            (
                date_key(day),
                day.isoformat(),  # '2026-11-01'
                day.day,
                day.month,
                day.strftime("%B"),  # 'November'
                (day.month - 1) // 3 + 1,  # quarter 1-4
                day.year,
                day.strftime("%A"),  # 'Sunday'
                1 if day.weekday() >= 5 else 0,  # Saturday=5, Sunday=6
            )
        )
        day += timedelta(days=1)

    con.executemany(
        """
        INSERT OR IGNORE INTO dim_date
            (date_key, full_date, day, month, month_name, quarter, year, day_of_week, is_weekend)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    logger.info("dim_date: %d days from %s to %s", len(rows), start, end)
    return len(rows)
