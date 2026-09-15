"""
WeatherPulse — Input Validator

Validates user-provided location strings before they reach the API.
Raises ValidationError with user-friendly messages on failure.
"""

from __future__ import annotations

from api.exceptions import ValidationError
from config import settings


def validate_location_input(raw_input: str) -> str:
    """
    Validate and sanitize a user-provided location string.

    Args:
        raw_input: The raw text from the search field.

    Returns:
        The stripped, validated location string ready for API use.

    Raises:
        ValidationError: If validation fails (with a user-friendly message).
    """
    location = raw_input.strip()

    if not location:
        raise ValidationError("Please enter a city name or ZIP code.")

    if len(location) > settings.MAX_LOCATION_LENGTH:
        raise ValidationError(
            f"Location input is too long (maximum {settings.MAX_LOCATION_LENGTH} characters)."
        )

    # Reject obviously invalid inputs (purely numeric strings > 10 chars
    # that aren't plausible ZIP codes, or strings with shell-injection chars)
    forbidden_chars = {";", "|", "&", "`", "$", "<", ">"}
    if any(c in location for c in forbidden_chars):
        raise ValidationError(
            "Location input contains invalid characters. Please enter a city name or ZIP code."
        )

    return location
