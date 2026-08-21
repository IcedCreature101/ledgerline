import pytest

from ledgerline.api.router import Request
from ledgerline.api.routes import payments as payments_routes


def test_retry_with_reordered_json_fields_returns_original_payment():
    # Fresh state for this route module (mirrors what the app does between demo runs / tests).
    payments_routes._reset_state()

    first_status, first_body = payments_routes.create_payment(
        Request(
            "POST",
            "/v1/payments",
            {"merchant_id": "m_1", "amount_minor": 2500, "currency": "USD"},
            {"Idempotency-Key": "key-1"},
        )
    )
    assert first_status == 201

    # Same merchant, same amount, same currency, same idempotency key — just the JSON
    # fields re-serialised in a different order, exactly as Harbour Point's client does.
    retry_status, retry_body = payments_routes.create_payment(
        Request(
            "POST",
            "/v1/payments",
            {"amount_minor": 2500, "currency": "USD", "merchant_id": "m_1"},
            {"Idempotency-Key": "key-1"},
        )
    )

    # A retry of the same logical payment must return the original response, not a conflict.
    assert retry_status == 200
    assert retry_body == first_body
