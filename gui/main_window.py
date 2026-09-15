"""
WeatherPulse — Main Application Window

Orchestrates all GUI panels, manages application state transitions,
and coordinates background threading for non-blocking API requests.

State machine:
    IDLE  →  LOADING  →  SUCCESS  →  (display weather)
                      →  ERROR    →  (display message, ready for retry)
"""

from __future__ import annotations

import logging
import threading
import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk
from typing import Optional

from api.exceptions import MissingAPIKeyError, ValidationError, WeatherPulseError
from api.location_api import get_location_by_ip
from gui.current_weather import CurrentWeatherPanel
from gui.daily_forecast import DailyForecastPanel
from gui.hourly_forecast import HourlyForecastPanel
from gui.theme import COLORS, FONTS, PAD, separator, styled_frame, styled_label
from models.weather import WeatherData
from services import weather_service
from utils.validators import validate_location_input

logger = logging.getLogger(__name__)


class MainWindow(tk.Tk):
    """
    Root Tkinter window for WeatherPulse.

    Responsibilities:
    - Build and lay out all UI regions.
    - Handle search interaction (validate → background fetch → GUI update).
    - Handle unit toggle without re-fetching data.
    - Handle IP-based location detection.
    - Display loading states and error messages inside the GUI.
    """

    def __init__(self):
        super().__init__()
        self._current_unit: str = "C"          # "C" or "F"
        self._weather_data: Optional[WeatherData] = None
        self._request_in_flight: bool = False
        self._loading_dots: int = 0

        self._configure_window()
        self._build_ui()
        self.after(100, self._check_api_key_on_start)

    # ─── Window Configuration ─────────────────────────────────────────────

    def _configure_window(self) -> None:
        """Set window geometry, title, and background."""
        self.title("WeatherPulse — Real-Time Weather Dashboard")
        self.configure(bg=COLORS["bg_root"])
        self.resizable(True, True)
        self.minsize(760, 600)

        # Centre the window on screen at startup
        w, h = 900, 850
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        # Custom close handler
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ─── UI Construction ──────────────────────────────────────────────────

    def _build_ui(self) -> None:
        """Assemble all GUI regions from top to bottom."""
        self._build_header()
        self._build_search_bar()
        self._build_status_bar()

        # Scrollable content area
        self._build_scroll_area()

    def _build_header(self) -> None:
        """Dark application header with title and tagline."""
        header = tk.Frame(self, bg=COLORS["bg_header"])
        header.pack(fill=tk.X)

        inner = tk.Frame(header, bg=COLORS["bg_header"])
        inner.pack(pady=PAD["xl"])

        tk.Label(
            inner,
            text="⛅  WeatherPulse",
            font=FONTS["app_title"],
            fg=COLORS["text_primary"],
            bg=COLORS["bg_header"],
        ).pack()

        tk.Label(
            inner,
            text="Real-Time Weather Dashboard",
            font=FONTS["app_tagline"],
            fg=COLORS["text_muted"],
            bg=COLORS["bg_header"],
        ).pack(pady=(2, 0))

        separator(self, bg_key="border").pack(fill=tk.X)

    def _build_search_bar(self) -> None:
        """Search field, unit toggle, and action buttons."""
        bar = tk.Frame(self, bg=COLORS["bg_root"])
        bar.pack(fill=tk.X, padx=PAD["xl"], pady=PAD["lg"])

        # ── Location input ────────────────────────────────────────────────
        input_row = styled_frame(bar, bg_key="bg_root")
        input_row.pack(fill=tk.X)

        styled_label(
            input_row,
            text="Location",
            font_key="body",
            color_key="text_secondary",
            bg_key="bg_root",
        ).pack(anchor=tk.W, pady=(0, PAD["xs"]))

        entry_frame = tk.Frame(
            input_row,
            bg=COLORS["bg_input"],
            highlightbackground=COLORS["border_light"],
            highlightthickness=1,
        )
        entry_frame.pack(fill=tk.X)

        self._search_var = tk.StringVar()
        self._search_entry = tk.Entry(
            entry_frame,
            textvariable=self._search_var,
            font=FONTS["body"],
            fg=COLORS["text_primary"],
            bg=COLORS["bg_input"],
            insertbackground=COLORS["accent"],
            relief=tk.FLAT,
            bd=PAD["sm"],
        )
        self._search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=6)
        self._search_entry.bind("<Return>", lambda _e: self._on_search())

        # Placeholder behaviour
        self._search_entry.insert(0, "Enter city name or ZIP code…")
        self._search_entry.configure(fg=COLORS["text_muted"])
        self._search_entry.bind("<FocusIn>", self._on_entry_focus_in)
        self._search_entry.bind("<FocusOut>", self._on_entry_focus_out)

        # ── Action buttons ────────────────────────────────────────────────
        btn_frame = styled_frame(input_row, bg_key="bg_root")
        btn_frame.pack(fill=tk.X, pady=(PAD["sm"], 0))

        self._search_btn = self._make_button(
            btn_frame,
            text="🔍  Search",
            command=self._on_search,
            primary=True,
        )
        self._search_btn.pack(side=tk.LEFT, padx=(0, PAD["sm"]))

        self._detect_btn = self._make_button(
            btn_frame,
            text="📍  Detect Location",
            command=self._on_detect_location,
            primary=False,
        )
        self._detect_btn.pack(side=tk.LEFT)

        # ── Unit toggle ───────────────────────────────────────────────────
        toggle_frame = styled_frame(bar, bg_key="bg_root")
        toggle_frame.pack(fill=tk.X, pady=(PAD["sm"], 0))

        styled_label(
            toggle_frame,
            text="Temperature:",
            font_key="small",
            color_key="text_muted",
            bg_key="bg_root",
        ).pack(side=tk.LEFT, padx=(0, PAD["sm"]))

        self._unit_var = tk.StringVar(value="C")

        self._c_btn = self._make_toggle_btn(toggle_frame, "°C", "C")
        self._c_btn.pack(side=tk.LEFT, padx=2)

        self._f_btn = self._make_toggle_btn(toggle_frame, "°F", "F")
        self._f_btn.pack(side=tk.LEFT, padx=2)

        self._update_toggle_style()

    def _build_status_bar(self) -> None:
        """Status / error message strip below the search bar."""
        self._status_var = tk.StringVar(value="")
        self._status_label = tk.Label(
            self,
            textvariable=self._status_var,
            font=FONTS["status"],
            fg=COLORS["text_secondary"],
            bg=COLORS["bg_root"],
            anchor=tk.W,
        )
        self._status_label.pack(fill=tk.X, padx=PAD["xl"], pady=(0, PAD["xs"]))

    def _build_scroll_area(self) -> None:
        """Vertically scrollable canvas containing the weather panels."""
        container = tk.Frame(self, bg=COLORS["bg_root"])
        container.pack(fill=tk.BOTH, expand=True, padx=PAD["lg"], pady=(0, PAD["lg"]))

        # Canvas + scrollbar
        self._canvas = tk.Canvas(
            container,
            bg=COLORS["bg_root"],
            bd=0,
            highlightthickness=0,
        )
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Inner frame inside canvas
        self._scroll_frame = tk.Frame(self._canvas, bg=COLORS["bg_root"])
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._scroll_frame, anchor="nw"
        )

        self._scroll_frame.bind("<Configure>", self._on_scroll_frame_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        # Mouse-wheel scrolling
        self._canvas.bind_all("<MouseWheel>", self._on_mouse_wheel)

        self._build_panels()

    def _build_panels(self) -> None:
        """Instantiate and pack all weather content panels."""
        panel_kwargs = {"bg": COLORS["bg_panel"]}

        self._current_panel = CurrentWeatherPanel(
            self._scroll_frame,
            bd=0,
            relief=tk.FLAT,
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        self._current_panel.pack(
            fill=tk.X, pady=(0, PAD["sm"]),
        )

        self._hourly_panel = HourlyForecastPanel(
            self._scroll_frame,
            bd=0,
            relief=tk.FLAT,
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        self._hourly_panel.pack(
            fill=tk.X, pady=(0, PAD["sm"]),
        )

        self._daily_panel = DailyForecastPanel(
            self._scroll_frame,
            bd=0,
            relief=tk.FLAT,
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )
        self._daily_panel.pack(
            fill=tk.X, pady=(0, PAD["sm"]),
        )

    # ─── Widget Factories ─────────────────────────────────────────────────

    def _make_button(
        self, parent: tk.Widget, text: str, command, primary: bool = True
    ) -> tk.Button:
        bg = COLORS["btn_primary"] if primary else COLORS["btn_detect"]
        hover = COLORS["btn_hover"] if primary else COLORS["btn_detect_hover"]

        btn = tk.Button(
            parent,
            text=text,
            command=command,
            font=FONTS["button"],
            fg=COLORS["text_primary"],
            bg=bg,
            activebackground=hover,
            activeforeground=COLORS["text_primary"],
            relief=tk.FLAT,
            padx=PAD["md"],
            pady=PAD["xs"],
            cursor="hand2",
            bd=0,
        )
        btn.bind("<Enter>", lambda _e, b=btn, h=hover: b.configure(bg=h))
        btn.bind("<Leave>", lambda _e, b=btn, c=bg: b.configure(bg=c))
        return btn

    def _make_toggle_btn(self, parent: tk.Widget, label: str, unit: str) -> tk.Button:
        btn = tk.Button(
            parent,
            text=label,
            command=lambda u=unit: self._on_unit_change(u),
            font=FONTS["button"],
            relief=tk.FLAT,
            padx=PAD["md"],
            pady=2,
            cursor="hand2",
            bd=0,
        )
        return btn

    # ─── Event Handlers ───────────────────────────────────────────────────

    def _on_entry_focus_in(self, _event) -> None:
        """Clear placeholder text when entry gains focus."""
        if self._search_var.get() == "Enter city name or ZIP code…":
            self._search_entry.delete(0, tk.END)
            self._search_entry.configure(fg=COLORS["text_primary"])

    def _on_entry_focus_out(self, _event) -> None:
        """Restore placeholder if entry is empty."""
        if not self._search_var.get().strip():
            self._search_entry.insert(0, "Enter city name or ZIP code…")
            self._search_entry.configure(fg=COLORS["text_muted"])

    def _on_search(self) -> None:
        """Validate input and kick off a background weather fetch."""
        if self._request_in_flight:
            return

        raw = self._search_var.get()
        if raw == "Enter city name or ZIP code…":
            raw = ""

        try:
            location = validate_location_input(raw)
        except ValidationError as exc:
            self._show_error(str(exc))
            return

        self._start_fetch(location)

    def _on_detect_location(self) -> None:
        """Detect location via IP, populate field, then fetch weather."""
        if self._request_in_flight:
            return

        self._set_loading(True, "Detecting your location…")

        def detect_and_fetch():
            city = get_location_by_ip()
            if city:
                self.after(0, lambda c=city: self._after_detect_success(c))
            else:
                self.after(
                    0,
                    lambda: self._show_error(
                        "Could not detect your location. Please enter a city manually."
                    ),
                )
                self.after(0, lambda: self._set_loading(False))

        threading.Thread(target=detect_and_fetch, daemon=True).start()

    def _after_detect_success(self, city: str) -> None:
        """Called on the main thread after successful IP detection."""
        # Update entry field
        self._search_entry.delete(0, tk.END)
        self._search_entry.insert(0, city)
        self._search_entry.configure(fg=COLORS["text_primary"])
        self._start_fetch(city)

    def _on_unit_change(self, unit: str) -> None:
        """Switch temperature unit and refresh displayed data (no API call)."""
        if unit == self._current_unit:
            return
        self._current_unit = unit
        self._update_toggle_style()

        if self._weather_data is not None:
            data = self._weather_data
            self._current_panel.refresh_unit(data, unit)
            self._hourly_panel.refresh_unit(data.hourly, unit)
            self._daily_panel.refresh_unit(data.daily, unit)

    def _on_scroll_frame_configure(self, _event) -> None:
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event) -> None:
        self._canvas.itemconfigure(self._canvas_window, width=event.width)

    def _on_mouse_wheel(self, event) -> None:
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_close(self) -> None:
        self.destroy()

    # ─── Background Fetch ─────────────────────────────────────────────────

    def _start_fetch(self, location: str) -> None:
        """Launch weather fetch in a background thread."""
        self._set_loading(True, "Loading weather data…")
        self._animate_loading()

        def worker():
            try:
                data = weather_service.fetch_weather(location)
                self.after(0, lambda d=data: self._on_fetch_success(d))
            except WeatherPulseError as exc:
                self.after(0, lambda msg=str(exc): self._on_fetch_error(msg))
            except Exception as exc:  # noqa: BLE001
                logger.exception("Unexpected error during weather fetch.")
                self.after(
                    0,
                    lambda: self._on_fetch_error(
                        "An unexpected error occurred. Please try again."
                    ),
                )

        threading.Thread(target=worker, daemon=True).start()

    def _on_fetch_success(self, data: WeatherData) -> None:
        """Update GUI with fetched weather data (called on main thread)."""
        self._weather_data = data
        self._set_loading(False)
        self._clear_status()

        self._current_panel.update(data, self._current_unit)
        self._hourly_panel.update(data.hourly, self._current_unit)
        self._daily_panel.update(data.daily, self._current_unit)

        logger.info(
            "Dashboard updated for %s.", data.location.display_name
        )

    def _on_fetch_error(self, message: str) -> None:
        """Show error message in the GUI status bar (called on main thread)."""
        self._set_loading(False)
        self._show_error(message)

    # ─── UI State Helpers ─────────────────────────────────────────────────

    def _set_loading(self, loading: bool, message: str = "") -> None:
        """Enter or exit the loading state."""
        self._request_in_flight = loading

        if loading:
            self._search_btn.configure(
                state=tk.DISABLED, bg=COLORS["btn_disabled"], text="⏳  Searching…"
            )
            self._detect_btn.configure(state=tk.DISABLED)
            self._status_label.configure(fg=COLORS["text_secondary"])
            self._status_var.set(message)
        else:
            self._search_btn.configure(
                state=tk.NORMAL, bg=COLORS["btn_primary"], text="🔍  Search"
            )
            self._detect_btn.configure(state=tk.NORMAL)

    def _animate_loading(self) -> None:
        """Cycle a dot animation on the status label while loading."""
        if not self._request_in_flight:
            return
        dots = "." * ((self._loading_dots % 3) + 1)
        base = self._status_var.get().rstrip(". ")
        self._status_var.set(f"{base}{dots}")
        self._loading_dots += 1
        self.after(400, self._animate_loading)

    def _show_error(self, message: str) -> None:
        """Display an error message in the status bar."""
        self._status_label.configure(fg=COLORS["text_error"])
        self._status_var.set(f"⚠  {message}")
        logger.warning("GUI error displayed: %s", message)

    def _clear_status(self) -> None:
        self._status_label.configure(fg=COLORS["text_secondary"])
        self._status_var.set("")

    def _update_toggle_style(self) -> None:
        """Highlight the active unit toggle button."""
        for btn, unit in [(self._c_btn, "C"), (self._f_btn, "F")]:
            if self._current_unit == unit:
                btn.configure(
                    bg=COLORS["toggle_active"],
                    fg=COLORS["text_primary"],
                )
            else:
                btn.configure(
                    bg=COLORS["toggle_inactive"],
                    fg=COLORS["text_secondary"],
                )

    def _check_api_key_on_start(self) -> None:
        """Show a one-time hint if no API key is configured."""
        from config import settings
        if not settings.OPENWEATHER_API_KEY:
            self._show_error(
                "No API key found. Add OPENWEATHER_API_KEY to your .env file to get started."
            )
