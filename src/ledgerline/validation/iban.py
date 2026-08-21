"""IBAN validation.

An IBAN carries its own checksum: move the first four characters to the end, replace every letter with
two digits (A=10 … Z=35) and the whole thing, read as one integer, is congruent to 1 modulo 97. That
catches transposed digits, which is the mistake a human actually makes when copying an account number.

The checksum says nothing about whether the account EXISTS — only that the string is not a typo. The
length check is the other half: every country publishes a fixed IBAN length, and a string of the wrong
length for its country is malformed however well it checksums.
"""
from __future__ import annotations

import re

_CLEAN = re.compile(r"[\s-]+")
_SHAPE = re.compile(r"^[A-Z]{2}[0-9]{2}[A-Z0-9]+$")

# Published IBAN lengths by country. A country absent from this table is one we do not process.
_LENGTHS: dict[str, int] = {
    "AT": 20, "BE": 16, "CH": 21, "CY": 28, "CZ": 24, "DE": 22, "DK": 18, "EE": 20,
    "ES": 24, "FI": 18, "FR": 27, "GB": 22, "GR": 27, "IE": 22, "IT": 27, "LT": 20,
    "LU": 20, "LV": 21, "NL": 18, "NO": 15, "PL": 28, "PT": 25, "RO": 24, "SE": 24,
    "SI": 19, "SK": 24,
}


def normalize(iban: str) -> str:
    """Strip the grouping a human types and upper-case it. Presentation is not identity."""
    if not isinstance(iban, str):
        raise TypeError(f"IBAN must be a string, got {type(iban).__name__}")
    return _CLEAN.sub("", iban).upper()


def country_of(iban: str) -> str:
    return normalize(iban)[:2]


def is_supported_country(iban: str) -> bool:
    return country_of(iban) in _LENGTHS


def checksum_ok(iban: str) -> bool:
    """The mod-97 check on its own."""
    s = normalize(iban)
    rearranged = s[4:] + s[:4]
    digits = "".join(str(ord(ch) - 55) if ch.isalpha() else ch for ch in rearranged)
    if not digits.isdigit():
        return False
    return int(digits) % 97 == 1


def validate_iban(iban: str) -> bool:
    """True when this IBAN is well-formed, the right length for its country, and checksums.

    Used at account-onboarding time, before a payout destination is stored.
    """
    try:
        s = normalize(iban)
    except TypeError:
        return False
    if len(s) < 5 or not _SHAPE.match(s):
        return False
    if not is_supported_country(s):
        return False
    expected = _LENGTHS[s[:2]]
    if len(s) != expected:
        return False
    return checksum_ok(s)


def format_iban(iban: str) -> str:
    """Group into fours, the way a bank statement prints it."""
    s = normalize(iban)
    return " ".join(s[i:i + 4] for i in range(0, len(s), 4))
