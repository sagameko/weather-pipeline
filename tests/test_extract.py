from datetime import date

import pytest

from weather_pipeline.config import load_settings
from weather_pipeline.extract import weather_api
from weather_pipeline.extract.weather_api import ExtractError, fetch_daily_weather

START, END = date(2026, 11, 1), date(2026, 11, 2)


class FakeResponse:
    """Pretends to be a requests.Response."""

    def __init__(self, status_code, data=None):
        self.status_code = status_code
        self._data = data
        self.text = "error details"

    def json(self):
        return self._data


@pytest.fixture
def settings():
    return load_settings()


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    """Skip the real retry waits so tests stay fast."""
    monkeypatch.setattr(weather_api.time, "sleep", lambda seconds: None)


def test_retries_on_server_error_then_succeeds(monkeypatch, settings):
    responses = [
        FakeResponse(503),
        FakeResponse(200, {"daily": {"time": ["2026-11-01"]}}),
    ]
    calls = []

    def fake_get(url, params, timeout):
        calls.append(params)
        return responses.pop(0)

    monkeypatch.setattr(weather_api.requests, "get", fake_get)
    data = fetch_daily_weather(settings.locations[0], START, END, settings)

    assert data == {"daily": {"time": ["2026-11-01"]}}
    assert len(calls) == 2  # failed once, then succeeded


def test_does_not_retry_a_bad_request(monkeypatch, settings):
    calls = []

    def fake_get(url, params, timeout):
        calls.append(params)
        return FakeResponse(400)

    monkeypatch.setattr(weather_api.requests, "get", fake_get)
    with pytest.raises(ExtractError, match="HTTP 400"):
        fetch_daily_weather(settings.locations[0], START, END, settings)
    assert len(calls) == 1  # gave up immediately, no retry
