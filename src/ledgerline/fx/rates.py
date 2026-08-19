"""Foreign-exchange rates and conversion.

Rates arrive from the treasury feed and are cached here. A conversion is only ever as good as the rate
behind it, so a rate we do not have is an error the caller has to handle — never a number we invent.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from ledgerline.core.currency import get_currency
from ledgerline.core.money import Money


class RateUnavailable(LookupError):
    """No rate for this pair on this date. The caller must decide what to do — hold the payment,
    use a different corridor, or fail the request. It is not something this module can paper over."""


@dataclass
class RateTable:
    """Mid-market rates, keyed by (base, quote). Rates are expressed in MAJOR units."""
    as_of: date
    rates: dict[tuple[str, str], Decimal] = field(default_factory=dict)

    def put(self, base: str, quote: str, rate: str | Decimal) -> None:
        self.rates[(base.upper(), quote.upper())] = Decimal(str(rate))

    def get(self, base: str, quote: str) -> Decimal:
        base, quote = base.upper(), quote.upper()
        if base == quote:
            return Decimal("1")
        try:
            return self.rates[(base, quote)]
        except KeyError:
            inverse = self.rates.get((quote, base))
            if inverse is not None and inverse != 0:
                return Decimal("1") / inverse
            raise RateUnavailable(f"no rate for {base}/{quote} on {self.as_of}")

    def has(self, base: str, quote: str) -> bool:
        base, quote = base.upper(), quote.upper()
        return base == quote or (base, quote) in self.rates or (quote, base) in self.rates


def convert(amount: Money, to_currency: str, table: RateTable) -> Money:
    """Convert `amount` into `to_currency` at the table's rate.

    Both sides are minor-unit integers with different exponents (USD has 2, JPY has 0), so the rate is
    applied in major units and re-scaled, rather than multiplied straight onto the minor amount.
    """
    src = get_currency(amount.currency)
    dst = get_currency(to_currency)
    if src.code == dst.code:
        return amount
    rate = table.get(src.code, dst.code)
    major = Decimal(amount.minor) / (10 ** src.exponent)
    converted = major * rate
    return Money.from_major(converted, dst.code)


def convert_all(amounts: list[Money], to_currency: str, table: RateTable) -> Money:
    """Convert and sum — the shape a multi-currency settlement report needs."""
    out = Money.zero(to_currency)
    for a in amounts:
        out = out + convert(a, to_currency, table)
    return out
