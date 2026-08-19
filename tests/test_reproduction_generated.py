import pytest
from ledgerline.api.app import build_app, reset_state
from ledgerline.api.router import Request


def test_idempotent_payment_retry_with_different_field_order():
    # Reset global state to ensure a clean environment
    reset_state()
    app = build_app()

    key = "key-123"
    # First request – canonical field order
    body_first = {"merchant_id": "m_1", "amount_minor": 2500, "currency": "USD"}
    # Second request – same logical content, different dict ordering
    body_second = {"amount_minor": 2500, "currency": "USD", "merchant_id": "m_1"}

    first_resp = app.dispatch(Request("POST", "/v1/payments", body_first, {"Idempotency-Key": key}))
    assert first_resp.status == 201  # payment created

    second_resp = app.dispatch(Request("POST", "/v1/payments", body_second, {"Idempotency-Key": key}))
    # The retry should be treated as idempotent and return the original response
    assert second_resp.status == 200
    assert second_resp.body == first_resp.body
