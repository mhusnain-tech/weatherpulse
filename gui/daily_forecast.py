"""
WeatherPulse — Daily Forecast Panel

Displays 5 days of aggregated weather as a clean table with
day name, icon, condition, high/low temperatures, and precipitation.
"""

from __future__ import annotations

import tkinter as tk
from typing import List, Optional

from gui.theme import COLORS, FONTS, PAD, separator, styled_frame, styled_label
from models.weather import DailyEntry
from services.unit_converter import format_temp_range
from utils.image_loader import load_weather_icon


class DailyForecastPanel(tk.Frame):
    """
    Renders a 5-row daily forecast table.

    Call update(daily_list, unit) to populate or refresh the panel.
    """

    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, bg=COLORS["bg_panel"], **kwargs)
        self._icon_refs: List[Optional[tk.PhotoImage]] = []
        self._row_frames: List[tk.Frame] = []
        self._build_skeleton()

    # ─── UI Construction ──────────────────────────────────────────────────

    def _build_skeleton(self) -> None:
        # Section header
        header_bar = styled_frame(self, bg_key="bg_panel")
        header_bar.pack(fill=tk.X, padx=PAD["lg"], pady=(PAD["lg"], 0))

        styled_label(
            header_bar,
            text="5-DAY FORECAST",
            font_key="section_head",
            color_key="accent",
            bg_key="bg_panel",
        ).pack(side=tk.LEFT)

        separator(self).pack(fill=tk.X, padx=PAD["lg"], pady=(PAD["xs"], PAD["sm"]))

        # Rows container
        self._rows_frame = styled_frame(self, bg_key="bg_panel")
        self._rows_frame.pack(fill=tk.X, padx=PAD["lg"], pady=(0, PAD["lg"]))

        self._empty_label = styled_label(
            self._rows_frame,
            text="Search a location to see the 5-day forecast.",
            font_key="small",
            color_key="text_muted",
            bg_key="bg_panel",
        )
        self._empty_label.pack(pady=PAD["md"])

    # ─── Public API ────────────────────────────────────────────────────────

    def update(self, daily: List[DailyEntry], unit: str) -> None:
        """
        Render daily forecast rows.

        Args:
            daily: List of DailyEntry (up to 5).
            unit:  "C" or "F".
        """
        self._clear_rows()

        if not daily:
            self._empty_label.pack(pady=PAD["md"])
            return

        self._empty_label.pack_forget()
        self._icon_refs = []

        for i, entry in enumerate(daily[:5]):
            row = self._make_row(entry, unit, i)
            row.pack(fill=tk.X, padx=PAD["xs"], pady=2)
            self._row_frames.append(row)

    def refresh_unit(self, daily: List[DailyEntry], unit: str) -> None:
        """Re-render temperatures only — convenience wrapper."""
        self.update(daily, unit)

    def clear(self) -> None:
        """Reset to empty state."""
        self._clear_rows()
        self._empty_label.pack(pady=PAD["md"])

    # ─── Private Helpers ──────────────────────────────────────────────────

    def _clear_rows(self) -> None:
        for frame in self._row_frames:
            frame.destroy()
        self._row_frames = []
        self._icon_refs = []
        self._empty_label.pack_forget()

    def _make_row(self, entry: DailyEntry, unit: str, idx: int) -> tk.Frame:
        """Build a single daily row with alternating background."""
        row_bg = COLORS["bg_card"] if idx % 2 == 0 else COLORS["bg_panel"]

        row = tk.Frame(
            self._rows_frame,
            bg=row_bg,
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )

        # Configure 4 columns: day | icon | condition | temps
        row.columnconfigure(0, minsize=70)
        row.columnconfigure(1, minsize=44)
        row.columnconfigure(2, weight=1)
        row.columnconfigure(3, minsize=120)

        # Day name
        tk.Label(
            row,
            text=entry.day_name,
            font=FONTS["day_name"],
            fg=COLORS["text_primary"],
            bg=row_bg,
            anchor=tk.W,
        ).grid(row=0, column=0, padx=(PAD["md"], PAD["xs"]), pady=PAD["sm"], sticky="w")

        # Icon
        icon_lbl = tk.Label(row, bg=row_bg)
        photo = load_weather_icon(entry.icon_code, size=32)
        if photo:
            self._icon_refs.append(photo)
            icon_lbl.configure(image=photo)
        else:
            self._icon_refs.append(None)
            icon_lbl.configure(text="🌤️", font=FONTS["card_temp"])
        icon_lbl.grid(row=0, column=1, padx=PAD["xs"], pady=PAD["xs"])

        # Condition
        tk.Label(
            row,
            text=entry.condition,
            font=FONTS["body"],
            fg=COLORS["text_secondary"],
            bg=row_bg,
            anchor=tk.W,
        ).grid(row=0, column=2, padx=PAD["xs"], pady=PAD["sm"], sticky="w")

        # Temperature range
        temp_str = format_temp_range(entry.temp_min_c, entry.temp_max_c, unit)

        # Add rain if notable
        if entry.pop > 0.1:
            temp_str += f"  💧{entry.pop * 100:.0f}%"

        tk.Label(
            row,
            text=temp_str,
            font=FONTS["temp_small"],
            fg=COLORS["accent"],
            bg=row_bg,
            anchor=tk.E,
        ).grid(row=0, column=3, padx=(PAD["xs"], PAD["md"]), pady=PAD["sm"], sticky="e")

        return row
