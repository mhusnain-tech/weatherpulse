"""
WeatherPulse — IP Geolocation API Client

Uses ipinfo.io to detect the user's approximate city based on their
public IP address. This is a best-effort, optional feature — failure
must never prevent the manual city-search from working.
"""

from __future__ import annotations

import logging
from typing import Optional

import requests

from config import settings

logger = logging.getLogger(__name__)


def get_location_by_ip() -> Optional[str]:
    """
    Attempt to detect the user's approximate city via IP geolocation.

    Uses ipinfo.io. If an IPINFO_TOKEN is configured it is included for
    higher rate limits; otherwise the unauthenticated endpoint is used.

    Returns:
        A city string (e.g. "Lahore") suitable for passing to the weather
        API, or None if detection failed for any reason.
    """
    try:
        params: dict[str, str] = {}
        if settings.IPINFO_TOKEN:
            params["token"] = settings.IPINFO_TOKEN

        response = requests.get(
            settings.IPINFO_URL,
            params=params,
            timeout=settings.REQUEST_TIMEOUT,
        )

        if response.status_code != 200:
            logger.warning(
                "ipinfo.io returned HTTP %d — location detection unavailable.",
                response.status_code,
            )
            return None

        data = response.json()
        city: Optional[str] = data.get("city")

        if city:
            logger.info("IP-based location detected: '%s'", city)
            return city

        logger.warning("ipinfo.io response did not contain a city field.")
        return None

    except requests.exceptions.Timeout:
        logger.warning("ipinfo.io request timed out.")
        return None
    except requests.exceptions.ConnectionError:
        logger.warning("Could not connect to ipinfo.io.")
        return None
    except (ValueError, KeyError) as exc:
        logger.warning("Failed to parse ipinfo.io response: %s", exc)
        return None
    except Exception as exc:  # noqa: BLE001
        logger.error("Unexpected error during IP location detection: %s", exc)
        return None
