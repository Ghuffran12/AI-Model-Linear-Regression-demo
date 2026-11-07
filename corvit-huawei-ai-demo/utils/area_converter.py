"""
Land measurement conversions between square yards, square feet,
square meters and acres, plus plot length x breadth area math.

Documented conversion constants (as specified by the project):
    1 square yard  = 9 square feet
    1 square yard  = 0.836127 square meters
    1 acre         = 4,840 square yards
    1 acre         = 43,560 square feet
"""

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import config

SUPPORTED_UNITS = ("sqyd", "sqft", "sqm", "acre")


def sqyd_to_sqft(value):
    return value * config.SQFT_PER_SQYD


def sqyd_to_sqm(value):
    return value * config.SQM_PER_SQYD


def sqyd_to_acres(value):
    return value / config.SQYD_PER_ACRE


def sqft_to_sqyd(value):
    return value / config.SQFT_PER_SQYD


def sqm_to_sqyd(value):
    return value / config.SQM_PER_SQYD


def acres_to_sqyd(value):
    return value * config.SQYD_PER_ACRE


def to_sqyd(value, unit):
    """Convert a value in the given unit into square yards."""
    unit = (unit or "sqyd").lower()
    value = float(value)
    if unit == "sqyd":
        return value
    if unit == "sqft":
        return sqft_to_sqyd(value)
    if unit == "sqm":
        return sqm_to_sqyd(value)
    if unit == "acre":
        return acres_to_sqyd(value)
    raise ValueError(f"Unsupported unit: {unit}")


def from_sqyd(value_sqyd, unit):
    """Convert a square-yard value into the requested unit."""
    unit = (unit or "sqyd").lower()
    value_sqyd = float(value_sqyd)
    if unit == "sqyd":
        return value_sqyd
    if unit == "sqft":
        return sqyd_to_sqft(value_sqyd)
    if unit == "sqm":
        return sqyd_to_sqm(value_sqyd)
    if unit == "acre":
        return sqyd_to_acres(value_sqyd)
    raise ValueError(f"Unsupported unit: {unit}")


def all_units(value_sqyd):
    """Return the equivalent area in every supported unit, from a square-yard value."""
    value_sqyd = float(value_sqyd)
    return {
        "sqyd": round(value_sqyd, 2),
        "sqft": round(sqyd_to_sqft(value_sqyd), 2),
        "sqm": round(sqyd_to_sqm(value_sqyd), 2),
        "acre": round(sqyd_to_acres(value_sqyd), 4),
    }


def area_from_dimensions(length, breadth):
    """Area = length x breadth, in whatever unit length/breadth are expressed in."""
    return float(length) * float(breadth)


def estimate_dimensions_from_area(area, ratio=1.0):
    """
    Estimate plausible Length/Breadth for a given area using a
    length:breadth ratio (default 1.0, i.e. a square plot).

    These are ESTIMATED dimensions, not surveyed measurements — every
    caller must present them to the user clearly labelled as such
    (the returned dict's "estimated" flag exists for that purpose).
    """
    area = float(area)
    ratio = float(ratio) if ratio else 1.0
    if ratio <= 0:
        ratio = 1.0
    breadth = (area / ratio) ** 0.5
    length = ratio * breadth
    return {"length": round(length, 2), "breadth": round(breadth, 2), "estimated": True}
