from pathlib import Path
from dataclasses import dataclass

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2] # Go 2 steps further to get to the root folder of the file
CONFIG_FILE = PROJECT_ROOT/ "config" / "settings.yaml"

@dataclass(frozen=True)
class Location:
    city: str
    state: str
    latitude: float
    longitude: float


@dataclass(frozen=True)
class Settings:
    api_base_url: str
    api_timeout: int
    timezone: str
    daily_variables: list[str]
    locations: list[Location]
    raw_dir: Path
    clean_dir: Path
    database: Path
    log_dir: Path
    max_bad_ratio: float

def load_settings(config_file: Path = CONFIG_FILE) -> Settings:
    if not config_file.exists():
        raise FileNotFoundError(f"Config file cant be found: {config_file}")

    with open(config_file, encoding= "utf-8") as f:
        cfg = yaml.safe_load(f)

    api, paths = cfg["api"], cfg["paths"]

    return Settings(
        api_base_url=api["base_url"],
        api_timeout=api["timeout_seconds"],
        timezone=api["timezone"],
        daily_variables=api["daily_variables"],
        locations=[Location(**item) for item in cfg["locations"]],
        raw_dir=PROJECT_ROOT / paths["raw_dir"],
        clean_dir=PROJECT_ROOT / paths["clean_dir"],
        database=PROJECT_ROOT / paths["database"],
        log_dir=PROJECT_ROOT / paths["log_dir"],
        max_bad_ratio=cfg["quality"]["max_bad_ratio"],
    )