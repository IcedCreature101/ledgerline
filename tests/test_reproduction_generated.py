import pytest
from ledgerline.core.money import Money
from ledgerline.payments.refunds import OrderLine, allocate, refund


def _sample_lines() -> list[OrderLine]:
    # Three order lines each worth $5.00
    return [
        OrderLine("SKU-A", Money.from_major("5.00", "USD")),
        OrderLine("SKU-B", Money.from_major("5.00", "USD")),
        OrderLine("SKU-C", Money.from_major("5.00", "USD")),
    ]


def test_allocate_returns_shares_that_sum_to_requested_amount():
    lines = _sample_lines()
    requested = Money.from_major("10.00", "USD")
    shares = allocate(requested, lines)

    # The sum of the per‑line shares must equal the requested refund amount.
    allocated_total = Money(sum(s.minor for s in shares), requested.currency)
    assert allocated_total == requested, (
        f"Allocated total {allocated_total} does not match requested {requested}"
    )


def test_refund_result_contains_correct_allocated_total():
    lines = _sample_lines()
    requested = Money.from_major("10.00", "USD")
    result = refund(requested, lines)

    # The refund dict should report an allocated_total that matches the requested amount.
    assert result["allocated_total"] == requested, (
        f"Refund allocated_total {result['allocated_total']} does not match requested {requested}"
    )
