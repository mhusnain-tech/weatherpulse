"""
WeatherPulse — Weather Icon Loader

Downloads OWM weather icons, converts them to Tkinter-compatible
PhotoImage objects, and caches them by (icon_code, size) to avoid
redundant downloads.

If a download fails for any reason the function returns None and
the caller must display a text fallback.
"""

from __future__ import annotations

import io
import logging
from typing import Optional, Tuple

import requests
from PIL import Image, ImageTk

from config import settings

logger = logging.getLogger(__name__)

# In-memory cache: (icon_code, size) → PhotoImage
_icon_cache: dict[Tuple[str, int], ImageTk.PhotoImage] = {}


def load_weather_icon(
    icon_code: str, size: int = 50
) -> Optional[ImageTk.PhotoImage]:
    """
    Download (or retrieve from cache) an OWM weather icon.

    Args:
        icon_code:  OWM icon identifier, e.g. "04d".
        size:       Target square pixel size for the icon image.

    Returns:
        A Tkinter-compatible PhotoImage, or None if loading failed.
    """
    cache_key = (icon_code, size)

    if cache_key in _icon_cache:
        return _icon_cache[cache_key]

    url = settings.OWM_ICON_URL.format(icon_code=icon_code)

    try:
        response = requests.get(url, timeout=settings.REQUEST_TIMEOUT)
        if response.status_code != 200:
            logger.warning(
                "Icon download failed for '%s': HTTP %d", icon_code, response.status_code
            )
            return None

        img = Image.open(io.BytesIO(response.content))
        img = img.resize((size, size), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        _icon_cache[cache_key] = photo
        logger.debug("Cached icon '%s' at %dpx", icon_code, size)
        return photo

    except requests.exceptions.RequestException as exc:
        logger.warning("Network error downloading icon '%s': %s", icon_code, exc)
        return None
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to load icon '%s': %s", icon_code, exc)
        return None


def clear_cache() -> None:
    """Clear the icon cache (mainly useful in tests)."""
    _icon_cache.clear()
