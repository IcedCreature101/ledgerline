"""The currency table.

`exponent` is the number of minor units per major unit as a power of ten — 2 for USD (cents), 0 for JPY
(the yen has no subunit), 3 for BHD (fils). Hard-coding 100 anywhere is a bug waiting for a JPY merchant.
"""
from __future__ import annotations

from dataclasses import dataclass


class UnknownCurrency(KeyError):
    """A currency code that is not in the table. Never guess a default — guessing is how a JPY payment
    becomes a hundredfold error."""


@dataclass(frozen=True)
class Currency:
    code: str
    exponent: int
    symbol: str
    name: str


_TABLE: dict[str, Currency] = {
    "USD": Currency("USD", 2, "$", "US Dollar"),
    "EUR": Currency("EUR", 2, "€", "Euro"),
    "GBP": Currency("GBP", 2, "£", "Pound Sterling"),
    "JPY": Currency("JPY", 0, "¥", "Japanese Yen"),
    "CHF": Currency("CHF", 2, "CHF ", "Swiss Franc"),
    "SEK": Currency("SEK", 2, "kr ", "Swedish Krona"),
    "INR": Currency("INR", 2, "₹", "Indian Rupee"),
    "BHD": Currency("BHD", 3, "BD ", "Bahraini Dinar"),
}


def get_currency(code: str) -> Currency:
    if not isinstance(code, str):
        raise UnknownCurrency(f"currency code must be a string, got {type(code).__name__}")
    try:
        return _TABLE[code.upper()]
    except KeyError:
        raise UnknownCurrency(code) from None


def is_supported(code: str) -> bool:
    return isinstance(code, str) and code.upper() in _TABLE


def supported_codes() -> list[str]:
    return sorted(_TABLE)
