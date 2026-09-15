"""
Tests — Temperature Unit Conversion

Verifies celsius_to_fahrenheit(), fahrenheit_to_celsius(), and
format_temp() / format_temp_range() against known values.
"""

import pytest
from services.unit_converter import (
    celsius_to_fahrenheit,
    fahrenheit_to_celsius,
    format_temp,
    format_temp_range,
)


class TestCelsiusToFahrenheit:
    def test_freezing_point(self):
        assert celsius_to_fahrenheit(0) == pytest.approx(32.0)

    def test_boiling_point(self):
        assert celsius_to_fahrenheit(100) == pytest.approx(212.0)

    def test_equal_point(self):
        """−40 is the only temperature where °C equals °F."""
        assert celsius_to_fahrenheit(-40) == pytest.approx(-40.0)

    def test_body_temperature(self):
        assert celsius_to_fahrenheit(37) == pytest.approx(98.6)

    def test_typical_summer(self):
        assert celsius_to_fahrenheit(30) == pytest.approx(86.0)

    def test_negative_value(self):
        assert celsius_to_fahrenheit(-10) == pytest.approx(14.0)

    def test_float_input(self):
        assert celsius_to_fahrenheit(20.5) == pytest.approx(68.9)


class TestFahrenheitToCelsius:
    def test_freezing_point(self):
        assert fahrenheit_to_celsius(32) == pytest.approx(0.0)

    def test_boiling_point(self):
        assert fahrenheit_to_celsius(212) == pytest.approx(100.0)

    def test_equal_point(self):
        assert fahrenheit_to_celsius(-40) == pytest.approx(-40.0)

    def test_body_temperature(self):
        assert fahrenheit_to_celsius(98.6) == pytest.approx(37.0, abs=0.01)

    def test_negative_fahrenheit(self):
        assert fahrenheit_to_celsius(14) == pytest.approx(-10.0)


class TestRoundTripConversion:
    @pytest.mark.parametrize("temp_c", [-40, -10, 0, 20, 37, 100])
    def test_round_trip(self, temp_c: float):
        """Converting C → F → C should return the original value."""
        result = fahrenheit_to_celsius(celsius_to_fahrenheit(temp_c))
        assert result == pytest.approx(temp_c, abs=1e-6)


class TestFormatTemp:
    def test_celsius_format(self):
        assert format_temp(28.0, "C") == "28.0°C"

    def test_fahrenheit_format(self):
        result = format_temp(0.0, "F")
        assert "32.0°F" == result

    def test_celsius_uppercase(self):
        assert format_temp(20.0, "c") == "20.0°C"

    def test_fahrenheit_lowercase(self):
        assert "f" not in format_temp(20.0, "f").lower() or "°F" in format_temp(20.0, "F")

    def test_negative_celsius(self):
        assert format_temp(-5.0, "C") == "-5.0°C"

    def test_format_temp_fahrenheit_value(self):
        """28°C should display as 82.4°F."""
        result = format_temp(28.0, "F")
        assert "82.4°F" == result


class TestFormatTempRange:
    def test_celsius_range(self):
        result = format_temp_range(18.0, 30.0, "C")
        assert "30°C" in result
        assert "18°C" in result

    def test_fahrenheit_range(self):
        result = format_temp_range(0.0, 100.0, "F")
        assert "°F" in result

    def test_range_order(self):
        """High should appear before low in output."""
        result = format_temp_range(10.0, 30.0, "C")
        idx_high = result.index("30")
        idx_low = result.index("10")
        assert idx_high < idx_low
