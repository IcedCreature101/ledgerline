import pytest

from ledgerline.core.money import Money
from ledgerline.payments.refunds import OrderLine, RefundError, allocate, refund


def _lines(*majors):
    return [OrderLine(f"SKU-{i}", Money.from_major(m, "USD")) for i, m in enumerate(majors)]


def test_a_full_refund_returns_each_line_in_full():
    lines = _lines("10.00", "20.00", "30.00")
    shares = allocate(Money.from_major("60.00", "USD"), lines)
    assert [s.minor for s in shares] == [1000, 2000, 3000]


def test_a_half_refund_splits_cleanly_when_the_halves_are_whole_cents():
    lines = _lines("10.00", "30.00")
    shares = allocate(Money.from_major("20.00", "USD"), lines)
    assert [s.minor for s in shares] == [500, 1500]


def test_allocation_is_parallel_to_the_lines_it_was_given():
    lines = _lines("5.00", "15.00")
    assert len(allocate(Money.from_major("4.00", "USD"), lines)) == len(lines)


def test_refunding_more_than_the_order_is_refused():
    lines = _lines("10.00")
    with pytest.raises(RefundError):
        refund(Money.from_major("15.00", "USD"), lines)


def test_a_second_refund_cannot_exceed_what_is_left():
    lines = _lines("10.00")
    with pytest.raises(RefundError):
        refund(Money.from_major("6.00", "USD"), lines,
               already_refunded=Money.from_major("5.00", "USD"))


def test_no_lines_is_refused():
    with pytest.raises(RefundError):
        allocate(Money.from_major("1.00", "USD"), [])


def test_refund_reports_the_skus_it_allocated_across():
    lines = _lines("10.00", "10.00")
    assert refund(Money.from_major("10.00", "USD"), lines)["lines"] == ["SKU-0", "SKU-1"]
