-- Star schema for daily weather (gold layer)

CREATE TABLE IF NOT EXISTS dim_location (
    location_key  INTEGER PRIMARY KEY,          -- surrogate key
    city          TEXT    NOT NULL,
    state         TEXT    NOT NULL,
    latitude      REAL    NOT NULL,
    longitude     REAL    NOT NULL,
    UNIQUE (city, state)                         -- natural key: no duplicate cities
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_key     INTEGER PRIMARY KEY,           -- e.g. 20261101
    full_date    TEXT    NOT NULL UNIQUE,        -- '2026-11-01'
    day          INTEGER NOT NULL,
    month        INTEGER NOT NULL,
    month_name   TEXT    NOT NULL,
    quarter      INTEGER NOT NULL,
    year         INTEGER NOT NULL,
    day_of_week  TEXT    NOT NULL,
    is_weekend   INTEGER NOT NULL CHECK (is_weekend IN (0, 1))
);

CREATE TABLE IF NOT EXISTS dim_weather_code (
    weather_code  INTEGER PRIMARY KEY,          -- WMO code, a stable standard
    description   TEXT    NOT NULL,             -- 'Light drizzle'
    category      TEXT    NOT NULL              -- 'Drizzle'
);

CREATE TABLE IF NOT EXISTS fct_daily_weather (
    date_key            INTEGER NOT NULL REFERENCES dim_date (date_key),
    location_key        INTEGER NOT NULL REFERENCES dim_location (location_key),
    weather_code        INTEGER NOT NULL REFERENCES dim_weather_code (weather_code),
    temp_max_c          REAL    NOT NULL,
    temp_min_c          REAL    NOT NULL,
    precipitation_mm    REAL    NOT NULL,
    wind_speed_max_kmh  REAL    NOT NULL,
    is_rain_day         INTEGER NOT NULL CHECK (is_rain_day IN (0, 1)),
    loaded_at           TEXT    NOT NULL,       -- when this row was loaded (UTC)
    PRIMARY KEY (date_key, location_key)        -- the grain: one city, one day
);