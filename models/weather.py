"""
WeatherPulse — Data Models

Normalized dataclasses that decouple the GUI from the raw
OpenWeatherMap JSON structure. All temperatures are stored in
Celsius; conversion is performed at display time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class LocationInfo:
    """Geographic location returned with weather data."""

    city: str
    country: str

    @property
    def display_name(self) -> str:
        """Human-readable 'City, COUNTRY' string."""
        return f"{self.city}, {self.country}"


@dataclass
class CurrentWeather:
    """Current conditions at a location (temperatures in °C)."""

    temp_c: float
    feels_like_c: float
    humidity: int           # percentage 0–100
    pressure: int           # hPa
    wind_speed: float       # m/s
    condition: str          # e.g. "Clouds"
    description: str        # e.g. "overcast clouds"
    icon_code: str          # OWM icon code, e.g. "04d"
    visibility: Optional[int] = None   # metres; absent in some responses


@dataclass
class HourlyEntry:
    """Single hourly forecast slot (3-hour intervals from OWM)."""

    dt: datetime
    temp_c: float
    condition: str
    description: str
    icon_code: str
    pop: float = 0.0        # precipitation probability 0.0–1.0

    @property
    def time_label(self) -> str:
        """Short time string for UI display, e.g. '3 PM'."""
        return self.dt.strftime("%-I %p") if hasattr(self.dt, "strftime") else ""

    @property
    def time_label_short(self) -> str:
        """Short time like '3PM' (no space)."""
        try:
            hour = self.dt.hour
            period = "AM" if hour < 12 else "PM"
            display_hour = hour % 12 or 12
            return f"{display_hour}{period}"
        except Exception:  # noqa: BLE001
            return ""


@dataclass
class DailyEntry:
    """Aggregated daily forecast derived from 3-hour OWM slots."""

    date: datetime
    day_name: str           # e.g. "MON", "TUE"
    temp_max_c: float
    temp_min_c: float
    condition: str
    description: str
    icon_code: str
    pop: float = 0.0        # max precipitation probability for the day

    @property
    def date_label(self) -> str:
        """Short date string e.g. 'Mon 11'."""
        return self.date.strftime("%a %d")


@dataclass
class WeatherData:
    """
    Complete normalized weather snapshot for one location.

    This is the single object passed from the service layer to the GUI;
    the GUI never touches raw API JSON.
    """

    location: LocationInfo
    current: CurrentWeather
    hourly: List[HourlyEntry] = field(default_factory=list)   # up to 6 entries
    daily: List[DailyEntry] = field(default_factory=list)     # up to 5 entries
