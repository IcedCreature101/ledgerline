"""LGR-107 — a conversion with no rate is an error, never a number we invented."""
from datetime import date
from decimal import Decimal

import pytest

from ledgerline.core.money import Money
from ledgerline.fx.rates import RateTable, RateUnavailable, convert, convert_all


def _table():
    t = RateTable(as_of=date(2024, 3, 1))
    t.put("USD", "EUR", "0.92")
    return t


def test_an_unquoted_pair_raises_rather_than_returning_parity():
    with pytest.raises(RateUnavailable):
        _table().get("USD", "SEK")


def test_converting_without_a_rate_raises():
    with pytest.raises(RateUnavailable):
        convert(Money.from_major("100.00", "USD"), "SEK", _table())


def test_the_error_names_the_pair_it_could_not_price():
    with pytest.raises(RateUnavailable) as excinfo:
        convert(Money.from_major("100.00", "USD"), "SEK", _table())
    message = str(excinfo.value)
    assert "USD" in message and "SEK" in message


def test_a_batch_conversion_fails_rather_than_reporting_a_wrong_total():
    amounts = [Money.from_major("100.00", "USD"), Money.from_major("100.00", "USD")]
    with pytest.raises(RateUnavailable):
        convert_all(amounts, "SEK", _table())


def test_quoted_pairs_and_their_inverses_still_work():
    t = _table()
    assert t.get("USD", "EUR") == Decimal("0.92")
    assert convert(Money.from_major("100.00", "USD"), "EUR", t) == Money.from_major("92.00", "EUR")
    assert convert(Money.from_major("92.00", "EUR"), "USD", t) == Money.from_major("100.00", "USD")


def test_the_same_currency_needs_no_rate():
    assert _table().get("SEK", "SEK") == Decimal("1")
