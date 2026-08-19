"""Payment endpoints."""
from __future__ import annotations

import itertools

from ledgerline.api.router import Request, Router
from ledgerline.core.money import Money
from ledgerline.fees.schedule import calculate_fee
from ledgerline.payments.authorization import authorize
from ledgerline.payments.capture import capture
from ledgerline.payments.idempotency import IdempotencyStore
from ledgerline.payments.refunds import OrderLine, refund

router = Router()
_payment_seq = itertools.count(1)

# Process-local state, which is what the demo needs; a deployment swaps these for the repository layer.
PAYMENTS: dict[str, dict] = {}
AUTHORIZATIONS: dict[str, object] = {}
IDEMPOTENCY = IdempotencyStore()


def _reset_state() -> None:
    PAYMENTS.clear()
    AUTHORIZATIONS.clear()
    IDEMPOTENCY._records.clear()


@router.route("POST", "/v1/payments")
def create_payment(request: Request):
    """Authorize a payment.

    Safe to retry: send the same `Idempotency-Key` and the original payment comes back rather than a
    second charge being made.
    """
    key = request.header("Idempotency-Key")
    body = request.body
    existing = IDEMPOTENCY.lookup(key, body)
    if existing is not None:
        return 200, existing

    amount = Money(int(body["amount_minor"]), body["currency"])
    merchant_id = body["merchant_id"]
    auth = authorize(merchant_id, amount)
    AUTHORIZATIONS[auth.auth_id] = auth

    payment_id = f"pay_{next(_payment_seq):06d}"
    response = {
        "id": payment_id,
        "authorization_id": auth.auth_id,
        "merchant_id": merchant_id,
        "amount_minor": amount.minor,
        "currency": amount.currency,
        "fee_minor": calculate_fee(amount).minor,
        "status": "authorized",
    }
    PAYMENTS[payment_id] = response
    IDEMPOTENCY.remember(key, body, response)
    return 201, response


@router.route("GET", "/v1/payments/<payment_id>")
def get_payment(request: Request, payment_id: str):
    if payment_id not in PAYMENTS:
        raise KeyError(f"no payment {payment_id}")
    return 200, PAYMENTS[payment_id]


@router.route("POST", "/v1/payments/<payment_id>/capture")
def capture_payment(request: Request, payment_id: str):
    if payment_id not in PAYMENTS:
        raise KeyError(f"no payment {payment_id}")
    payment = PAYMENTS[payment_id]
    auth = AUTHORIZATIONS[payment["authorization_id"]]
    amount = Money(int(request.body["amount_minor"]), payment["currency"])
    captured = capture(auth, amount)
    payment["status"] = "captured" if auth.remaining().is_zero() else "partially_captured"
    return 200, {
        "id": payment_id,
        "captured_minor": captured.minor,
        "captured_total_minor": auth.captured_total().minor,
        "remaining_minor": auth.remaining().minor,
        "status": payment["status"],
    }


@router.route("POST", "/v1/payments/<payment_id>/refund")
def refund_payment(request: Request, payment_id: str):
    if payment_id not in PAYMENTS:
        raise KeyError(f"no payment {payment_id}")
    payment = PAYMENTS[payment_id]
    currency = payment["currency"]
    amount = Money(int(request.body["amount_minor"]), currency)
    lines = [OrderLine(sku=ln["sku"], amount=Money(int(ln["amount_minor"]), currency))
             for ln in request.body["lines"]]
    result = refund(amount, lines)
    return 200, {
        "id": payment_id,
        "refunded_minor": result["allocated_total"].minor,
        "allocation": [{"sku": sku, "amount_minor": share.minor}
                       for sku, share in zip(result["lines"], result["allocated"])],
    }
