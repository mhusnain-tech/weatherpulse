"""
Tests — Input Validation

Verifies validate_location_input() correctly accepts valid input and
rejects empty, whitespace-only, too-long, and dangerous strings.
"""

import pytest
from api.exceptions import ValidationError
from utils.validators import validate_location_input


class TestValidInput:
    def test_simple_city_name(self):
        assert validate_location_input("London") == "London"

    def test_city_with_country(self):
        assert validate_location_input("London,UK") == "London,UK"

    def test_zip_code_us(self):
        assert validate_location_input("10001,US") == "10001,US"

    def test_zip_code_short(self):
        assert validate_location_input("90210") == "90210"

    def test_city_with_spaces(self):
        assert validate_location_input("New York") == "New York"

    def test_city_with_special_chars(self):
        """Accented characters are valid (real city names)."""
        assert validate_location_input("São Paulo") == "São Paulo"

    def test_numeric_zip(self):
        assert validate_location_input("12345") == "12345"

    def test_leading_trailing_spaces_stripped(self):
        result = validate_location_input("  Paris  ")
        assert result == "Paris"

    def test_internal_spaces_preserved(self):
        result = validate_location_input("  Los Angeles  ")
        assert result == "Los Angeles"


class TestEmptyInput:
    def test_empty_string(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_location_input("")
        assert "enter" in str(exc_info.value).lower()

    def test_whitespace_only_single_space(self):
        with pytest.raises(ValidationError):
            validate_location_input(" ")

    def test_whitespace_only_tabs(self):
        with pytest.raises(ValidationError):
            validate_location_input("\t\t")

    def test_whitespace_only_newlines(self):
        with pytest.raises(ValidationError):
            validate_location_input("\n\n")

    def test_whitespace_mixed(self):
        with pytest.raises(ValidationError):
            validate_location_input("   \t  \n  ")


class TestTooLongInput:
    def test_exactly_at_limit(self):
        """100-character input should pass."""
        result = validate_location_input("A" * 100)
        assert len(result) == 100

    def test_one_over_limit(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_location_input("A" * 101)
        assert "long" in str(exc_info.value).lower() or "100" in str(exc_info.value)

    def test_far_over_limit(self):
        with pytest.raises(ValidationError):
            validate_location_input("X" * 500)


class TestDangerousInput:
    @pytest.mark.parametrize("dangerous", [
        "city; rm -rf /",
        "city | cat /etc/passwd",
        "city & echo hacked",
        "city` echo hacked`",
        "city$(whoami)",
        "city<script>",
        "city>output.txt",
    ])
    def test_shell_injection_blocked(self, dangerous: str):
        with pytest.raises(ValidationError):
            validate_location_input(dangerous)


class TestErrorMessages:
    def test_empty_error_message_is_user_friendly(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_location_input("")
        message = str(exc_info.value)
        assert len(message) > 10
        assert message[0].isupper()

    def test_toolong_error_mentions_limit(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_location_input("A" * 200)
        assert "100" in str(exc_info.value)
