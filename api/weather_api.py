"""
WeatherPulse — OpenWeatherMap API Client

Responsible for all HTTP communication with the OpenWeatherMap API.
Raises application-level exceptions so the GUI never sees raw
requests exceptions or HTTP status codes.
"""

from __future__ import annotations

import logging
from typing import Any

import requests

from config import settings
from api.exceptions import (
    APIKeyError,
    APIResponseError,
    LocationNotFoundError,
    MissingAPIKeyError,
    NetworkError,
    RateLimitError,
    TimeoutError,
)

logger = logging.getLogger(__name__)


# ─── Internal Helpers ────────────────────────────────────────────────────────


def _check_api_key() -> str:
    """Return the configured API key or raise MissingAPIKeyError."""
    key = settings.OPENWEATHER_API_KEY
    if not key:
        raise MissingAPIKeyError()
    return key


def _handle_response(response: requests.Response, location: str = "") -> dict[str, Any]:
    """
    Validate an HTTP response from the OWM API and return parsed JSON.

    Raises application-level exceptions for all known error codes.
    """
    status = response.status_code

    if status == 200:
        try:
            return response.json()
        except ValueError as exc:
            logger.error("Failed to parse API JSON response: %s", exc)
            raise APIResponseError() from exc

    if status == 401:
        logger.warning("API authentication failed (401).")
        raise APIKeyError()

    if status == 404:
        logger.info("Location not found: '%s' (404).", location)
        raise LocationNotFoundError(location)

    if status == 429:
        logger.warning("API rate limit exceeded (429).")
        raise RateLimitError()

    # All other non-200 responses
    logger.error("Unexpected API response: HTTP %d — %s", status, response.text[:200])
    raise APIResponseError(
        f"Weather data could not be processed (HTTP {status}). Please try again."
    )


def _make_request(url: str, params: dict[str, Any]) -> dict[str, Any]:
    """
    Execute an HTTP GET request and convert any requests exceptions into
    application-level exceptions.
    """
    try:
        response = requests.get(url, params=params, timeout=settings.REQUEST_TIMEOUT)
        return _handle_response(response, params.get("q", ""))
    except requests.exceptions.Timeout as exc:
        logger.warning("API request timed out: %s", exc)
        raise TimeoutError() from exc
    except requests.exceptions.ConnectionError as exc:
        logger.warning("Network connection error: %s", exc)
        raise NetworkError() from exc
    except requests.exceptions.RequestException as exc:
        logger.error("Unexpected requests exception: %s", exc)
        raise NetworkError(
            "An unexpected network error occurred. Please try again."
        ) from exc


# ─── Public API ──────────────────────────────────────────────────────────────


def get_current_weather(location: str) -> dict[str, Any]:
    """
    Fetch current weather data for a city name or ZIP code.

    Args:
        location: City name (e.g. "London"), city+country (e.g. "London,UK"),
                  or ZIP code (e.g. "10001,US").

    Returns:
        Parsed JSON dict from the OWM current weather endpoint.

    Raises:
        MissingAPIKeyError: No API key configured.
        APIKeyError: API key rejected by OpenWeatherMap.
        LocationNotFoundError: Location not found.
        RateLimitError: Request limit exceeded.
        TimeoutError: Request timed out.
        NetworkError: Connection failed.
        APIResponseError: Response could not be parsed.
    """
    api_key = _check_api_key()
    params = {
        "q": location,
        "appid": api_key,
        "units": "metric",  # Always Celsius; conversion handled locally
    }
    logger.info("Fetching current weather for: '%s'", location)
    data = _make_request(settings.OWM_CURRENT_URL, params)
    logger.info("Current weather retrieved successfully for: '%s'", location)
    return data


def get_forecast(location: str) -> dict[str, Any]:
    """
    Fetch 5-day / 3-hour forecast for a city name or ZIP code.

    Args:
        location: Same format as get_current_weather().

    Returns:
        Parsed JSON dict from the OWM forecast endpoint.

    Raises:
        Same exceptions as get_current_weather().
    """
    api_key = _check_api_key()
    params = {
        "q": location,
        "appid": api_key,
        "units": "metric",
        "cnt": 40,  # Maximum 5-day window (40 × 3h slots)
    }
    logger.info("Fetching forecast for: '%s'", location)
    data = _make_request(settings.OWM_FORECAST_URL, params)
    logger.info("Forecast retrieved successfully for: '%s'", location)
    return data
