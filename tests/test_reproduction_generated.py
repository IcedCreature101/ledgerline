import pytest

from ledgerline.payments.authorization import authorize
from ledgerline.payments.capture import capture, OverCapture
from ledgerline.core.money import Money


def test_capture_cumulative_over_authorization_raises():
    # Authorize a hold of $100.00 USD
    auth = authorize("merchant_1", Money.from_major("100.00", "USD"))

    # First partial capture of $80.00 – should succeed
    capture(auth, Money.from_major("80.00", "USD"))

    # Second capture that would push the total captured to $110.00,
    # exceeding the authorized $100.00 – should raise OverCapture
    with pytest.raises(OverCapture):
        capture(auth, Money.from_major("30.00", "USD"))
