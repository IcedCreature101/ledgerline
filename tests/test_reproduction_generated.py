import pytest
from datetime import date

from ledgerline.fx.rates import convert, RateUnavailable, RateTable
from ledgerline.core.money import Money


def test_convert_missing_rate_raises():
    # Set up a rate table that has rates for USD→EUR and USD→GBP only.
    table = RateTable(as_of=date(2024, 3, 1))
    table.put("USD", "EUR", "0.92")
    table.put("USD", "GBP", "0.79")

    amount = Money.from_major("100.00", "USD")

    # Converting to a currency with no published rate (SEK) must raise.
    with pytest.raises(RateUnavailable):
        convert(amount, "SEK", table)
