"""Refunds, including partial refunds split back across the original order lines.

When a customer is refunded part of an order, the refund has to be attributed to the individual lines —
tax is reclaimed per line, and the merchant's revenue report is per line. Splitting a single amount into
per-line shares is where money goes missing: shares are computed in fractions of a cent and every one of
them has to be rounded, but the SUM of the rounded shares must still equal the amount refunded. A cent
that appears or disappears here is a real cent that will not reconcile.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from ledgerline.core.money import Money


class RefundError(ValueError):
    """The refund cannot be made as asked."""


@dataclass(frozen=True)
class OrderLine:
    sku: str
    amount: Money
    description: str = ""


def allocate(amount: Money, lines: list[OrderLine]) -> list[Money]:
    """Split `amount` across `lines` in proportion to each line's share of the order.

    The returned list is parallel to `lines`, and its total is the amount that was passed in.
    """
    if not lines:
        raise RefundError("cannot allocate a refund with no order lines")
    order_total = sum(ln.amount.minor for ln in lines)
    if order_total <= 0:
        raise RefundError("order total must be positive to allocate against")
    if amount.is_negative():
        raise RefundError("cannot allocate a negative refund")

    # First pass: compute each line's raw share and its rounded cent value.
    raw_shares: list[Decimal] = []
    rounded_shares: list[int] = []
    for line in lines:
        proportion = Decimal(line.amount.minor) / Decimal(order_total)
        raw = Decimal(amount.minor) * proportion
        raw_shares.append(raw)
        rounded = int(raw.quantize(Decimal(1), rounding=ROUND_HALF_UP))
        rounded_shares.append(rounded)

    # Compute the difference between the requested amount and the sum of rounded shares.
    total_rounded = sum(rounded_shares)
    diff = amount.minor - total_rounded  # positive => need to add cents, negative => need to remove

    if diff != 0:
        # Remainders indicate how far each raw share was from its rounded value.
        # remainder = raw - rounded (can be positive or negative)
        remainders = [(i, raw_shares[i] - Decimal(rounded_shares[i])) for i in range(len(lines))]

        if diff > 0:
            # Need to add cents to the lines with the largest positive remainders
            remainders.sort(key=lambda x: x[1], reverse=True)
            for i in range(diff):
                idx = remainders[i][0]
                rounded_shares[idx] += 1
        else:
            # Need to subtract cents from the lines with the most negative remainders
            remainders.sort(key=lambda x: x[1])  # ascending: most negative first
            for i in range(-diff):
                idx = remainders[i][0]
                rounded_shares[idx] -= 1

    # Convert the final cent amounts back to Money objects.
    return [Money(share, amount.currency) for share in rounded_shares]


def refund(amount: Money, lines: list[OrderLine], *, already_refunded: Money | None = None) -> dict:
    """Build a refund: the per-line allocation plus the total actually returned."""
    paid = already_refunded or Money.zero(amount.currency)
    order_total = Money(sum(ln.amount.minor for ln in lines), amount.currency)
    if (paid + amount).minor > order_total.minor:
        raise RefundError(
            f"refunding {amount} would exceed the order total {order_total} "
            f"(already refunded {paid})"
        )
    shares = allocate(amount, lines)
    return {
        "requested": amount,
        "allocated": shares,
        "allocated_total": Money(sum(s.minor for s in shares), amount.currency),
        "lines": [ln.sku for ln in lines],
    }
