import pytest

from ledgerline.payments.authorization import authorize
from ledgerline.core.money import Money
from ledgerline.payments.capture import capture, OverCapture


def test_partial_captures_cannot_exceed_authorization_total():
    # Authorize a hold of $100.00 USD
    auth = authorize("merchant_123", Money.from_major("100.00", "USD"))

    # First partial capture of $80.00 should succeed
    capture(auth, Money.from_major("80.00", "USD"))

    # Second capture that would bring the total to $160.00 must be rejected
    with pytest.raises(OverCapture):
        capture(auth, Money.from_major("80.00", "USD"))
