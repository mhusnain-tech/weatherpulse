"""
WeatherPulse — Custom Exceptions

All application-level exceptions that the API layer raises.
These are caught by the service layer or GUI and translated into
user-friendly messages — raw requests exceptions never reach the GUI.
"""


class WeatherPulseError(Exception):
    """Base exception for all WeatherPulse application errors."""


class APIKeyError(WeatherPulseError):
    """Raised when the API key is missing or rejected (HTTP 401)."""

    def __init__(self, message: str = "Weather service authentication failed. "
                                       "Please check the API configuration."):
        super().__init__(message)


class LocationNotFoundError(WeatherPulseError):
    """Raised when the requested location does not exist (HTTP 404)."""

    def __init__(self, location: str = ""):
        msg = (
            f"Location '{location}' not found. "
            "Please check the city name or ZIP code."
            if location
            else "Location not found. Please check the city or ZIP code."
        )
        super().__init__(msg)


class NetworkError(WeatherPulseError):
    """Raised on connection failures."""

    def __init__(self, message: str = "Unable to connect to the weather service. "
                                       "Please check your internet connection."):
        super().__init__(message)


class TimeoutError(WeatherPulseError):
    """Raised when a request exceeds the configured timeout."""

    def __init__(self, message: str = "The weather service took too long to respond. "
                                       "Please try again."):
        super().__init__(message)


class RateLimitError(WeatherPulseError):
    """Raised when the API rate limit is exceeded (HTTP 429)."""

    def __init__(self, message: str = "Weather service request limit reached. "
                                       "Please try again later."):
        super().__init__(message)


class APIResponseError(WeatherPulseError):
    """Raised when the API response cannot be parsed or is malformed."""

    def __init__(self, message: str = "Weather data could not be processed. "
                                       "Please try again."):
        super().__init__(message)


class MissingAPIKeyError(WeatherPulseError):
    """Raised when no API key is configured at all."""

    def __init__(self, message: str = "No API key configured. "
                                       "Please add OPENWEATHER_API_KEY to your .env file."):
        super().__init__(message)


class ValidationError(WeatherPulseError):
    """Raised when user input fails validation."""
