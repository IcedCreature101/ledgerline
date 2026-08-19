import pytest
from datetime import date

from ledgerline.fx.rates import convert, RateUnavailable, RateTable
from ledgerline.core.money import Money


def test_convert_missing_rate_raises():
    # Set up a rate table that does NOT contain a USD→SEK rate
    table = RateTable(as_of=date(2024, 3, 1))
    # Add a different rate to ensure the table is populated
    table.put("USD", "EUR", "0.92")

    amount = Money.from_major("100.00", "USD")

    # Converting to SEK should raise RateUnavailable because the pair is missing
    with pytest.raises(RateUnavailable):
        convert(amount, "SEK", table)
