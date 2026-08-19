import pytest
from ledgerline.api.routes.accounts import add_payout_account

def test_maltese_iban_is_rejected_on_onboarding():
    # Malta is not a supported payout corridor and should be rejected.
    maltese_iban = "MT84MALT011000012345MTLCAST001S"
    # Minimal request object with the required `body` attribute.
    request = type(
        "DummyRequest",
        (),
        {"body": {"iban": maltese_iban, "merchant_id": "merchant_123"}}
    )()
    status, payload = add_payout_account(request)

    assert status == 422, "Onboarding should reject unsupported country IBANs"
    assert payload["error"]["code"] == "invalid_iban"
    assert "that IBAN is not one we can pay out to" in payload["error"]["message"]
