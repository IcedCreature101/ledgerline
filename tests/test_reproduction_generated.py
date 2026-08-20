import pytest
from ledgerline.core.money import Money
from ledgerline.payments.refunds import OrderLine, refund


def test_refund_allocation_total_matches_requested_amount():
    # Refund $10.00 across three $5.00 order lines
    amount = Money.from_major("10.00", "USD")
    lines = [
        OrderLine(sku="SKU-A", amount=Money.from_major("5.00", "USD")),
        OrderLine(sku="SKU-B", amount=Money.from_major("5.00", "USD")),
        OrderLine(sku="SKU-C", amount=Money.from_major("5.00", "USD")),
    ]

    result = refund(amount, lines)

    # The allocated total must equal the requested refund amount
    assert result["allocated_total"] == amount, (
        f"Allocated total {result['allocated_total']} does not equal requested {amount}"
    )
