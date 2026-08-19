"""Money — an exact minor-unit amount with a currency.

Money is stored in MINOR UNITS (cents, pence, yen) as an int. Floats never appear: a payments ledger
that represents 0.10 + 0.20 as 0.30000000000000004 will, given enough volume, fail to balance, and a
ledger that does not balance is not a ledger.

Decimal is used only at the boundaries where a rate or a percentage has to be applied; the result is
always quantised back to minor units through an explicit rounding rule, because "how do we round" is a
business decision and not something to leave to the default.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, ROUND_HALF_UP, Decimal

from ledgerline.core.currency import Currency, get_currency


class CurrencyMismatch(ValueError):
    """Two amounts in different currencies were combined. Always a bug in the caller."""


@dataclass(frozen=True)
class Money:
    minor: int
    currency: str

    def __post_init__(self) -> None:
        if not isinstance(self.minor, int) or isinstance(self.minor, bool):
            raise TypeError(f"Money.minor must be an int in minor units, got {type(self.minor).__name__}")
        get_currency(self.currency)          # raises for an unknown code, at construction

    # ── construction ────────────────────────────────────────────────────────────────────────────
    @classmethod
    def from_major(cls, amount: str | Decimal | int, currency: str) -> "Money":
        """Build from a major-unit amount ("12.34"). Strings, not floats — a float has already lost
        precision by the time it reaches us."""
        cur = get_currency(currency)
        d = Decimal(str(amount))
        scaled = (d * (10 ** cur.exponent)).quantize(Decimal(1), rounding=ROUND_HALF_UP)
        return cls(int(scaled), cur.code)

    @classmethod
    def zero(cls, currency: str) -> "Money":
        return cls(0, get_currency(currency).code)

    # ── arithmetic ──────────────────────────────────────────────────────────────────────────────
    def _same(self, other: "Money") -> None:
        if self.currency != other.currency:
            raise CurrencyMismatch(f"cannot combine {self.currency} and {other.currency}")

    def __add__(self, other: "Money") -> "Money":
        self._same(other)
        return Money(self.minor + other.minor, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        self._same(other)
        return Money(self.minor - other.minor, self.currency)

    def __neg__(self) -> "Money":
        return Money(-self.minor, self.currency)

    def __lt__(self, other: "Money") -> bool:
        self._same(other)
        return self.minor < other.minor

    def __le__(self, other: "Money") -> bool:
        self._same(other)
        return self.minor <= other.minor

    def __gt__(self, other: "Money") -> bool:
        self._same(other)
        return self.minor > other.minor

    def __ge__(self, other: "Money") -> bool:
        self._same(other)
        return self.minor >= other.minor

    def is_zero(self) -> bool:
        return self.minor == 0

    def is_negative(self) -> bool:
        return self.minor < 0

    # ── scaling ─────────────────────────────────────────────────────────────────────────────────
    def apply_rate(self, rate: Decimal | str, *, rounding: str = ROUND_HALF_EVEN) -> "Money":
        """Multiply by a rate and quantise back to whole minor units.

        Banker's rounding by default: over a large number of fee calculations, ROUND_HALF_UP is biased
        upward and the merchant is systematically overcharged by a fraction of a cent per transaction.
        """
        product = Decimal(self.minor) * Decimal(str(rate))
        return Money(int(product.quantize(Decimal(1), rounding=rounding)), self.currency)

    # ── presentation ────────────────────────────────────────────────────────────────────────────
    def to_major(self) -> Decimal:
        cur = get_currency(self.currency)
        return (Decimal(self.minor) / (10 ** cur.exponent)).quantize(
            Decimal(1).scaleb(-cur.exponent))

    def format(self) -> str:
        cur = get_currency(self.currency)
        return f"{cur.symbol}{self.to_major():,.{cur.exponent}f}"

    def __str__(self) -> str:
        return f"{self.to_major()} {self.currency}"


def total(amounts: list[Money], currency: str) -> Money:
    """Sum a list, with the currency stated explicitly so an empty list still has one."""
    acc = Money.zero(currency)
    for a in amounts:
        acc = acc + a
    return acc
