"""Extract daily weather from the Open-Meteo archive API."""

import json
import logging
import time
from dataclasses import asdict
from datetime import UTC, date, datetime
from pathlib import Path

import requests

from weather_pipeline.config import Location, Settings

logger = logging.getLogger(__name__)

RETRY_STATUS_CODES = {429, 500, 502, 503, 504}  # temporary problems worth retrying
MAX_ATTEMPTS = 3


class ExtractError(Exception):
    """Raised when weather data could not be fetched from the API."""


def fetch_daily_weather(
    location: Location, start: date, end: date, settings: Settings
) -> dict:
    """Call the API for one location and return the JSON response as a dict."""
    params = {
        "latitude": location.latitude,
        "longitude": location.longitude,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": ",".join(settings.daily_variables),
        "timezone": settings.timezone,
    }

    error = ""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.get(
                settings.api_base_url, params=params, timeout=settings.api_timeout
            )
        except (requests.ConnectionError, requests.Timeout) as e:
            error = f"{type(e).__name__}: {e}"  # network problem: retry
        else:
            if response.status_code == 200:
                return response.json()  # success
            if response.status_code not in RETRY_STATUS_CODES:
                raise ExtractError(  # our mistake: stop now
                    f"{location.city}: HTTP {response.status_code} - {response.text[:200]}"
                )
            error = f"HTTP {response.status_code}"  # server busy: retry

        if attempt < MAX_ATTEMPTS:
            wait_seconds = 2**attempt  # 2s, then 4s
            logger.warning(
                "%s: attempt %d/%d failed (%s). Retrying in %ds",
                location.city,
                attempt,
                MAX_ATTEMPTS,
                error,
                wait_seconds,
            )
            time.sleep(wait_seconds)

    raise ExtractError(
        f"{location.city}: failed after {MAX_ATTEMPTS} attempts ({error})"
    )


def raw_path(settings: Settings, location: Location, start: date, end: date) -> Path:
    return (
        settings.raw_dir
        / "open_meteo"
        / f"{start}_{end}"
        / f"{location.city.lower()}.json"
    )


def save_raw(
    payload: dict, location: Location, start: date, end: date, settings: Settings
) -> Path:
    """Save the untouched API response plus metadata about where and when it came from."""
    path = raw_path(settings, location, start, end)
    path.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "source": "open-meteo-archive",
        "extracted_at": datetime.now(UTC).isoformat(),
        "location": asdict(location),
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "payload": payload,  # the API response, unchanged
    }

    tmp_path = path.with_suffix(".tmp")  # write to a temp file first...
    tmp_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    tmp_path.replace(path)
    return path


def extract_all(settings: Settings, start: date, end: date) -> list[Path]:
    """Extract every configured location. Fails at the end if any location failed."""
    logger.info(
        "Extracting %s to %s for %d locations", start, end, len(settings.locations)
    )
    saved, failed = [], []

    for location in settings.locations:
        try:
            payload = fetch_daily_weather(location, start, end, settings)
        except ExtractError as e:
            logger.error("%s", e)
            failed.append(location.city)
            continue  # keep going with the other cities

        days = len(payload.get("daily", {}).get("time", []))
        path = save_raw(payload, location, start, end, settings)
        logger.info("Saved %d days for %s to %s", days, location.city, path)
        saved.append(path)

    if failed:
        raise ExtractError(f"Extraction failed for: {', '.join(failed)}")
    return saved
