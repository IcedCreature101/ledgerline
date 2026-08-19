"""Reporting endpoints — statements and settlement exports."""
from __future__ import annotations

from ledgerline.api.router import Request, Router
from ledgerline.reporting.periods import month_period
from ledgerline.reporting.statements import build_statement

router = Router()

# The repository the report handlers read through, installed by the application at wiring time.
REPOSITORY = None


@router.route("GET", "/v1/merchants/<merchant_id>/statement")
def get_statement(request: Request, merchant_id: str):
    year = int(request.query.get("year", 0))
    month = int(request.query.get("month", 0))
    period = month_period(year, month)
    txns = REPOSITORY.export_settled(merchant_id) if REPOSITORY else []
    statement = build_statement(merchant_id, period, txns)
    return 200, statement.as_dict()


@router.route("GET", "/v1/merchants/<merchant_id>/settlements")
def list_settlements(request: Request, merchant_id: str):
    page_size = int(request.query.get("page_size", 50))
    txns = REPOSITORY.export_settled(merchant_id, page_size=page_size) if REPOSITORY else []
    return 200, {
        "merchant_id": merchant_id,
        "count": len(txns),
        "transactions": [{"id": t.id, "amount_minor": t.amount.minor, "currency": t.amount.currency,
                          "settled_at": t.settled_at} for t in txns],
    }
