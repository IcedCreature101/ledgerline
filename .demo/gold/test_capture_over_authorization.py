"""LGR-105 — partial captures accumulate against the hold; the hold is the ceiling."""
import pytest

from ledgerline.core.money import Money
from ledgerline.payments.authorization import authorize
from ledgerline.payments.capture import OverCapture, capture


def _auth(major="100.00"):
    return authorize("m_1", Money.from_major(major, "USD"))


def test_two_partial_captures_cannot_exceed_the_hold():
    auth = _auth()
    capture(auth, Money.from_major("80.00", "USD"))
    with pytest.raises(OverCapture):
        capture(auth, Money.from_major("80.00", "USD"))
    assert auth.captured_total() == Money.from_major("80.00", "USD")


def test_a_capture_of_exactly_what_remains_is_allowed():
    auth = _auth()
    capture(auth, Money.from_major("80.00", "USD"))
    capture(auth, Money.from_major("20.00", "USD"))
    assert auth.remaining().is_zero()


def test_one_cent_beyond_the_remainder_is_refused():
    auth = _auth()
    capture(auth, Money.from_major("80.00", "USD"))
    with pytest.raises(OverCapture):
        capture(auth, Money.from_major("20.01", "USD"))


def test_many_small_captures_stop_at_the_hold():
    auth = _auth("1.00")
    for _ in range(100):
        capture(auth, Money(1, "USD"))
    with pytest.raises(OverCapture):
        capture(auth, Money(1, "USD"))
    assert auth.captured_total() == Money.from_major("1.00", "USD")


def test_a_fully_captured_authorization_is_no_longer_open():
    auth = _auth()
    capture(auth, Money.from_major("100.00", "USD"))
    assert not auth.is_open()
