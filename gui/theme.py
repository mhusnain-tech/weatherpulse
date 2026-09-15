"""
WeatherPulse — GUI Design Tokens & Shared Utilities

Centralizes colors, fonts, spacing, and helper widget factories so all
GUI panels share a consistent look without repeating style definitions.
"""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont


# ─── Color Palette ────────────────────────────────────────────────────────────

COLORS = {
    # Backgrounds
    "bg_root":      "#0d1b2a",   # deep navy — root window
    "bg_panel":     "#1a2a3a",   # card surface
    "bg_header":    "#0a1520",   # darker header strip
    "bg_input":     "#243447",   # entry field
    "bg_card":      "#1e3145",   # hourly/daily card
    "bg_hover":     "#2a4060",   # card hover

    # Accents
    "accent":       "#4a9eff",   # primary blue
    "accent_dark":  "#2a7fd4",   # button hover
    "accent_green": "#4caf82",   # positive indicators
    "accent_warn":  "#f0a840",   # warning yellow

    # Text
    "text_primary":   "#e8f0fe",  # primary white-ish
    "text_secondary": "#8eb4d8",  # muted blue-grey
    "text_muted":     "#5a7a9a",  # very muted
    "text_error":     "#ff6b6b",  # error red
    "text_success":   "#4caf82",  # success green

    # Borders
    "border":       "#2a4060",
    "border_light": "#3a5070",

    # Buttons
    "btn_primary":  "#4a9eff",
    "btn_hover":    "#2a7fd4",
    "btn_disabled": "#2a3a4a",
    "btn_detect":   "#243447",
    "btn_detect_hover": "#2a4060",

    # Unit toggle
    "toggle_active":   "#4a9eff",
    "toggle_inactive": "#1a2a3a",
}


# ─── Font Definitions ─────────────────────────────────────────────────────────

FONTS = {
    "app_title":    ("Segoe UI", 22, "bold"),
    "app_tagline":  ("Segoe UI", 10),
    "section_head": ("Segoe UI", 11, "bold"),
    "city_name":    ("Segoe UI", 20, "bold"),
    "temp_large":   ("Segoe UI", 44, "bold"),
    "temp_medium":  ("Segoe UI", 18, "bold"),
    "temp_small":   ("Segoe UI", 13, "bold"),
    "condition":    ("Segoe UI", 14),
    "detail_label": ("Segoe UI", 10),
    "detail_value": ("Segoe UI", 11, "bold"),
    "card_time":    ("Segoe UI", 9, "bold"),
    "card_temp":    ("Segoe UI", 12, "bold"),
    "card_cond":    ("Segoe UI", 8),
    "day_name":     ("Segoe UI", 10, "bold"),
    "body":         ("Segoe UI", 10),
    "small":        ("Segoe UI", 9),
    "status":       ("Segoe UI", 10, "italic"),
    "error":        ("Segoe UI", 10, "bold"),
    "button":       ("Segoe UI", 11, "bold"),
}


# ─── Spacing ─────────────────────────────────────────────────────────────────

PAD = {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24}


# ─── Widget Factories ─────────────────────────────────────────────────────────

def styled_label(
    parent: tk.Widget,
    text: str = "",
    font_key: str = "body",
    color_key: str = "text_primary",
    bg_key: str = "bg_panel",
    **kwargs,
) -> tk.Label:
    """Create a consistently styled Label."""
    return tk.Label(
        parent,
        text=text,
        font=FONTS.get(font_key, FONTS["body"]),
        fg=COLORS.get(color_key, COLORS["text_primary"]),
        bg=COLORS.get(bg_key, COLORS["bg_panel"]),
        **kwargs,
    )


def styled_frame(
    parent: tk.Widget,
    bg_key: str = "bg_panel",
    **kwargs,
) -> tk.Frame:
    """Create a consistently styled Frame."""
    return tk.Frame(
        parent,
        bg=COLORS.get(bg_key, COLORS["bg_panel"]),
        **kwargs,
    )


def separator(parent: tk.Widget, bg_key: str = "border") -> tk.Frame:
    """Thin horizontal separator line."""
    return tk.Frame(
        parent,
        height=1,
        bg=COLORS.get(bg_key, COLORS["border"]),
    )
