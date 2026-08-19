import pytest

from ledgerline.payments.idempotency import IdempotencyConflict, IdempotencyStore, fingerprint

BODY = {"merchant_id": "m_1", "amount_minor": 2500, "currency": "USD"}


def test_a_key_never_seen_before_has_no_stored_response():
    assert IdempotencyStore().lookup("key-1", BODY) is None


def test_the_stored_response_comes_back_on_a_replay():
    store = IdempotencyStore()
    store.remember("key-1", BODY, {"id": "pay_1"})
    assert store.lookup("key-1", BODY) == {"id": "pay_1"}


def test_reusing_a_key_for_a_different_payment_is_a_conflict():
    store = IdempotencyStore()
    store.remember("key-1", BODY, {"id": "pay_1"})
    with pytest.raises(IdempotencyConflict):
        store.lookup("key-1", {**BODY, "amount_minor": 9900})


def test_a_record_older_than_the_ttl_is_forgotten():
    store = IdempotencyStore(ttl_seconds=60)
    store.remember("key-1", BODY, {"id": "pay_1"}, now=1_000.0)
    assert store.lookup("key-1", BODY, now=1_030.0) == {"id": "pay_1"}
    assert store.lookup("key-1", BODY, now=1_100.0) is None
    assert len(store) == 0


def test_no_key_means_no_idempotency():
    store = IdempotencyStore()
    store.remember("", BODY, {"id": "pay_1"})
    assert len(store) == 0
    assert store.lookup("", BODY) is None


def test_the_fingerprint_of_the_same_body_is_stable():
    assert fingerprint(BODY) == fingerprint(dict(BODY))


def test_different_bodies_fingerprint_differently():
    assert fingerprint(BODY) != fingerprint({**BODY, "amount_minor": 1})
