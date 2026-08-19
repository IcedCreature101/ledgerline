"""LGR-101 — tiered processing fees are marginal, not a single rate on the whole amount."""
from decimal import Decimal

from ledgerline.core.money import Money
from ledgerline.fees.schedule import STANDARD, calculate_fee, effective_rate


def test_a_payment_spanning_all_three_tiers():
    # 1,000.00 @ 2.9% = 29.00
    # 9,000.00 @ 2.4% = 216.00
    # 40,000.00 @ 1.8% = 720.00   → 965.00 variable, plus the 0.30 fixed component
    assert calculate_fee(Money.from_major("50000.00", "USD"), STANDARD) == \
        Money.from_major("965.30", "USD")


def test_a_payment_spanning_two_tiers():
    # 1,000.00 @ 2.9% = 29.00 + 4,000.00 @ 2.4% = 96.00 → 125.00, plus 0.30
    assert calculate_fee(Money.from_major("5000.00", "USD"), STANDARD) == \
        Money.from_major("125.30", "USD")


def test_the_first_tier_is_unchanged():
    assert calculate_fee(Money.from_major("1000.00", "USD"), STANDARD) == \
        Money.from_major("29.30", "USD")


def test_crossing_a_boundary_never_makes_the_fee_go_down():
    previous = None
    for major in ("999.00", "1000.00", "1000.01", "1500.00", "9999.99", "10000.00", "10000.01"):
        fee = calculate_fee(Money.from_major(major, "USD"), STANDARD)
        if previous is not None:
            assert fee.minor >= previous, f"fee fell at {major}"
        previous = fee.minor


def test_the_effective_rate_falls_smoothly_rather_than_stepping():
    small = effective_rate(Money.from_major("5000.00", "USD"), STANDARD)
    large = effective_rate(Money.from_major("50000.00", "USD"), STANDARD)
    assert Decimal("0.018") < large < small
