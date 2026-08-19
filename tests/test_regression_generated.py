import pytest
from datetime import datetime, timezone
from types import SimpleNamespace

from src.ledgerline.payments.capture import capture, capture_full, OverCapture, AuthorizationError


# Simple stub for Money that satisfies the interface used by capture()
class MoneyStub:
    def __init__(self, minor: int, currency: str = "USD"):
        self.minor = minor
        self.currency = currency

    def is_zero(self) -> bool:
        return self.minor == 0

    def is_negative(self) -> bool:
        return self.minor < 0

    def __repr__(self) -> str:
        # Represent in a readable way for error messages
        major = self.minor / 100
        return f"{major:.2f} {self.currency}"


# Simple stub for Authorization that satisfies the interface used by capture()
class AuthStub:
    def __init__(self, amount_minor: int, currency: str = "USD"):
        self.auth_id = "auth-123"
        self.amount = MoneyStub(amount_minor, currency)
        self.currency = currency
        self.captured = []  # list of MoneyStub
        self.voided = False
        self.created_at = datetime.now(timezone.utc)

    def is_expired(self, now: datetime) -> bool:
        # For testing we never expire
        return False

    def captured_total(self) -> SimpleNamespace:
        total_minor = sum(m.minor for m in self.captured)
        return SimpleNamespace(minor=total_minor)

    def remaining(self) -> MoneyStub:
        remaining_minor = self.amount.minor - sum(m.minor for m in self.captured)
        return MoneyStub(remaining_minor, self.currency)


def make_auth(total_minor: int, currency: str = "USD") -> AuthStub:
    return AuthStub(total_minor, currency)


def test_capture_allows_valid_partial_captures():
    auth = make_auth(10000)  # $100.00 in minor units (cents)
    # first partial capture of $30.00
    captured1 = capture(auth, MoneyStub(3000, "USD"))
    assert captured1.minor == 3000
    # second partial capture of $50.00
    captured2 = capture(auth, MoneyStub(5000, "USD"))
    assert captured2.minor == 5000
    # total captured should be $80.00
    assert sum(m.minor for m in auth.captured) == 8000
    # remaining should be $20.00
    assert auth.remaining().minor == 2000


def test_capture_raises_overcapture_when_exceeding_authorization():
    auth = make_auth(10000)  # $100.00
    # capture $60.00 first
    capture(auth, MoneyStub(6000, "USD"))
    # attempting to capture $50.00 would exceed the authorized $100.00
    with pytest.raises(OverCapture) as exc:
        capture(auth, MoneyStub(5000, "USD"))
    assert "cannot capture" in str(exc.value)


def test_capture_full_captures_exact_remaining_amount():
    auth = make_auth(10000)  # $100.00
    # capture $30.00 first
    capture(auth, MoneyStub(3000, "USD"))
    # capture_full should capture the remaining $70.00
    full_capture = capture_full(auth)
    assert full_capture.minor == 7000
    # after full capture, total captured equals authorized amount
    assert sum(m.minor for m in auth.captured) == 10000
    # remaining should now be zero
    assert auth.remaining().minor == 0


def test_capture_rejects_zero_or_negative_amounts():
    auth = make_auth(5000)  # $50.00
    with pytest.raises(AuthorizationError):
        capture(auth, MoneyStub(0, "USD"))
    with pytest.raises(AuthorizationError):
        capture(auth, MoneyStub(-100, "USD"))
