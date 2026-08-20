import pytest
from ledgerline.core.money import Money
from ledgerline.payments.refunds import OrderLine, refund


def test_refund_allocation_total_matches_requested_amount():
    # Three order lines each worth $5.00
    lines = [
        OrderLine("SKU-A", Money.from_major("5.00", "USD")),
        OrderLine("SKU-B", Money.from_major("5.00", "USD")),
        OrderLine("SKU-C", Money.from_major("5.00", "USD")),
    ]
    # Refund request of $10.00
    amount = Money.from_major("10.00", "USD")

    result = refund(amount, lines)

    allocated_total = result["allocated_total"]
    # The allocated total must equal the requested refund amount
    assert allocated_total == amount, (
        f"Allocated total {allocated_total} does not equal requested amount {amount}"
    )
