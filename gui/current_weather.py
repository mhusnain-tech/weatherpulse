"""
WeatherPulse — Current Weather Panel

Displays location, weather icon, temperature, condition description,
and detail stats (feels-like, humidity, wind, pressure, visibility).
"""

from __future__ import annotations

import tkinter as tk
from typing import Optional

from gui.theme import COLORS, FONTS, PAD, separator, styled_frame, styled_label
from models.weather import WeatherData
from services.unit_converter import celsius_to_fahrenheit, format_temp
from utils.image_loader import load_weather_icon


class CurrentWeatherPanel(tk.Frame):
    """
    A self-contained frame that renders current weather conditions.

    Call update(weather_data, unit) to populate or refresh the panel.
    Call clear() to return the panel to its empty placeholder state.
    """

    def __init__(self, parent: tk.Widget, **kwargs):
        bg = COLORS["bg_panel"]
        super().__init__(parent, bg=bg, **kwargs)

        self._icon_ref: Optional[tk.PhotoImage] = None  # keep reference alive
        self._build_ui()

    # ─── UI Construction ───────────────────────────────────────────────────

    def _build_ui(self) -> None:
        """Build the static panel skeleton; data slots start empty."""
        self.configure(bg=COLORS["bg_panel"])

        # Section header
        header_bar = styled_frame(self, bg_key="bg_panel")
        header_bar.pack(fill=tk.X, padx=PAD["lg"], pady=(PAD["lg"], 0))

        styled_label(
            header_bar,
            text="CURRENT WEATHER",
            font_key="section_head",
            color_key="accent",
            bg_key="bg_panel",
        ).pack(side=tk.LEFT)

        separator(self).pack(fill=tk.X, padx=PAD["lg"], pady=(PAD["xs"], PAD["md"]))

        # Location name
        self._location_var = tk.StringVar(value="")
        self._location_label = styled_label(
            self,
            font_key="city_name",
            color_key="text_primary",
            bg_key="bg_panel",
            textvariable=self._location_var,
        )
        self._location_label.pack(pady=(0, PAD["sm"]))

        # Weather icon
        self._icon_label = tk.Label(
            self,
            bg=COLORS["bg_panel"],
            text="",
        )
        self._icon_label.pack()

        # Main temperature
        self._temp_var = tk.StringVar(value="")
        self._temp_label = tk.Label(
            self,
            textvariable=self._temp_var,
            font=FONTS["temp_large"],
            fg=COLORS["accent"],
            bg=COLORS["bg_panel"],
        )
        self._temp_label.pack(pady=(PAD["xs"], 0))

        # Both units displayed together
        self._both_temps_var = tk.StringVar(value="")
        styled_label(
            self,
            textvariable=self._both_temps_var,
            font_key="body",
            color_key="text_secondary",
            bg_key="bg_panel",
        ).pack()

        # Condition description
        self._condition_var = tk.StringVar(value="")
        styled_label(
            self,
            textvariable=self._condition_var,
            font_key="condition",
            color_key="text_secondary",
            bg_key="bg_panel",
        ).pack(pady=(PAD["xs"], PAD["md"]))

        separator(self).pack(fill=tk.X, padx=PAD["lg"], pady=(0, PAD["md"]))

        # Details grid
        details_frame = styled_frame(self, bg_key="bg_panel")
        details_frame.pack(padx=PAD["xl"], pady=(0, PAD["lg"]), fill=tk.X)
        details_frame.columnconfigure((0, 1), weight=1)

        self._feels_var = tk.StringVar(value="")
        self._humidity_var = tk.StringVar(value="")
        self._wind_var = tk.StringVar(value="")
        self._pressure_var = tk.StringVar(value="")
        self._visibility_var = tk.StringVar(value="")

        detail_pairs = [
            ("🌡️  Feels Like", self._feels_var, 0, 0),
            ("💧  Humidity",   self._humidity_var, 0, 1),
            ("💨  Wind",       self._wind_var,    1, 0),
            ("📊  Pressure",   self._pressure_var, 1, 1),
            ("👁️  Visibility", self._visibility_var, 2, 0),
        ]

        for label_text, var, row, col in detail_pairs:
            cell = styled_frame(details_frame, bg_key="bg_card")
            cell.configure(
                relief=tk.FLAT,
                bd=0,
                highlightbackground=COLORS["border"],
                highlightthickness=1,
            )
            cell.grid(row=row, column=col, padx=PAD["sm"], pady=PAD["xs"], sticky="ew")

            styled_label(
                cell,
                text=label_text,
                font_key="detail_label",
                color_key="text_muted",
                bg_key="bg_card",
            ).pack(anchor=tk.W, padx=PAD["sm"], pady=(PAD["xs"], 0))

            tk.Label(
                cell,
                textvariable=var,
                font=FONTS["detail_value"],
                fg=COLORS["text_primary"],
                bg=COLORS["bg_card"],
            ).pack(anchor=tk.W, padx=PAD["sm"], pady=(0, PAD["xs"]))

        self._details_frame = details_frame

    # ─── Public API ────────────────────────────────────────────────────────

    def update(self, data: WeatherData, unit: str) -> None:
        """
        Populate the panel with current weather data.

        Args:
            data: Normalized WeatherData instance.
            unit: "C" or "F".
        """
        cur = data.current
        loc = data.location

        self._location_var.set(loc.display_name)
        self._condition_var.set(cur.description)

        # Temperatures
        temp_display = format_temp(cur.temp_c, unit)
        self._temp_var.set(temp_display)

        c_str = f"{cur.temp_c:.1f}°C"
        f_str = f"{celsius_to_fahrenheit(cur.temp_c):.1f}°F"
        self._both_temps_var.set(f"{c_str}  /  {f_str}")

        # Detail fields
        feels = format_temp(cur.feels_like_c, unit)
        self._feels_var.set(feels)
        self._humidity_var.set(f"{cur.humidity}%")
        self._wind_var.set(f"{cur.wind_speed:.1f} m/s")
        self._pressure_var.set(f"{cur.pressure} hPa")

        if cur.visibility is not None:
            vis_km = cur.visibility / 1000
            self._visibility_var.set(f"{vis_km:.1f} km")
        else:
            self._visibility_var.set("N/A")

        # Icon (async-safe: we call from the main thread after fetch completes)
        self._load_icon(cur.icon_code)

    def refresh_unit(self, data: WeatherData, unit: str) -> None:
        """Re-render temperatures only (for unit toggle without re-fetching)."""
        cur = data.current
        temp_display = format_temp(cur.temp_c, unit)
        self._temp_var.set(temp_display)
        feels = format_temp(cur.feels_like_c, unit)
        self._feels_var.set(feels)

    def clear(self) -> None:
        """Reset all data fields to empty strings."""
        for var in (
            self._location_var, self._temp_var, self._both_temps_var,
            self._condition_var, self._feels_var, self._humidity_var,
            self._wind_var, self._pressure_var, self._visibility_var,
        ):
            var.set("")
        self._icon_label.configure(image="", text="")
        self._icon_ref = None

    # ─── Private Helpers ───────────────────────────────────────────────────

    def _load_icon(self, icon_code: str) -> None:
        """Download and display the weather icon (80 px)."""
        photo = load_weather_icon(icon_code, size=80)
        if photo:
            self._icon_ref = photo
            self._icon_label.configure(image=photo, text="")
        else:
            self._icon_ref = None
            self._icon_label.configure(image="", text="🌤️", font=FONTS["temp_medium"])
