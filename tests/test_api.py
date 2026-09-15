"""
Tests — API Layer

Uses unittest.mock to patch requests.get so no real HTTP calls are
made. Verifies that weather_api and weather_service raise the correct
application-level exceptions for each HTTP error scenario.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
import requests

from api import weather_api
from api.exceptions import (
    APIKeyError,
    APIResponseError,
    LocationNotFoundError,
    MissingAPIKeyError,
    NetworkError,
    RateLimitError,
    TimeoutError,
)
from services import weather_service


# ─── Fixtures ─────────────────────────────────────────────────────────────────

SAMPLE_CURRENT = {
    "name": "London",
    "sys": {"country": "GB"},
    "main": {
        "temp": 15.0,
        "feels_like": 13.5,
        "humidity": 72,
        "pressure": 1012,
    },
    "weather": [{"main": "Clouds", "description": "overcast clouds", "icon": "04d"}],
    "wind": {"speed": 3.5},
    "visibility": 10000,
}

# Build minimal forecast with future timestamps
_NOW_TS = int(datetime.now(tz=timezone.utc).timestamp())

SAMPLE_FORECAST = {
    "list": [
        {
            "dt": _NOW_TS + 3600 * (i + 1),
            "main": {"temp": 14.0 + i, "feels_like": 13.0, "humidity": 70, "pressure": 1010},
            "weather": [{"main": "Clouds", "description": "overcast clouds", "icon": "04d"}],
            "wind": {"speed": 3.0},
            "pop": 0.1 * i,
            "dt_txt": f"2025-01-1{i} 12:00:00",
        }
        for i in range(8)
    ]
}


def _make_response(status_code: int, body: dict | None = None) -> MagicMock:
    """Create a mock requests.Response."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = body or {}
    mock_resp.text = json.dumps(body or {})
    return mock_resp


# ─── weather_api tests ────────────────────────────────────────────────────────

class TestGetCurrentWeatherSuccess:
    @patch("api.weather_api.requests.get")
    def test_returns_dict_on_200(self, mock_get):
        mock_get.return_value = _make_response(200, SAMPLE_CURRENT)
        with patch("api.weather_api.settings.OPENWEATHER_API_KEY", "test-key"):
            result = weather_api.get_current_weather("London")
        assert result["name"] == "London"

    @patch("api.weather_api.requests.get")
    def test_passes_metric_units(self, mock_get):
        mock_get.return_value = _make_response(200, SAMPLE_CURRENT)
        with patch("api.weather_api.settings.OPENWEATHER_API_KEY", "test-key"):
            weather_api.get_current_weather("London")
        call_kwargs = mock_get.call_args
        params = call_kwargs[1]["params"]
        assert params["units"] == "metric"


class TestGetCurrentWeatherErrors:
    def test_raises_missing_key_when_no_key(self):
        with patch("api.weather_api.settings.OPENWEATHER_API_KEY", ""):
            with pytest.raises(MissingAPIKeyError):
                weather_api.get_current_weather("London")

    @patch("api.weather_api.requests.get")
    def test_raises_location_not_found_on_404(self, mock_get):
        mock_get.return_value = _make_response(404)
        with patch("api.weather_api.settings.OPENWEATHER_API_KEY", "test-key"):
            with pytest.raises(LocationNotFoundError):
                weather_api.get_current_weather("FakeCity123")

    @patch("api.weather_api.requests.get")
    def test_raises_api_key_error_on_401(self, mock_get):
        mock_get.return_value = _make_response(401)
        with patch("api.weather_api.settings.OPENWEATHER_API_KEY", "bad-key"):
            with pytest.raises(APIKeyError):
                weather_api.get_current_weather("London")

    @patch("api.weather_api.requests.get")
    def test_raises_rate_limit_on_429(self, mock_get):
        mock_get.return_value = _make_response(429)
        with patch("api.weather_api.settings.OPENWEATHER_API_KEY", "test-key"):
            with pytest.raises(RateLimitError):
                weather_api.get_current_weather("London")

    @patch("api.weather_api.requests.get")
    def test_raises_timeout_on_requests_timeout(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout("timed out")
        with patch("api.weather_api.settings.OPENWEATHER_API_KEY", "test-key"):
            with pytest.raises(TimeoutError):
                weather_api.get_current_weather("London")

    @patch("api.weather_api.requests.get")
    def test_raises_network_error_on_connection_error(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError("no network")
        with patch("api.weather_api.settings.OPENWEATHER_API_KEY", "test-key"):
            with pytest.raises(NetworkError):
                weather_api.get_current_weather("London")

    @patch("api.weather_api.requests.get")
    def test_raises_api_response_error_on_malformed_json(self, mock_get):
        mock_resp = _make_response(200, {})
        mock_resp.json.side_effect = ValueError("malformed JSON")
        mock_get.return_value = mock_resp
        with patch("api.weather_api.settings.OPENWEATHER_API_KEY", "test-key"):
            with pytest.raises(APIResponseError):
                weather_api.get_current_weather("London")

    @patch("api.weather_api.requests.get")
    def test_raises_api_response_error_on_unexpected_status(self, mock_get):
        mock_get.return_value = _make_response(503)
        with patch("api.weather_api.settings.OPENWEATHER_API_KEY", "test-key"):
            with pytest.raises(APIResponseError):
                weather_api.get_current_weather("London")


# ─── weather_service tests ────────────────────────────────────────────────────

class TestWeatherServiceFetchSuccess:
    @patch("services.weather_service.weather_api.get_forecast")
    @patch("services.weather_service.weather_api.get_current_weather")
    def test_returns_weather_data_object(self, mock_current, mock_forecast):
        mock_current.return_value = SAMPLE_CURRENT
        mock_forecast.return_value = SAMPLE_FORECAST

        result = weather_service.fetch_weather("London")

        assert result.location.city == "London"
        assert result.location.country == "GB"
        assert result.current.temp_c == pytest.approx(15.0)
        assert result.current.humidity == 72

    @patch("services.weather_service.weather_api.get_forecast")
    @patch("services.weather_service.weather_api.get_current_weather")
    def test_populates_hourly(self, mock_current, mock_forecast):
        mock_current.return_value = SAMPLE_CURRENT
        mock_forecast.return_value = SAMPLE_FORECAST

        result = weather_service.fetch_weather("London")

        assert len(result.hourly) > 0
        assert len(result.hourly) <= 6

    @patch("services.weather_service.weather_api.get_forecast")
    @patch("services.weather_service.weather_api.get_current_weather")
    def test_populates_daily(self, mock_current, mock_forecast):
        mock_current.return_value = SAMPLE_CURRENT
        mock_forecast.return_value = SAMPLE_FORECAST

        result = weather_service.fetch_weather("London")

        # At least 1 daily entry from the sample data
        assert len(result.daily) >= 1

    @patch("services.weather_service.weather_api.get_forecast")
    @patch("services.weather_service.weather_api.get_current_weather")
    def test_caches_last_result(self, mock_current, mock_forecast):
        mock_current.return_value = SAMPLE_CURRENT
        mock_forecast.return_value = SAMPLE_FORECAST

        weather_service.fetch_weather("London")
        cached = weather_service.get_cached_data()

        assert cached is not None
        assert cached.location.city == "London"


class TestWeatherServicePropagatesErrors:
    @patch("services.weather_service.weather_api.get_current_weather")
    def test_propagates_location_not_found(self, mock_current):
        mock_current.side_effect = LocationNotFoundError("FakeCity")
        with pytest.raises(LocationNotFoundError):
            weather_service.fetch_weather("FakeCity")

    @patch("services.weather_service.weather_api.get_current_weather")
    def test_propagates_api_key_error(self, mock_current):
        mock_current.side_effect = APIKeyError()
        with pytest.raises(APIKeyError):
            weather_service.fetch_weather("London")

    @patch("services.weather_service.weather_api.get_current_weather")
    def test_propagates_network_error(self, mock_current):
        mock_current.side_effect = NetworkError()
        with pytest.raises(NetworkError):
            weather_service.fetch_weather("London")

    @patch("services.weather_service.weather_api.get_current_weather")
    def test_propagates_timeout(self, mock_current):
        mock_current.side_effect = TimeoutError()
        with pytest.raises(TimeoutError):
            weather_service.fetch_weather("London")


class TestErrorMessages:
    def test_location_not_found_includes_city(self):
        exc = LocationNotFoundError("FakeCity")
        assert "FakeCity" in str(exc)

    def test_missing_api_key_message(self):
        exc = MissingAPIKeyError()
        assert "API key" in str(exc)

    def test_rate_limit_message(self):
        exc = RateLimitError()
        assert "limit" in str(exc).lower() or "rate" in str(exc).lower()

    def test_timeout_message(self):
        exc = TimeoutError()
        assert "too long" in str(exc).lower() or "timeout" in str(exc).lower() or "respond" in str(exc).lower()

    def test_network_error_message(self):
        exc = NetworkError()
        assert "connect" in str(exc).lower() or "network" in str(exc).lower()
