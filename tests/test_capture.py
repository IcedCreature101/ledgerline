from datetime import datetime, timedelta, timezone

import pytest

from ledgerline.core.money import CurrencyMismatch, Money
from ledgerline.payments.authorization import AuthorizationError, authorize
from ledgerline.payments.capture import OverCapture, capture, capture_full, void


def _auth(major="100.00"):
    return authorize("m_1", Money.from_major(major, "USD"))


def test_a_full_capture_leaves_nothing_held():
    auth = _auth()
    capture(auth, Money.from_major("100.00", "USD"))
    assert auth.remaining().is_zero()
    assert auth.captured_total() == Money.from_major("100.00", "USD")


def test_capture_full_captures_what_remains():
    auth = _auth()
    assert capture_full(auth) == Money.from_major("100.00", "USD")


def test_a_single_capture_beyond_the_hold_is_refused():
    auth = _auth()
    with pytest.raises(OverCapture):
        capture(auth, Money.from_major("100.01", "USD"))


def test_a_partial_capture_leaves_the_rest_held():
    auth = _auth()
    capture(auth, Money.from_major("30.00", "USD"))
    assert auth.remaining() == Money.from_major("70.00", "USD")
    assert auth.is_open()


def test_capturing_a_different_currency_is_refused():
    auth = _auth()
    with pytest.raises(CurrencyMismatch):
        capture(auth, Money.from_major("10.00", "EUR"))


def test_zero_and_negative_captures_are_refused():
    auth = _auth()
    for bad in (Money.zero("USD"), Money(-100, "USD")):
        with pytest.raises(AuthorizationError):
            capture(auth, bad)


def test_an_expired_authorization_cannot_be_captured():
    auth = _auth()
    later = datetime.now(timezone.utc) + timedelta(days=8)
    with pytest.raises(AuthorizationError):
        capture(auth, Money.from_major("10.00", "USD"), now=later)


def test_a_voided_authorization_cannot_be_captured():
    auth = _auth()
    void(auth)
    with pytest.raises(AuthorizationError):
        capture(auth, Money.from_major("10.00", "USD"))


def test_an_authorization_with_captures_cannot_be_voided():
    auth = _auth()
    capture(auth, Money.from_major("10.00", "USD"))
    with pytest.raises(AuthorizationError):
        void(auth)


def test_authorizing_nothing_is_refused():
    with pytest.raises(AuthorizationError):
        authorize("m_1", Money.zero("USD"))
