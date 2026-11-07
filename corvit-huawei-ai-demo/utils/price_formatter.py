"""
Currency and number formatting helpers for displaying model output
professionally (e.g. "PKR 12,500,000").
"""

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import config


def format_currency(amount, currency_code=None):
    currency_code = currency_code or config.CURRENCY_CODE
    return f"{currency_code} {amount:,.0f}"


def format_price_per_unit(amount, unit_label, currency_code=None):
    currency_code = currency_code or config.CURRENCY_CODE
    return f"{currency_code} {amount:,.2f} / {unit_label}"


def to_crore(amount):
    """Amount expressed in crore (1 crore = 10,000,000) — standard South-Asian convention."""
    return amount / 10_000_000


def to_lakh(amount):
    """Amount expressed in lakh (1 lakh = 100,000) — standard South-Asian convention."""
    return amount / 100_000
