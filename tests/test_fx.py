from datetime import date
from decimal import Decimal

import pytest

from ledgerline.core.money import Money
from ledgerline.fx.rates import RateTable, convert, convert_all


def _table():
    t = RateTable(as_of=date(2024, 3, 1))
    t.put("USD", "EUR", "0.92")
    t.put("USD", "GBP", "0.79")
    t.put("EUR", "JPY", "163.00")
    return t


def test_converting_to_the_same_currency_is_the_identity():
    amount = Money.from_major("100.00", "USD")
    assert convert(amount, "USD", _table()) == amount


def test_a_quoted_pair_converts_at_its_rate():
    assert convert(Money.from_major("100.00", "USD"), "EUR", _table()) == Money.from_major("92.00", "EUR")


def test_the_inverse_of_a_quoted_pair_is_derived():
    got = convert(Money.from_major("92.00", "EUR"), "USD", _table())
    assert got == Money.from_major("100.00", "USD")


def test_converting_into_a_currency_with_no_minor_unit():
    assert convert(Money.from_major("10.00", "EUR"), "JPY", _table()) == Money(1630, "JPY")


def test_has_reports_what_the_table_can_price():
    t = _table()
    assert t.has("USD", "EUR") and t.has("EUR", "USD") and t.has("USD", "USD")
    assert not t.has("USD", "SEK")


def test_rates_are_case_insensitive():
    assert _table().get("usd", "eur") == Decimal("0.92")


def test_convert_all_sums_into_one_currency():
    amounts = [Money.from_major("100.00", "USD"), Money.from_major("100.00", "USD")]
    assert convert_all(amounts, "EUR", _table()) == Money.from_major("184.00", "EUR")


def test_an_unknown_currency_code_is_refused():
    from ledgerline.core.currency import UnknownCurrency
    with pytest.raises(UnknownCurrency):
        convert(Money.from_major("1.00", "USD"), "ZZZ", _table())
