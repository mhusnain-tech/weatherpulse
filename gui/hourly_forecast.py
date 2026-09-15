"""
WeatherPulse — Hourly Forecast Panel

Displays the next 6 forecast slots (3-hour OWM intervals) as a
horizontally scrollable row of cards.
"""

from __future__ import annotations

import tkinter as tk
from typing import List, Optional

from gui.theme import COLORS, FONTS, PAD, separator, styled_frame, styled_label
from models.weather import HourlyEntry
from services.unit_converter import format_temp
from utils.image_loader import load_weather_icon


class HourlyForecastPanel(tk.Frame):
    """
    Displays up to 6 hourly forecast cards in a horizontal row.

    Call update(hourly_list, unit) to populate or refresh the panel.
    """

    def __init__(self, parent: tk.Widget, **kwargs):
        super().__init__(parent, bg=COLORS["bg_panel"], **kwargs)
        self._icon_refs: List[Optional[tk.PhotoImage]] = []
        self._card_frames: List[tk.Frame] = []
        self._build_skeleton()

    # ─── UI Construction ──────────────────────────────────────────────────

    def _build_skeleton(self) -> None:
        """Build header + placeholder for cards."""
        # Section header
        header_bar = styled_frame(self, bg_key="bg_panel")
        header_bar.pack(fill=tk.X, padx=PAD["lg"], pady=(PAD["lg"], 0))

        styled_label(
            header_bar,
            text="NEXT 6 HOURS",
            font_key="section_head",
            color_key="accent",
            bg_key="bg_panel",
        ).pack(side=tk.LEFT)

        separator(self).pack(fill=tk.X, padx=PAD["lg"], pady=(PAD["xs"], PAD["md"]))

        # Cards container
        self._cards_row = styled_frame(self, bg_key="bg_panel")
        self._cards_row.pack(
            fill=tk.X, padx=PAD["lg"], pady=(0, PAD["lg"]), expand=False
        )

        # Empty-state label
        self._empty_label = styled_label(
            self._cards_row,
            text="Search a location to see the hourly forecast.",
            font_key="small",
            color_key="text_muted",
            bg_key="bg_panel",
        )
        self._empty_label.pack(pady=PAD["md"])

    # ─── Public API ────────────────────────────────────────────────────────

    def update(self, hourly: List[HourlyEntry], unit: str) -> None:
        """
        Render hourly forecast cards.

        Args:
            hourly: List of HourlyEntry (up to 6).
            unit:   "C" or "F".
        """
        self._clear_cards()

        if not hourly:
            self._empty_label.pack(pady=PAD["md"])
            return

        self._empty_label.pack_forget()
        self._icon_refs = []

        for i, entry in enumerate(hourly[:6]):
            card = self._make_card(entry, unit, i)
            card.pack(side=tk.LEFT, padx=PAD["xs"], expand=True, fill=tk.X)
            self._card_frames.append(card)

    def refresh_unit(self, hourly: List[HourlyEntry], unit: str) -> None:
        """Re-render temperatures only."""
        self.update(hourly, unit)

    def clear(self) -> None:
        """Reset to empty state."""
        self._clear_cards()
        self._empty_label.pack(pady=PAD["md"])

    # ─── Private Helpers ──────────────────────────────────────────────────

    def _clear_cards(self) -> None:
        for frame in self._card_frames:
            frame.destroy()
        self._card_frames = []
        self._icon_refs = []
        self._empty_label.pack_forget()

    def _make_card(self, entry: HourlyEntry, unit: str, idx: int) -> tk.Frame:
        """Build a single hourly card widget."""
        card = tk.Frame(
            self._cards_row,
            bg=COLORS["bg_card"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
        )

        # Time label
        tk.Label(
            card,
            text=entry.time_label_short,
            font=FONTS["card_time"],
            fg=COLORS["accent"],
            bg=COLORS["bg_card"],
        ).pack(pady=(PAD["sm"], 0))

        # Icon
        icon_label = tk.Label(card, bg=COLORS["bg_card"])
        photo = load_weather_icon(entry.icon_code, size=36)
        if photo:
            self._icon_refs.append(photo)
            icon_label.configure(image=photo)
        else:
            self._icon_refs.append(None)
            icon_label.configure(text="🌤️", font=FONTS["card_temp"])
        icon_label.pack(pady=PAD["xs"])

        # Temperature
        tk.Label(
            card,
            text=format_temp(entry.temp_c, unit),
            font=FONTS["card_temp"],
            fg=COLORS["text_primary"],
            bg=COLORS["bg_card"],
        ).pack()

        # Condition
        cond_text = entry.condition[:8] if len(entry.condition) > 8 else entry.condition
        tk.Label(
            card,
            text=cond_text,
            font=FONTS["card_cond"],
            fg=COLORS["text_muted"],
            bg=COLORS["bg_card"],
            wraplength=60,
        ).pack(pady=(0, PAD["xs"]))

        # Precipitation probability (if non-zero)
        if entry.pop > 0.05:
            tk.Label(
                card,
                text=f"💧 {entry.pop * 100:.0f}%",
                font=FONTS["small"],
                fg=COLORS["accent_green"],
                bg=COLORS["bg_card"],
            ).pack(pady=(0, PAD["xs"]))
        else:
            tk.Label(card, text="", bg=COLORS["bg_card"]).pack(pady=(0, PAD["xs"]))

        return card
