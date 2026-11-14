import csv

from weather_pipeline.config import PROJECT_ROOT

WEATHER_CODES_SEED = PROJECT_ROOT / "seeds" / "weather_codes.csv"


def read_weather_codes() -> list[tuple[int, str, str]]:
    with open(WEATHER_CODES_SEED, newline="", encoding="utf-8") as f:
        return [
            (int(r["weather_code"]), r["description"], r["category"])
            for r in csv.DictReader(f)
        ]
