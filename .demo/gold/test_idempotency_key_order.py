"""LGR-104 — a retry is the same request whatever order its fields serialize in."""
from ledgerline.api.app import build_app, reset_state
from ledgerline.api.router import Request
from ledgerline.payments.idempotency import IdempotencyStore, fingerprint

BODY = {"merchant_id": "m_1", "amount_minor": 2500, "currency": "USD"}
REORDERED = {"amount_minor": 2500, "currency": "USD", "merchant_id": "m_1"}


def test_field_order_does_not_change_the_fingerprint():
    assert fingerprint(BODY) == fingerprint(REORDERED)


def test_a_genuinely_different_body_still_fingerprints_differently():
    assert fingerprint(BODY) != fingerprint({**BODY, "amount_minor": 9900})


def test_nested_field_order_does_not_change_the_fingerprint():
    a = {"metadata": {"b": 1, "a": 2}, "amount_minor": 1}
    b = {"amount_minor": 1, "metadata": {"a": 2, "b": 1}}
    assert fingerprint(a) == fingerprint(b)


def test_the_store_replays_a_reordered_retry():
    store = IdempotencyStore()
    store.remember("key-1", BODY, {"id": "pay_1"})
    assert store.lookup("key-1", REORDERED) == {"id": "pay_1"}


def test_the_api_returns_the_original_payment_on_a_reordered_retry():
    reset_state()
    app = build_app()
    first = app.dispatch(Request("POST", "/v1/payments", BODY, {"Idempotency-Key": "key-1"}))
    retry = app.dispatch(Request("POST", "/v1/payments", REORDERED, {"Idempotency-Key": "key-1"}))
    assert first.status == 201
    assert retry.status == 200, f"a legitimate retry was rejected: {retry.body}"
    assert retry.body["id"] == first.body["id"]
