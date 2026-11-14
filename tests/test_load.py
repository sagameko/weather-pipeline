import json
from datetime import date

from weather_pipeline.config import Location
from weather_pipeline.load.dimensions import (
    load_dim_date,
    load_dim_location,
    load_dim_weather_code,
)
from weather_pipeline.load.facts import load_fct_daily_weather

MELBOURNE = Location(city="Melbourne", state="VIC", latitude=-37.81, longitude=144.96)


def test_dim_date_marks_weekends(db):
    load_dim_date(db, date(2026, 11, 1), date(2026, 11, 7))
    weekends = db.execute(
        "SELECT day_of_week FROM dim_date WHERE is_weekend = 1 ORDER BY date_key"
    ).fetchall()
    assert weekends == [("Sunday",), ("Saturday",)]


def test_dim_location_upsert_keeps_the_same_key(db):
    load_dim_location(db, [MELBOURNE])
    moved = Location(city="Melbourne", state="VIC", latitude=-37.80, longitude=144.97)
    load_dim_location(db, [moved])
    assert db.execute("SELECT location_key, latitude FROM dim_location").fetchall() == [
        (1, -37.80)
    ]


def test_fact_load_is_idempotent(db, tmp_path, good_row):
    clean_file = tmp_path / "clean.jsonl"
    rows = [good_row, dict(good_row, date="2026-11-02", precipitation_mm=5.5)]
    clean_file.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    start, end = date(2026, 11, 1), date(2026, 11, 2)

    load_dim_location(db, [MELBOURNE])
    load_dim_weather_code(db)
    load_dim_date(db, start, end)
    load_fct_daily_weather(db, clean_file, start, end)
    load_fct_daily_weather(db, clean_file, start, end)  # second run must not duplicate

    result = db.execute(
        "SELECT date_key, is_rain_day FROM fct_daily_weather ORDER BY date_key"
    ).fetchall()
    assert result == [(20261101, 0), (20261102, 1)]
