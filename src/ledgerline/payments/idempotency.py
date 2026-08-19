"""Idempotency for payment creation.

A client that does not get a response cannot know whether the payment was made, so it retries. Without
idempotency that retry is a second charge on a real card. The client sends an `Idempotency-Key` with the
request and we promise: the same key with the same request returns the ORIGINAL result, and never
executes twice.

The request body is fingerprinted alongside the key so that reusing a key for a genuinely different
payment is caught as a conflict rather than silently returning someone else's receipt.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any


class IdempotencyConflict(ValueError):
    """The same key was reused with a different request body."""


def fingerprint(body: dict[str, Any]) -> str:
    """A stable fingerprint of the request body."""
    # Ensure the fingerprint is independent of the order of keys in the JSON object.
    # `sort_keys=True` produces a deterministic string representation.
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode("utf-8")).hexdigest()


@dataclass
class _Record:
    fingerprint: str
    response: dict
    created_at: float


@dataclass
class IdempotencyStore:
    ttl_seconds: int = 24 * 60 * 60
    _records: dict = field(default_factory=dict)

    def _expired(self, rec: _Record, now: float) -> bool:
        return (now - rec.created_at) > self.ttl_seconds

    def lookup(self, key: str, body: dict, *, now: float | None = None) -> dict | None:
        """The stored response for this key, or None if this is the first time we have seen it."""
        if not key:
            return None
        now = time.time() if now is None else now
        rec = self._records.get(key)
        if rec is None:
            return None
        if self._expired(rec, now):
            del self._records[key]
            return None
        if rec.fingerprint != fingerprint(body):
            raise IdempotencyConflict(
                f"idempotency key {key!r} was already used for a different request")
        return rec.response

    def remember(self, key: str, body: dict, response: dict, *, now: float | None = None) -> None:
        if not key:
            return
        now = time.time() if now is None else now
        self._records[key] = _Record(fingerprint(body), response, now)

    def __len__(self) -> int:
        return len(self._records)
