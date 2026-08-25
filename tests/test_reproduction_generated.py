import pytest
from ledgerline.payments.idempotency import IdempotencyStore, IdempotencyConflict


def test_idempotency_lookup_allows_same_content_different_field_order():
    store = IdempotencyStore()
    key = "test-key"
    # Original request body
    body_original = {
        "merchant_id": "m_1",
        "amount_minor": 2500,
        "currency": "USD",
    }
    stored_response = {"id": "pay_000001"}

    # Remember the first request
    store.remember(key, body_original, stored_response)

    # Same logical request but fields in a different order
    body_shuffled = {
        "currency": "USD",
        "amount_minor": 2500,
        "merchant_id": "m_1",
    }

    # The lookup should return the previously stored response, not raise IdempotencyConflict
    result = store.lookup(key, body_shuffled)
    assert result == stored_response, "Idempotent lookup should succeed for identical content regardless of field order"
