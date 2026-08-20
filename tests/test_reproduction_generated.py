import pytest

from ledgerline.payments.authorization import authorize
from ledgerline.payments.capture import capture, OverCapture
from ledgerline.core.money import Money


def test_over_capture_raises_when_cumulative_captures_exceed_authorization():
    # Create an authorization for 100.00 USD
    auth = authorize("merchant_1", Money.from_major("100.00", "USD"))

    # First partial capture of 80.00 USD should succeed
    capture(auth, Money.from_major("80.00", "USD"))

    # Second capture that would push total captured over the authorized amount
    # should raise OverCapture
    with pytest.raises(OverCapture):
        capture(auth, Money.from_major("80.00", "USD"))
