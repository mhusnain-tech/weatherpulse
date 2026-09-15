"""
WeatherPulse — Configuration Settings
Loads environment variables and defines application constants.
"""

import os
from dotenv import load_dotenv

# Load .env file from the project root
load_dotenv()


# ─── API Credentials ────────────────────────────────────────────────────────

OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")
IPINFO_TOKEN: str = os.getenv("IPINFO_TOKEN", "")


# ─── OpenWeatherMap URLs ─────────────────────────────────────────────────────

OWM_BASE_URL: str = "https://api.openweathermap.org/data/2.5"
OWM_CURRENT_URL: str = f"{OWM_BASE_URL}/weather"
OWM_FORECAST_URL: str = f"{OWM_BASE_URL}/forecast"
OWM_ICON_URL: str = "https://openweathermap.org/img/wn/{icon_code}@2x.png"


# ─── ipinfo.io ───────────────────────────────────────────────────────────────

IPINFO_URL: str = "https://ipinfo.io/json"


# ─── Request Settings ────────────────────────────────────────────────────────

REQUEST_TIMEOUT: int = 10  # seconds


# ─── Input Validation ────────────────────────────────────────────────────────

MAX_LOCATION_LENGTH: int = 100


# ─── Application Metadata ────────────────────────────────────────────────────

APP_NAME: str = "WeatherPulse"
APP_VERSION: str = "1.0.0"
APP_TAGLINE: str = "Real-Time Weather Dashboard"


# ─── Logging ─────────────────────────────────────────────────────────────────

LOG_FILE: str = "weatherpulse.log"
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
