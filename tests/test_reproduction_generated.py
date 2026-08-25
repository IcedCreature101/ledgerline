import pytest
from ledgerline.api.app import reset_state, build_app
from ledgerline.api.router import Request


def test_idempotent_payment_retry_with_different_field_order():
    # Ensure a clean environment
    reset_state()
    app = build_app()

    key = "key-1"
    # First request – normal field order
    body_first = {"merchant_id": "m_1", "amount_minor": 2500, "currency": "USD"}
    resp_first = app.dispatch(
        Request("POST", "/v1/payments", body_first, {"Idempotency-Key": key})
    )
    assert resp_first.status == 201, "first request should create the payment"

    # Second request – same data, different dict ordering
    body_second = {"amount_minor": 2500, "currency": "USD", "merchant_id": "m_1"}
    resp_second = app.dispatch(
        Request("POST", "/v1/payments", body_second, {"Idempotency-Key": key})
    )
    # The retry must be treated as idempotent and return the original response
    assert resp_second.status == 200, "retry with same idempotency key should succeed"
    assert resp_second.body == resp_first.body, "retry response must match the original response"
