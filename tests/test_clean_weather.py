from weather_pipeline.transform.clean_weather import to_rows


def test_to_rows_turns_columns_into_one_row_per_day(raw_record):
    rows = to_rows(raw_record)
    assert len(rows) == 2
    assert rows[1] == {
        "city": "Melbourne",
        "state": "VIC",
        "date": "2026-11-02",
        "weather_code": 61,
        "temp_max_c": 19.0,
        "temp_min_c": 10.7,
        "precipitation_mm": 5.5,
        "wind_speed_max_kmh": 17.2,
    }


def test_to_rows_uses_none_for_missing_fields(raw_record):
    del raw_record["payload"]["daily"]["precipitation_sum"]
    rows = to_rows(raw_record)
    assert all(row["precipitation_mm"] is None for row in rows)
