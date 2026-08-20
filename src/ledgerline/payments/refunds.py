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

    # Initial proportional allocation with rounding
    raw_shares: list[Money] = []
    for line in lines:
        proportion = Decimal(line.amount.minor) / Decimal(order_total)
        share = (Decimal(amount.minor) * proportion).quantize(Decimal(1), rounding=ROUND_HALF_UP)
        raw_shares.append(Money(int(share), amount.currency))

    # Adjust for any rounding discrepancy so that the sum matches the requested amount
    allocated_total = sum(s.minor for s in raw_shares)
    diff = amount.minor - allocated_total  # positive => need to add cents, negative => need to remove

    if diff != 0:
        # Distribute the missing/extra cents to the first |diff| lines
        sign = 1 if diff > 0 else -1
        adjusted_shares: list[Money] = []
        for i, share in enumerate(raw_shares):
            if i < abs(diff):
                adjusted_shares.append(Money(share.minor + sign, share.currency))
            else:
                adjusted_shares.append(share)
        return adjusted_shares

    return raw_shares


def refund(amount: Money, lines: list[OrderLine], *, already_refunded: Money | None = None) -> dict:
    """Build a refund: the per-line allocation plus the total actually returned."""
    paid = already_refunded or Money.zero(amount.currency)
    order_total = Money(sum(ln.amount.minor for ln in lines), amount.currency)
    if (paid + amount).minor > order_total.minor:
        raise RefundError(
            f"refunding {amount} would exceed the order total {order_total} "
            f"(already refunded {paid})")
    shares = allocate(amount, lines)
    return {
        "requested": amount,
        "allocated": shares,
        "allocated_total": Money(sum(s.minor for s in shares), amount.currency),
        "lines": [ln.sku for ln in lines],
    }
