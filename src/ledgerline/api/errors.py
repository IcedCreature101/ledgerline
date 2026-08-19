"""Mapping domain errors onto HTTP responses.

A client cannot act on a 500. "Your currency is not supported" is a request problem the caller can fix;
"the rate feed is down" is ours and they should retry. Every domain exception is therefore mapped
deliberately, and anything unmapped is a 500 — which is correct, because an exception we did not plan
for IS a server error and should page someone rather than be dressed up as a client mistake.
"""
from __future__ import annotations

from ledgerline.core.currency import UnknownCurrency
from ledgerline.core.money import CurrencyMismatch
from ledgerline.fx.rates import RateUnavailable
from ledgerline.ledger.entries import UnbalancedEntry
from ledgerline.payments.authorization import AuthorizationError
from ledgerline.payments.idempotency import IdempotencyConflict
from ledgerline.payments.refunds import RefundError
from ledgerline.reporting.periods import PeriodError


class ApiError(Exception):
    """An error with an HTTP status already decided."""

    def __init__(self, status: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message

    def as_response(self) -> tuple[int, dict]:
        return self.status, {"error": {"code": self.code, "message": self.message}}


_STATUS: list[tuple[type, int, str]] = [
    (IdempotencyConflict, 409, "idempotency_conflict"),
    (UnknownCurrency,     400, "unsupported_currency"),
    (CurrencyMismatch,    400, "currency_mismatch"),
    (RefundError,         422, "refund_not_allowed"),
    (AuthorizationError,  422, "authorization_error"),
    (UnbalancedEntry,     500, "ledger_unbalanced"),
    (PeriodError,         400, "invalid_period"),
    (RateUnavailable,     503, "rate_unavailable"),
    (ValueError,          400, "invalid_request"),
    (KeyError,            404, "not_found"),
]


def to_response(exc: Exception) -> tuple[int, dict]:
    """Turn any exception into (status, body)."""
    if isinstance(exc, ApiError):
        return exc.as_response()
    for kind, status, code in _STATUS:
        if isinstance(exc, kind):
            return status, {"error": {"code": code, "message": str(exc)}}
    return 500, {"error": {"code": "internal_error", "message": "an unexpected error occurred"}}
