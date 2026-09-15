"""
WeatherPulse — Application Logger

Configures Python's standard logging for both file and (optional) console
output. API keys and secrets must never appear in log output.
"""

from __future__ import annotations

import logging
import logging.handlers
import os

from config import settings


def setup_logging() -> None:
    """
    Configure the root logger with:
    - A rotating file handler writing to weatherpulse.log
    - A console handler at WARNING level (keeps terminal quiet in normal use)

    Should be called once at application startup, before any other module
    creates a logger.
    """
    root_logger = logging.getLogger()
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    root_logger.setLevel(level)

    # Avoid adding duplicate handlers if called more than once (e.g. in tests)
    if root_logger.handlers:
        return

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)-8s] %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ── File Handler ──────────────────────────────────────────────────────────
    try:
        file_handler = logging.handlers.RotatingFileHandler(
            settings.LOG_FILE,
            maxBytes=2 * 1024 * 1024,   # 2 MB
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except OSError as exc:
        # If log file cannot be created (e.g. read-only filesystem), continue
        print(f"[WeatherPulse] Warning: Could not create log file — {exc}")

    # ── Console Handler ───────────────────────────────────────────────────────
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
