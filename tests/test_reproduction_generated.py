import pytest
from types import SimpleNamespace

from ledgerline.api.routes.accounts import add_payout_account


def test_add_payout_account_rejects_unsupported_country():
    """
    Onboarding must reject payout accounts whose IBAN belongs to a country
    that is not supported for payouts (e.g., Malta). The current implementation
    validates only the checksum/format, so this test should fail until the
    validation logic is corrected.
    """
    request = SimpleNamespace(
        body={
            "merchant_id": "merchant_123",
            "iban": "MT84MALT011000012345MTLCAST001S",  # valid Maltese IBAN, but unsupported
        }
    )
    status, payload = add_payout_account(request)

    # Expected behavior: the request is rejected with a 422 error code.
    assert status == 422, "Unsupported country IBAN should be rejected with 422"
    assert isinstance(payload, dict)
    assert "error" in payload
    assert payload["error"]["code"] == "invalid_iban"
    assert "that IBAN is not one we can pay out to" in payload["error"]["message"]
