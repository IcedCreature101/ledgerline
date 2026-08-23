import pytest
from ledgerline.api.app import build_app, reset_state
from ledgerline.api.router import Request


def test_idempotent_retry_returns_cached_response():
    # Ensure a clean state before the test
    reset_state()
    app = build_app()

    # First request with a given Idempotency-Key
    first_body = {
        "merchant_id": "m_1",
        "amount_minor": 2500,
        "currency": "USD",
    }
    first_resp = app.dispatch(
        Request(
            "POST",
            "/v1/payments",
            first_body,
            {"Idempotency-Key": "key-1"},
        )
    )
    assert first_resp.status == 201
    # Capture the successful response payload
    cached_response = first_resp.body

    # Retry the same payment with the same Idempotency-Key but a different dict order
    retry_body = {
        "amount_minor": 2500,
        "currency": "USD",
        "merchant_id": "m_1",
    }
    retry_resp = app.dispatch(
        Request(
            "POST",
            "/v1/payments",
            retry_body,
            {"Idempotency-Key": "key-1"},
        )
    )
    # The retry should return the cached result, not a conflict
    assert retry_resp.status == 200
    assert retry_resp.body == cached_response
