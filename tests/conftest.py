import sqlite3

import pytest

from weather_pipeline.load.warehouse import create_tables


@pytest.fixture
def good_row() -> dict:
    """One valid clean row. Tests copy and break it on purpose."""
    return {
        "city": "Melbourne",
        "state": "VIC",
        "date": "2026-11-01",
        "weather_code": 53,
        "temp_max_c": 19.5,
        "temp_min_c": 12.2,
        "precipitation_mm": 0.9,
        "wind_speed_max_kmh": 10.9,
    }


@pytest.fixture
def raw_record() -> dict:
    """A small raw file in the same shape that extract saves."""
    return {
        "location": {
            "city": "Melbourne",
            "state": "VIC",
            "latitude": -37.81,
            "longitude": 144.96,
        },
        "payload": {
            "daily": {
                "time": ["2026-11-01", "2026-11-02"],
                "weather_code": [53, 61],
                "temperature_2m_max": [19.5, 19.0],
                "temperature_2m_min": [12.2, 10.7],
                "precipitation_sum": [0.9, 5.5],
                "wind_speed_10m_max": [10.9, 17.2],
            }
        },
    }


@pytest.fixture
def db():
    """A fresh, empty warehouse in memory for each test."""
    con = sqlite3.connect(":memory:")
    con.execute("PRAGMA foreign_keys = ON")
    create_tables(con)
    yield con  # the test runs here
    con.close()  # cleanup after the test
