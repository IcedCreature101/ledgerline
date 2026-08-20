import pytest

from ledgerline.payments.authorization import authorize
from ledgerline.core.money import Money
from ledgerline.payments.capture import capture, OverCapture


def test_partial_captures_cannot_exceed_authorization_total():
    # Authorize a hold of $100.00
    auth = authorize("merchant_1", Money.from_major("100.00", "USD"))

    # First partial capture of $80.00 should succeed
    capture(auth, Money.from_major("80.00", "USD"))

    # Second capture of $80.00 would bring total captured to $160.00,
    # exceeding the authorized amount, and must raise OverCapture.
    with pytest.raises(OverCapture):
        capture(auth, Money.from_major("80.00", "USD"))
