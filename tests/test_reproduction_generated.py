import pytest
from decimal import Decimal
from datetime import date

from ledgerline.fx.rates import RateTable, RateUnavailable, convert
from ledgerline.core.money import Money


def test_convert_without_published_rate_raises_instead_of_silently_passing_through():
    """A corridor with no published rate must fail loudly, not return the same
    numeric amount in a different currency (the SEK underpayment bug)."""
    table = RateTable(as_of=date(2024, 3, 1))
    # No USD/SEK rate has been published (this is the exact scenario from the ticket).
    amount = Money.from_major("100.00", "USD")

    with pytest.raises(RateUnavailable):
        convert(amount, "SEK", table)


def test_convert_still_works_for_a_published_corridor_and_its_inverse():
    """Corridors that DO have a published rate must keep working exactly as before,
    including the inverse of a quoted pair."""
    table = RateTable(as_of=date(2024, 3, 1))
    table.put("USD", "EUR", "0.92")

    amount = Money.from_major("100.00", "USD")
    converted = convert(amount, "EUR", table)
    assert converted == Money.from_major("92.00", "EUR")

    inverse_amount = Money.from_major("92.00", "EUR")
    inverse_converted = convert(inverse_amount, "USD", table)
    expected_inverse = Decimal("92.00") / Decimal("0.92")
    assert inverse_converted == Money.from_major(expected_inverse, "USD")
