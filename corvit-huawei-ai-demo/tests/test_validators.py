"""
Tests for utils/validators.py — input validation and the supported
prediction range.

Covers the project spec's required checks (section 13 / section 8):
rejecting empty, negative, non-numeric, NaN/infinite, invalid-unit and
invalid-locality values; detecting inconsistent length/breadth vs. area;
and enforcing the 120-10,000 sq yd prediction boundary with the exact
required message.
"""

import math

import pytest

from config import config
from utils.validators import (
    ValidationError,
    is_finite_number,
    validate_dimensions_consistency,
    validate_location,
    validate_positive_number,
    validate_prediction_range,
    validate_unit,
)


# ---------------------------------------------------------------------
# is_finite_number
# ---------------------------------------------------------------------

@pytest.mark.parametrize("value", [5, 5.5, "5", "5.5", "0.001", -3])
def test_is_finite_number_accepts_valid_numbers(value):
    assert is_finite_number(value) is True


@pytest.mark.parametrize(
    "value",
    [float("nan"), float("inf"), float("-inf"), "nan", "inf", "abc", None, "", "12a", [1, 2]],
)
def test_is_finite_number_rejects_non_finite_and_junk(value):
    assert is_finite_number(value) is False


# ---------------------------------------------------------------------
# validate_unit
# ---------------------------------------------------------------------

@pytest.mark.parametrize("unit", ["sqyd", "sqft", "sqm", "acre", "SqYd", " ACRE "])
def test_validate_unit_accepts_supported_units_case_insensitively(unit):
    assert validate_unit(unit) in ("sqyd", "sqft", "sqm", "acre")


@pytest.mark.parametrize("value", [None, ""])
def test_validate_unit_defaults_to_sqyd_when_omitted(value):
    # Mirrors validate_location's "no preference" handling: an absent
    # or empty unit is treated as "not specified", not as an invalid
    # value, and falls back to the default rather than erroring.
    assert validate_unit(value) == "sqyd"


@pytest.mark.parametrize("unit", ["furlong", "hectare", "sq_yard", "yards"])
def test_validate_unit_rejects_unsupported_units(unit):
    with pytest.raises(ValidationError):
        validate_unit(unit)


# ---------------------------------------------------------------------
# validate_positive_number
# ---------------------------------------------------------------------

def test_validate_positive_number_accepts_valid_value():
    assert validate_positive_number("500", "Plot area") == pytest.approx(500.0)
    assert validate_positive_number(500, "Plot area") == pytest.approx(500.0)


@pytest.mark.parametrize("value", [None, ""])
def test_validate_positive_number_rejects_missing(value):
    with pytest.raises(ValidationError):
        validate_positive_number(value, "Plot area")


@pytest.mark.parametrize("value", [0, -1, -500, "0", "-10"])
def test_validate_positive_number_rejects_zero_or_negative(value):
    with pytest.raises(ValidationError):
        validate_positive_number(value, "Plot area")


@pytest.mark.parametrize("value", ["abc", "fifty", "12a", float("nan"), float("inf")])
def test_validate_positive_number_rejects_non_numeric_and_non_finite(value):
    with pytest.raises(ValidationError):
        validate_positive_number(value, "Plot area")


# ---------------------------------------------------------------------
# validate_location (the optional locality selector)
# ---------------------------------------------------------------------

@pytest.mark.parametrize("value", [None, "", "any", "Any", "any_location"])
def test_validate_location_treats_omitted_as_no_preference(value):
    assert validate_location(value) is None


def test_validate_location_accepts_a_supported_locality():
    loc = config.LOCATIONS[1]
    assert validate_location(loc) == loc


def test_validate_location_rejects_unsupported_locality():
    with pytest.raises(ValidationError):
        validate_location("Atlantis Heights")


# ---------------------------------------------------------------------
# validate_dimensions_consistency — spec example: 40 x 30 yd = 1,200 sq yd
# ---------------------------------------------------------------------

def test_consistency_accepts_matching_area():
    assert validate_dimensions_consistency(40, 30, 1200) is True


def test_consistency_accepts_small_rounding_differences():
    # Within the 2% default tolerance.
    assert validate_dimensions_consistency(40, 30, 1210) is True


def test_consistency_rejects_grossly_mismatched_area():
    with pytest.raises(ValidationError):
        validate_dimensions_consistency(40, 30, 5000)


def test_consistency_skipped_when_any_value_missing():
    # Only enforced when area AND both dimensions are explicitly given.
    assert validate_dimensions_consistency(None, 30, 1200) is True
    assert validate_dimensions_consistency(40, None, 1200) is True
    assert validate_dimensions_consistency(40, 30, None) is True


def test_consistency_rejects_non_positive_product():
    with pytest.raises(ValidationError):
        validate_dimensions_consistency(0, 30, 0)


# ---------------------------------------------------------------------
# validate_prediction_range — the 120-10,000 sq yd boundary
# ---------------------------------------------------------------------

def test_prediction_range_accepts_inclusive_boundaries():
    assert validate_prediction_range(config.MIN_PREDICTION_SQYD) is True
    assert validate_prediction_range(config.MAX_PREDICTION_SQYD) is True


def test_prediction_range_accepts_mid_range_value():
    assert validate_prediction_range(500) is True


@pytest.mark.parametrize(
    "area",
    [
        0,
        1,
        119,
        119.999,
        config.MAX_PREDICTION_SQYD + 0.001,
        10001,
        50000,
    ],
)
def test_prediction_range_rejects_out_of_range_values(area):
    with pytest.raises(ValidationError) as exc_info:
        validate_prediction_range(area)
    message = str(exc_info.value)
    assert "Prediction Not Available" in message
    assert "120" in message
    assert "10,000" in message


def test_prediction_range_message_matches_spec_wording():
    with pytest.raises(ValidationError) as exc_info:
        validate_prediction_range(50)
    assert str(exc_info.value) == (
        "Prediction Not Available: Please enter a plot size between 120 and 10,000 square yards."
    )
