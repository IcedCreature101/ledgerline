import pytest
from ledgerline.api.routes.accounts import add_payout_account


def test_add_payout_account_rejects_unsupported_country():
    # A validly‑formed Maltese IBAN (country not supported for payouts)
    maltese_iban = "MT84MALT011000012345MTLCAST001S"

    class DummyRequest:
        def __init__(self, body):
            self.body = body

    request = DummyRequest(
        {
            "iban": maltese_iban,
            "merchant_id": "merchant_123",
        }
    )

    status, payload = add_payout_account(request)

    assert status == 422, "Onboarding should reject unsupported country IBANs"
    assert (
        payload.get("error", {}).get("code") == "invalid_iban"
    ), "Error payload should contain code 'invalid_iban'"
