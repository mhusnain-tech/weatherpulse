"""
WeatherPulse — Weather Service

Orchestrates API calls, normalizes raw JSON into WeatherData models,
aggregates the 3-hour forecast into daily summaries, and caches the
last successful result so unit-switching never triggers a new request.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from api import weather_api
from api.exceptions import APIResponseError
from models.weather import (
    CurrentWeather,
    DailyEntry,
    HourlyEntry,
    LocationInfo,
    WeatherData,
)

logger = logging.getLogger(__name__)

# ─── In-Memory Cache ─────────────────────────────────────────────────────────
# Stores the last successful WeatherData so unit toggling is instant.
_cached_data: Optional[WeatherData] = None
_cached_location: Optional[str] = None


# ─── Public API ──────────────────────────────────────────────────────────────


def fetch_weather(location: str) -> WeatherData:
    """
    Fetch and normalize complete weather data for *location*.

    Calls both the current-weather and forecast endpoints, normalizes
    both responses, and caches the result.

    Args:
        location: City name, "City,Country", or ZIP code.

    Returns:
        Populated WeatherData instance.

    Raises:
        Any exception from api.weather_api (all are WeatherPulseError subclasses).
        APIResponseError: If the API response is structurally invalid.
    """
    global _cached_data, _cached_location

    current_raw = weather_api.get_current_weather(location)
    forecast_raw = weather_api.get_forecast(location)

    weather_data = _normalize(current_raw, forecast_raw)

    _cached_data = weather_data
    _cached_location = location

    return weather_data


def get_cached_data() -> Optional[WeatherData]:
    """Return the last successfully fetched WeatherData, or None."""
    return _cached_data


# ─── Normalization ────────────────────────────────────────────────────────────


def _normalize(current_raw: Dict[str, Any], forecast_raw: Dict[str, Any]) -> WeatherData:
    """
    Translate raw OWM JSON into a WeatherData instance.

    Raises:
        APIResponseError: If mandatory fields are missing.
    """
    try:
        location = _parse_location(current_raw)
        current = _parse_current(current_raw)
        hourly = _parse_hourly(forecast_raw)
        daily = _aggregate_daily(forecast_raw)
        return WeatherData(location=location, current=current, hourly=hourly, daily=daily)
    except (KeyError, TypeError, ValueError) as exc:
        logger.error("Failed to normalize weather data: %s", exc)
        raise APIResponseError() from exc


def _parse_location(data: Dict[str, Any]) -> LocationInfo:
    city = data["name"]
    country = data["sys"]["country"]
    return LocationInfo(city=city, country=country)


def _parse_current(data: Dict[str, Any]) -> CurrentWeather:
    main = data["main"]
    weather = data["weather"][0]
    wind = data.get("wind", {})
    visibility = data.get("visibility")  # metres, optional

    return CurrentWeather(
        temp_c=float(main["temp"]),
        feels_like_c=float(main["feels_like"]),
        humidity=int(main["humidity"]),
        pressure=int(main["pressure"]),
        wind_speed=float(wind.get("speed", 0.0)),
        condition=weather["main"],
        description=weather["description"].capitalize(),
        icon_code=weather["icon"],
        visibility=int(visibility) if visibility is not None else None,
    )


def _parse_hourly(forecast_raw: Dict[str, Any], max_entries: int = 6) -> List[HourlyEntry]:
    """
    Extract the next *max_entries* 3-hour slots from the forecast list.
    OWM returns slots at future times; we take the first N.
    """
    entries: List[HourlyEntry] = []
    now_ts = datetime.now(tz=timezone.utc).timestamp()

    for item in forecast_raw.get("list", []):
        if len(entries) >= max_entries:
            break

        item_ts = item["dt"]
        if item_ts <= now_ts:
            continue  # Skip slots already in the past

        dt = datetime.fromtimestamp(item_ts)
        weather = item["weather"][0]
        main = item["main"]
        pop = float(item.get("pop", 0.0))

        entries.append(
            HourlyEntry(
                dt=dt,
                temp_c=float(main["temp"]),
                condition=weather["main"],
                description=weather["description"].capitalize(),
                icon_code=weather["icon"],
                pop=pop,
            )
        )

    return entries


def _aggregate_daily(forecast_raw: Dict[str, Any], max_days: int = 5) -> List[DailyEntry]:
    """
    Aggregate 3-hour OWM forecast slots into daily summaries.

    For each calendar day we collect:
    - max/min temperatures
    - most common weather condition (midday slot preferred)
    - maximum precipitation probability
    """
    # Group slots by date string "YYYY-MM-DD"
    day_slots: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for item in forecast_raw.get("list", []):
        dt = datetime.fromtimestamp(item["dt"])
        day_key = dt.strftime("%Y-%m-%d")
        day_slots[day_key].append(item)

    daily_entries: List[DailyEntry] = []

    # Sort dates and skip today if we already have it; take up to max_days
    today_str = datetime.now().strftime("%Y-%m-%d")
    sorted_days = sorted(day_slots.keys())

    # Prefer days starting from tomorrow, fall back to all if needed
    future_days = [d for d in sorted_days if d >= today_str]

    for day_key in future_days[:max_days]:
        slots = day_slots[day_key]
        date = datetime.strptime(day_key, "%Y-%m-%d")

        temps = [float(s["main"]["temp"]) for s in slots]
        temp_max = max(temps)
        temp_min = min(temps)

        # Prefer midday slot (12:00–15:00) for representative condition
        midday_slot = _pick_representative_slot(slots)
        weather = midday_slot["weather"][0]
        pop = max(float(s.get("pop", 0.0)) for s in slots)

        daily_entries.append(
            DailyEntry(
                date=date,
                day_name=date.strftime("%a").upper(),
                temp_max_c=temp_max,
                temp_min_c=temp_min,
                condition=weather["main"],
                description=weather["description"].capitalize(),
                icon_code=weather["icon"],
                pop=pop,
            )
        )

    return daily_entries


def _pick_representative_slot(slots: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Choose the most representative slot for a day's condition.
    Prefers a slot near midday (12:00); falls back to the first slot.
    """
    best = slots[0]
    best_distance = 999

    for slot in slots:
        dt = datetime.fromtimestamp(slot["dt"])
        distance = abs(dt.hour - 12)
        if distance < best_distance:
            best_distance = distance
            best = slot

    return best
