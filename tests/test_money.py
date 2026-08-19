from decimal import Decimal

import pytest

from ledgerline.core.currency import UnknownCurrency, get_currency, is_supported
from ledgerline.core.money import CurrencyMismatch, Money, total


def test_from_major_scales_to_minor_units():
    assert Money.from_major("12.34", "USD").minor == 1234
    assert Money.from_major("12", "USD").minor == 1200


def test_jpy_has_no_minor_unit():
    assert Money.from_major("1200", "JPY").minor == 1200
    assert str(Money(1200, "JPY")) == "1200 JPY"


def test_bhd_has_three_decimal_places():
    assert Money.from_major("1.234", "BHD").minor == 1234


def test_addition_and_subtraction():
    a, b = Money(1000, "USD"), Money(250, "USD")
    assert (a + b).minor == 1250
    assert (a - b).minor == 750


def test_mixing_currencies_is_refused():
    with pytest.raises(CurrencyMismatch):
        Money(100, "USD") + Money(100, "EUR")


def test_comparison():
    assert Money(100, "USD") < Money(200, "USD")
    assert Money(200, "USD") >= Money(200, "USD")


def test_apply_rate_uses_bankers_rounding():
    # 2.5 and 3.5 minor units both settle on the even neighbour
    assert Money(5, "USD").apply_rate(Decimal("0.5")).minor == 2
    assert Money(7, "USD").apply_rate(Decimal("0.5")).minor == 4


def test_total_of_an_empty_list_still_has_a_currency():
    assert total([], "GBP") == Money(0, "GBP")


def test_format_uses_the_currency_symbol():
    assert Money.from_major("1234.50", "USD").format() == "$1,234.50"


def test_unknown_currency_is_refused_at_construction():
    with pytest.raises(UnknownCurrency):
        Money(100, "XYZ")
    assert not is_supported("XYZ")
    assert get_currency("usd").code == "USD"


def test_minor_must_be_an_integer():
    with pytest.raises(TypeError):
        Money(12.34, "USD")
