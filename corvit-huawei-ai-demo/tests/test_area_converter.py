"""
Tests for utils/area_converter.py — unit conversions and plot-area math.

Covers the project spec's required checks: "Area conversions are correct"
and "Length multiplied by breadth produces the correct area" (section 13),
using the documented constants from the spec itself:
    1 sq yd = 9 sq ft
    1 sq yd = 0.836127 sq m
    1 acre  = 4,840 sq yd = 43,560 sq ft
"""

import math

import pytest

from utils import area_converter as ac


# ---------------------------------------------------------------------
# Documented conversion constants
# ---------------------------------------------------------------------

def test_sqyd_to_sqft():
    assert ac.sqyd_to_sqft(1) == pytest.approx(9.0)
    assert ac.sqyd_to_sqft(500) == pytest.approx(4500.0)


def test_sqyd_to_sqm():
    assert ac.sqyd_to_sqm(1) == pytest.approx(0.836127)
    assert ac.sqyd_to_sqm(1000) == pytest.approx(836.127)


def test_acre_conversions():
    assert ac.acres_to_sqyd(1) == pytest.approx(4840.0)
    assert ac.sqyd_to_acres(4840) == pytest.approx(1.0)
    assert ac.sqyd_to_sqft(4840) == pytest.approx(43560.0)  # 1 acre in sq ft, via sq yd


def test_inverse_conversions_are_consistent():
    assert ac.sqft_to_sqyd(9) == pytest.approx(1.0)
    assert ac.sqm_to_sqyd(0.836127) == pytest.approx(1.0, rel=1e-6)


@pytest.mark.parametrize("unit", ["sqyd", "sqft", "sqm", "acre"])
def test_round_trip_to_sqyd_and_back(unit):
    original = 1234.5
    value_sqyd = ac.to_sqyd(original, unit)
    back = ac.from_sqyd(value_sqyd, unit)
    assert back == pytest.approx(original, rel=1e-6)


def test_to_sqyd_is_identity_for_sqyd():
    assert ac.to_sqyd(777, "sqyd") == pytest.approx(777.0)


def test_to_sqyd_rejects_unsupported_unit():
    with pytest.raises(ValueError):
        ac.to_sqyd(100, "furlong")


def test_from_sqyd_rejects_unsupported_unit():
    with pytest.raises(ValueError):
        ac.from_sqyd(100, "hectare")


def test_all_units_matches_individual_conversions():
    # all_units() rounds each value for display (2dp for sqyd/sqft/sqm,
    # 4dp for acre), so compare with a tolerance that absorbs that
    # rounding rather than demanding exact equality with the raw value.
    result = ac.all_units(500)
    assert result["sqyd"] == pytest.approx(500.0, abs=0.01)
    assert result["sqft"] == pytest.approx(ac.sqyd_to_sqft(500), abs=0.01)
    assert result["sqm"] == pytest.approx(ac.sqyd_to_sqm(500), abs=0.01)
    assert result["acre"] == pytest.approx(ac.sqyd_to_acres(500), abs=0.0001)


# ---------------------------------------------------------------------
# Length x breadth area math (the spec's own worked example:
# 40 x 30 yd = 1,200 sq yd)
# ---------------------------------------------------------------------

def test_area_from_dimensions_matches_spec_example():
    assert ac.area_from_dimensions(40, 30) == pytest.approx(1200.0)


@pytest.mark.parametrize(
    "length,breadth,expected",
    [
        (50, 10, 500),
        (120, 1, 120),
        (100, 100, 10000),
        (25.5, 4, 102.0),
    ],
)
def test_area_from_dimensions_various(length, breadth, expected):
    assert ac.area_from_dimensions(length, breadth) == pytest.approx(expected)


# ---------------------------------------------------------------------
# Estimated dimensions from area alone
# ---------------------------------------------------------------------

def test_estimate_dimensions_from_area_default_is_square():
    dims = ac.estimate_dimensions_from_area(900, ratio=1.0)
    assert dims["length"] == pytest.approx(30.0)
    assert dims["breadth"] == pytest.approx(30.0)
    assert dims["estimated"] is True


@pytest.mark.parametrize("area,ratio", [(1200, 1.0), (500, 2.0), (10000, 0.5), (120, 1.5)])
def test_estimate_dimensions_reproduce_the_area(area, ratio):
    dims = ac.estimate_dimensions_from_area(area, ratio=ratio)
    reproduced = dims["length"] * dims["breadth"]
    assert reproduced == pytest.approx(area, rel=1e-2)
    assert dims["estimated"] is True  # must never be presented as a surveyed measurement


def test_estimate_dimensions_handles_missing_or_invalid_ratio():
    # A zero/negative/omitted ratio must fall back to a sane 1:1 square,
    # not raise or divide by zero.
    dims_zero = ac.estimate_dimensions_from_area(400, ratio=0)
    dims_none = ac.estimate_dimensions_from_area(400, ratio=None)
    assert math.isfinite(dims_zero["length"]) and dims_zero["length"] > 0
    assert dims_none["length"] == pytest.approx(dims_zero["length"])
