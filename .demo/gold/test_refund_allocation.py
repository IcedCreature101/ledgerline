"""LGR-102 — a split refund returns exactly what was asked for, to the cent."""
from ledgerline.core.money import Money
from ledgerline.payments.refunds import OrderLine, allocate


def _lines(*majors):
    return [OrderLine(f"SKU-{i}", Money.from_major(m, "USD")) for i, m in enumerate(majors)]


def _total(shares):
    return sum(s.minor for s in shares)


def test_ten_dollars_across_three_equal_lines_returns_ten_dollars():
    shares = allocate(Money.from_major("10.00", "USD"), _lines("5.00", "5.00", "5.00"))
    assert _total(shares) == 1000


def test_the_remainder_lands_somewhere_rather_than_vanishing():
    shares = allocate(Money.from_major("10.00", "USD"), _lines("5.00", "5.00", "5.00"))
    assert sorted(s.minor for s in shares) == [333, 333, 334]


def test_a_one_cent_refund_across_three_lines_is_still_one_cent():
    assert _total(allocate(Money(1, "USD"), _lines("5.00", "5.00", "5.00"))) == 1


def test_allocation_totals_the_refund_for_many_shapes():
    shapes = [("1.00", "2.00", "3.00"), ("0.01", "0.01", "0.01"), ("7.77", "1.11", "3.33"),
              ("100.00", "0.01"), ("33.33", "33.33", "33.34")]
    for amounts in ("10.00", "0.07", "1.00", "99.99"):
        for shape in shapes:
            shares = allocate(Money.from_major(amounts, "USD"), _lines(*shape))
            assert _total(shares) == Money.from_major(amounts, "USD").minor, (amounts, shape)


def test_no_share_is_negative():
    shares = allocate(Money.from_major("0.05", "USD"), _lines("5.00", "5.00", "5.00"))
    assert all(s.minor >= 0 for s in shares)
