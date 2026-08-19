import pytest
from datetime import datetime, timezone

from ledgerline.core.money import Money
from ledgerline.payments.capture import capture, capture_full, OverCapture, void


class DummyAuth:
    def __init__(self, auth_id: str, amount: Money):
        self.auth_id = auth_id
        self.amount = amount
        self.currency = amount.currency
        self.captured = []
        self.voided = False
        self.created_at = datetime.now(timezone.utc)

    def captured_total(self) -> Money:
        total = Money(0, self.currency)
        for c in self.captured:
            total += c
        return total

    def remaining(self) -> Money:
        return self.amount - self.captured_total()

    def is_expired(self, now: datetime) -> bool:
        return False


def test_over_capture_raises():
    auth = DummyAuth("auth123", Money(100, "USD"))
    # Attempt to capture more than the authorized amount
    with pytest.raises(OverCapture) as exc:
        capture(auth, Money(160, "USD"))
    assert "cannot capture" in str(exc.value)
    # Ensure no capture was recorded
    assert auth.captured == []


def test_successful_partial_and_full_capture():
    auth = DummyAuth("auth456", Money(100, "USD"))
    # First partial capture
    captured1 = capture(auth, Money(40, "USD"))
    assert captured1 == Money(40, "USD")
    assert auth.captured == [Money(40, "USD")]
    assert auth.remaining() == Money(60, "USD")

    # Full capture of the remaining amount
    captured2 = capture_full(auth)
    assert captured2 == Money(60, "USD")
    assert auth.captured == [Money(40, "USD"), Money(60, "USD")]
    assert auth.remaining() == Money(0, "USD")

    # Further capture should now raise OverCapture
    with pytest.raises(OverCapture):
        capture(auth, Money(1, "USD"))
