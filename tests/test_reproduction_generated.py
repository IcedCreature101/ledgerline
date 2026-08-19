import pytest
from ledgerline.api.app import build_app, reset_state
from ledgerline.api.router import Request


def test_idempotent_payment_retry_with_different_field_order():
    # Ensure a clean state before the test
    reset_state()
    app = build_app()

    # First request with a specific field order
    body_first = {
        "merchant_id": "m_1",
        "amount_minor": 2500,
        "currency": "USD",
    }
    first_resp = app.dispatch(
        Request(
            method="POST",
            path="/v1/payments",
            body=body_first,
            headers={"Idempotency-Key": "key-1"},
        )
    )
    assert first_resp.status == 201
    first_body = first_resp.body

    # Second request with the same logical content but a different dict order
    body_retry = {
        "amount_minor": 2500,
        "currency": "USD",
        "merchant_id": "m_1",
    }
    second_resp = app.dispatch(
        Request(
            method="POST",
            path="/v1/payments",
            body=body_retry,
            headers={"Idempotency-Key": "key-1"},
        )
    )
    # The retry should be treated as idempotent and return the original response
    assert second_resp.status == 200
    assert second_resp.body == first_body
