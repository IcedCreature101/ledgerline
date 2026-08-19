"""Capturing against an authorization.

An authorization is a HOLD; capture is what actually moves the money. A merchant may capture in parts —
shipping half an order today and the rest on Friday — so an authorization can be captured several times.

The hold is the ceiling. Capturing beyond it is not something the card network will honour, and a
platform that lets it through discovers the problem as a chargeback weeks later.
"""
from __future__ import annotations

from datetime import datetime, timezone

from ledgerline.core.money import CurrencyMismatch, Money
from ledgerline.payments.authorization import Authorization, AuthorizationError


class OverCapture(AuthorizationError):
    """More was captured than the authorization holds."""


def capture(auth: Authorization, amount: Money, *, now: datetime | None = None) -> Money:
    """Capture `amount` against `auth`. Returns the amount captured.

    Raises OverCapture when the authorization does not hold enough for this capture.
    """
    now = now or datetime.now(timezone.utc)
    if auth.voided:
        raise AuthorizationError(f"{auth.auth_id} has been voided")
    if auth.is_expired(now):
        raise AuthorizationError(f"{auth.auth_id} expired on {auth.created_at.date()}")
    if amount.currency != auth.currency:
        raise CurrencyMismatch(f"{auth.auth_id} holds {auth.currency}, capture is {amount.currency}")
    if amount.is_zero() or amount.is_negative():
        raise AuthorizationError("a capture must be for a positive amount")

    if amount.minor > auth.amount.minor:
        raise OverCapture(
            f"cannot capture {amount} against {auth.auth_id}: authorized for {auth.amount}")

    auth.captured.append(amount)
    return amount


def capture_full(auth: Authorization, *, now: datetime | None = None) -> Money:
    """Capture whatever is still held."""
    return capture(auth, auth.remaining(), now=now)


def void(auth: Authorization) -> None:
    """Release the hold. Only possible while nothing has been captured."""
    if auth.captured:
        raise AuthorizationError(f"{auth.auth_id} has captures and cannot be voided")
    auth.voided = True
