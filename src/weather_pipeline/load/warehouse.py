import logging
import sqlite3
from datetime import date
from pathlib import Path

from weather_pipeline.config import PROJECT_ROOT, Settings
from weather_pipeline.load.dimensions import (
    load_dim_date,
    load_dim_location,
    load_dim_weather_code,
)
from weather_pipeline.load.facts import load_fct_daily_weather
from weather_pipeline.transform.clean_weather import clean_path

logger = logging.getLogger(__name__)
DDL_FILE = PROJECT_ROOT / "sql" / "ddl" / "create_tables.sql"


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys = ON")
    return con


def create_tables(con: sqlite3.Connection) -> None:
    con.executescript(DDL_FILE.read_text(encoding="utf-8"))
    logger.info("Star schema tables are ready!")


def load_all(settings: Settings, start: date, end: date) -> int:
    """Load dimensions and facts in one transaction: all or nothing."""
    con = connect(settings.database)
    try:
        create_tables(con)
        with con:  # commit if everything succeeds, else rollback
            load_dim_location(con, settings.locations)
            load_dim_weather_code(con)
            load_dim_date(con, start, end)
            count = load_fct_daily_weather(
                con, clean_path(settings, start, end), start, end
            )
        return count
    finally:
        con.close()
