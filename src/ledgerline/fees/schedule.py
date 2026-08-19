"""Processing fees.

A merchant is priced on a TIERED schedule: the first slice of a payment is charged at the headline rate
and each further slice at a progressively lower one. Tiers are marginal — the same way income tax works —
so a payment does not get cheaper per-unit the instant it crosses a boundary in a way that makes the
merchant's effective rate jump discontinuously.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from ledgerline.core.money import Money


@dataclass(frozen=True)
class Tier:
    """A slice of a payment priced at `rate`. `upto_minor` is the top of the slice, None for the last."""
    upto_minor: int | None
    rate: Decimal


@dataclass(frozen=True)
class FeeSchedule:
    name: str
    tiers: tuple[Tier, ...]
    fixed_minor: int = 0          # a flat per-transaction component, charged once

    def rate_for(self, amount: Money) -> Decimal:
        """The rate of the tier the amount falls in. Reporting only — pricing uses every tier."""
        for tier in self.tiers:
            if tier.upto_minor is None or amount.minor <= tier.upto_minor:
                return tier.rate
        return self.tiers[-1].rate


STANDARD = FeeSchedule(
    name="standard",
    tiers=(
        Tier(upto_minor=100_000, rate=Decimal("0.029")),      # up to 1,000.00 → 2.9%
        Tier(upto_minor=1_000_000, rate=Decimal("0.024")),    # up to 10,000.00 → 2.4%
        Tier(upto_minor=None, rate=Decimal("0.018")),         # above that → 1.8%
    ),
    fixed_minor=30,
)

ENTERPRISE = FeeSchedule(
    name="enterprise",
    tiers=(
        Tier(upto_minor=1_000_000, rate=Decimal("0.019")),
        Tier(upto_minor=None, rate=Decimal("0.011")),
    ),
    fixed_minor=0,
)

_SCHEDULES = {s.name: s for s in (STANDARD, ENTERPRISE)}


def get_schedule(name: str) -> FeeSchedule:
    try:
        return _SCHEDULES[name]
    except KeyError:
        raise ValueError(f"unknown fee schedule {name!r}") from None


def calculate_fee(amount: Money, schedule: FeeSchedule | str = STANDARD) -> Money:
    """The processing fee for a single payment, including the fixed component.

    The variable part is charged across the schedule's tiers; the fixed part is charged once.
    """
    sched = get_schedule(schedule) if isinstance(schedule, str) else schedule
    if amount.is_negative():
        raise ValueError("cannot charge a fee on a negative amount")
    if amount.is_zero():
        return Money.zero(amount.currency)

    # Compute the variable fee by iterating over the tiers and applying each rate to the
    # portion of the amount that falls within that tier.
    remaining_minor = amount.minor
    previous_upto = 0
    variable_fee = Money.zero(amount.currency)

    for tier in sched.tiers:
        # Determine the slice size for this tier.
        if tier.upto_minor is None:
            slice_minor = remaining_minor
        else:
            slice_limit = tier.upto_minor - previous_upto
            slice_minor = min(remaining_minor, slice_limit)

        if slice_minor > 0:
            slice_money = Money(slice_minor, amount.currency)
            variable_fee = variable_fee + slice_money.apply_rate(tier.rate)
            remaining_minor -= slice_minor
            previous_upto = tier.upto_minor if tier.upto_minor is not None else previous_upto

        if remaining_minor <= 0:
            break

    # Add the fixed component.
    total_minor = variable_fee.minor + sched.fixed_minor
    return Money(total_minor, amount.currency)


def effective_rate(amount: Money, schedule: FeeSchedule | str = STANDARD) -> Decimal:
    """The blended rate actually paid, for the merchant's statement."""
    if amount.is_zero():
        return Decimal("0")
    fee = calculate_fee(amount, schedule)
    return (Decimal(fee.minor) / Decimal(amount.minor)).quantize(Decimal("0.00001"))
