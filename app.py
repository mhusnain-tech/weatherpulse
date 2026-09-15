"""
WeatherPulse — Application Entry Point

Initialises logging, then launches the Tkinter main window.
"""

import sys
import logging

from utils.logger import setup_logging

# Configure logging before importing any other module that uses it
setup_logging()

logger = logging.getLogger(__name__)


def main() -> None:
    """Start the WeatherPulse application."""
    logger.info("WeatherPulse starting up.")

    try:
        from gui.main_window import MainWindow
        app = MainWindow()
        app.mainloop()
    except KeyboardInterrupt:
        logger.info("WeatherPulse shut down by keyboard interrupt.")
    except Exception:
        logger.exception("Unhandled exception — application terminated.")
        sys.exit(1)

    logger.info("WeatherPulse exited cleanly.")


if __name__ == "__main__":
    main()
