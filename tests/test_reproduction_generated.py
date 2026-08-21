import pytest

from ledgerline.api.app import build_app, reset_state
from ledgerline.api.router import Request


def test_retry_with_reordered_fields_is_treated_as_same_payment():
    reset_state()
    app = build_app()

    first = app.dispatch(Request(
        "POST", "/v1/payments",
        {"merchant_id": "m_1", "amount_minor": 2500, "currency": "USD"},
        {"Idempotency-Key": "key-1"},
    ))
    assert first.status == 201

    retry = app.dispatch(Request(
        "POST", "/v1/payments",
        {"amount_minor": 2500, "currency": "USD", "merchant_id": "m_1"},
        {"Idempotency-Key": "key-1"},
    ))

    assert retry.status == 200
    assert retry.body == first.body
