from decimal import Decimal

import pytest

from ledgerline.core.money import Money
from ledgerline.fees.schedule import (ENTERPRISE, STANDARD, calculate_fee, effective_rate,
                                      get_schedule)


def test_small_payment_pays_the_headline_rate_plus_the_fixed_fee():
    # 20.00 @ 2.9% = 0.58, plus the 0.30 fixed component
    assert calculate_fee(Money.from_major("20.00", "USD"), STANDARD) == Money.from_major("0.88", "USD")


def test_a_payment_at_the_top_of_the_first_tier():
    # 1,000.00 @ 2.9% = 29.00, plus 0.30
    assert calculate_fee(Money.from_major("1000.00", "USD"), STANDARD) == Money.from_major("29.30", "USD")


def test_zero_costs_nothing():
    assert calculate_fee(Money.zero("USD"), STANDARD).is_zero()


def test_a_negative_amount_is_refused():
    with pytest.raises(ValueError):
        calculate_fee(Money(-100, "USD"), STANDARD)


def test_enterprise_schedule_has_no_fixed_component():
    assert calculate_fee(Money.from_major("100.00", "USD"), ENTERPRISE) == Money.from_major("1.90", "USD")


def test_schedules_are_addressable_by_name():
    assert get_schedule("standard") is STANDARD
    with pytest.raises(ValueError):
        get_schedule("platinum")


def test_effective_rate_includes_the_fixed_component():
    rate = effective_rate(Money.from_major("20.00", "USD"), STANDARD)
    assert rate == Decimal("0.04400")


def test_fees_are_charged_in_the_payment_currency():
    assert calculate_fee(Money.from_major("100.00", "EUR"), STANDARD).currency == "EUR"
