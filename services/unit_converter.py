"""
WeatherPulse — Temperature Unit Converter

Pure functions for Celsius ↔ Fahrenheit conversion and formatting.
No external dependencies; trivially testable.
"""

from __future__ import annotations


def celsius_to_fahrenheit(temp_c: float) -> float:
    """
    Convert Celsius to Fahrenheit.

    Args:
        temp_c: Temperature in degrees Celsius.

    Returns:
        Equivalent temperature in degrees Fahrenheit.
    """
    return (temp_c * 9 / 5) + 32


def fahrenheit_to_celsius(temp_f: float) -> float:
    """
    Convert Fahrenheit to Celsius.

    Args:
        temp_f: Temperature in degrees Fahrenheit.

    Returns:
        Equivalent temperature in degrees Celsius.
    """
    return (temp_f - 32) * 5 / 9


def format_temp(temp_c: float, unit: str) -> str:
    """
    Format a Celsius temperature for display in the requested unit.

    Args:
        temp_c: Temperature in degrees Celsius.
        unit:   "C" for Celsius or "F" for Fahrenheit.

    Returns:
        Formatted string such as "28°C" or "82.4°F".
    """
    if unit.upper() == "F":
        converted = celsius_to_fahrenheit(temp_c)
        return f"{converted:.1f}°F"
    return f"{temp_c:.1f}°C"


def format_temp_range(min_c: float, max_c: float, unit: str) -> str:
    """
    Format a high/low temperature range for daily forecast display.

    Args:
        min_c: Minimum temperature in °C.
        max_c: Maximum temperature in °C.
        unit:  "C" or "F".

    Returns:
        Formatted string like "32°C / 24°C" or "89.6°F / 75.2°F".
    """
    if unit.upper() == "F":
        hi = celsius_to_fahrenheit(max_c)
        lo = celsius_to_fahrenheit(min_c)
        return f"{hi:.0f}°F / {lo:.0f}°F"
    return f"{max_c:.0f}°C / {min_c:.0f}°C"
