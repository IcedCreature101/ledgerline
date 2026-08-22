"""
Ticket: A conversion for a currency pair with no published rate must fail
loudly (RateUnavailable) rather than silently returning the amount unchanged
in the target currency.
"""
from datetime import date

import pytest

from ledgerline.core.money import Money
from ledgerline.fx.rates import RateTable, RateUnavailable, convert


def test_convert_without_published_rate_raises_instead_of_1_to_1():
    table = RateTable(as_of=date(2024, 3, 1))
    # USD/SEK was never published on this table -- the corridor that bit us.
    amount = Money.from_major("100.00", "USD")

    with pytest.raises(RateUnavailable):
        convert(amount, "SEK", table)
