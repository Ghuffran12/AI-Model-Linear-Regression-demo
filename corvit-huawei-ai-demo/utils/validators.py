"""
Input validation for plot dimensions, measurement units, localities
and the supported prediction range.

Every function here either returns a cleaned value or raises
ValidationError with a clear, user-safe message (never an internal
stack trace or file path) — the Flask layer in app.py catches
ValidationError and turns it straight into a structured JSON error
response with an appropriate HTTP status code.
"""

import math
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import config
from utils.area_converter import SUPPORTED_UNITS


class ValidationError(Exception):
    """A user-facing validation failure. The message is safe to show as-is."""

    def __init__(self, message):
        self.message = message
        super().__init__(message)


def is_finite_number(value):
    """True only for values that convert cleanly to a finite float (rejects NaN/inf)."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(f)


def validate_unit(unit):
    unit = (unit or "sqyd").strip().lower()
    if unit not in SUPPORTED_UNITS:
        raise ValidationError(
            f"Unsupported measurement unit '{unit}'. Supported units: {', '.join(SUPPORTED_UNITS)}."
        )
    return unit


def validate_positive_number(value, field_name):
    if value is None or value == "":
        raise ValidationError(f"{field_name} is required.")
    if not is_finite_number(value):
        raise ValidationError(f"{field_name} must be a valid number.")
    value = float(value)
    if value <= 0:
        raise ValidationError(f"{field_name} must be greater than zero.")
    return value


def validate_location(location):
    """Returns None for 'no preference', the cleaned location string, or raises."""
    if location in (None, "", "any", "Any", "any_location"):
        return None
    if location not in config.LOCATIONS:
        raise ValidationError(
            f"'{location}' is not a supported locality. Supported localities: {', '.join(config.LOCATIONS)}."
        )
    return location


def validate_dimensions_consistency(length_sqyd, breadth_sqyd, area_sqyd, tolerance=0.02):
    """
    If both an explicit area AND length/breadth were supplied (already
    converted to the same unit — square yards), make sure they roughly
    agree. `tolerance` is a relative tolerance (default 2%) to allow
    for ordinary rounding, not a loophole for genuinely different
    numbers.
    """
    if length_sqyd is None or breadth_sqyd is None or area_sqyd is None:
        return True

    computed = length_sqyd * breadth_sqyd
    if computed <= 0:
        raise ValidationError("Plot length and breadth must produce a positive area.")

    relative_diff = abs(computed - area_sqyd) / computed
    if relative_diff > tolerance:
        raise ValidationError(
            "The provided plot area is inconsistent with length x breadth. "
            f"Length x breadth = {computed:,.2f} sq yards, but the entered area = {area_sqyd:,.2f} sq yards."
        )
    return True


def validate_prediction_range(area_sqyd):
    """
    Enforce the supported square-yard PREDICTION range specifically.
    This always operates on the canonical square-yard value, so a plot
    entered in acres or square feet cannot silently bypass the limit —
    conversion and the prediction range are deliberately kept separate.
    """
    if area_sqyd < config.MIN_PREDICTION_SQYD or area_sqyd > config.MAX_PREDICTION_SQYD:
        raise ValidationError(
            "Prediction Not Available: Please enter a plot size between "
            f"{config.MIN_PREDICTION_SQYD:,.0f} and {config.MAX_PREDICTION_SQYD:,.0f} square yards."
        )
    return True
