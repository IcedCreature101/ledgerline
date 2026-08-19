"""Merchant payout-account endpoints."""
from __future__ import annotations

import itertools

from ledgerline.api.router import Request, Router
from ledgerline.validation.iban import format_iban, normalize, validate_iban

router = Router()
_account_seq = itertools.count(1)

ACCOUNTS: dict[str, dict] = {}


def _reset_state() -> None:
    ACCOUNTS.clear()


@router.route("POST", "/v1/accounts")
def add_payout_account(request: Request):
    """Register a payout destination.

    The IBAN is validated here, at the boundary — once it is stored, the next thing that touches it is a
    real payout file going to a real bank.
    """
    iban = request.body.get("iban", "")
    if not validate_iban(iban):
        return 422, {"error": {"code": "invalid_iban",
                               "message": "that IBAN is not one we can pay out to"}}
    account_id = f"acct_{next(_account_seq):06d}"
    record = {
        "id": account_id,
        "merchant_id": request.body["merchant_id"],
        "iban": normalize(iban),
        "iban_formatted": format_iban(iban),
        "verified": False,
    }
    ACCOUNTS[account_id] = record
    return 201, record


@router.route("GET", "/v1/accounts/<account_id>")
def get_account(request: Request, account_id: str):
    if account_id not in ACCOUNTS:
        raise KeyError(f"no account {account_id}")
    return 200, ACCOUNTS[account_id]
