"""The operator console — what the application currently reports.

    python -m ledgerline.demo               # every report
    python -m ledgerline.demo fees          # one of them

This is the surface support looks at when a merchant calls. It prints what the system produces; whether
that is what the merchant's contract entitles them to is the question a ticket asks.
"""
from __future__ import annotations

import sys
from datetime import date, datetime, timezone

from ledgerline.api.app import build_app, reset_state
from ledgerline.api.router import Request
from ledgerline.core.money import Money
from ledgerline.db.connection import connect
from ledgerline.db.migrations import migrate
from ledgerline.db.repository import Transaction, TransactionRepository
from ledgerline.fees.schedule import STANDARD, calculate_fee, effective_rate
from ledgerline.fx.rates import RateTable, convert
from ledgerline.payments.authorization import authorize
from ledgerline.payments.capture import capture
from ledgerline.payments.refunds import OrderLine, allocate
from ledgerline.reporting.periods import month_period
from ledgerline.reporting.settlement import settlement_date
from ledgerline.validation.iban import format_iban, validate_iban


def _line(label: str, value) -> None:
    print(f"  {label:<46} {value}")


def report_fees() -> None:
    print("\nFEES — standard tiered schedule")
    for major in ("50.00", "750.00", "5000.00", "50000.00"):
        amount = Money.from_major(major, "USD")
        fee = calculate_fee(amount, STANDARD)
        _line(f"payment of {amount}", f"fee {fee}  (effective {effective_rate(amount, STANDARD)})")


def report_refund() -> None:
    print("\nREFUND — 10.00 USD returned across three 5.00 order lines")
    lines = [OrderLine(f"SKU-{c}", Money.from_major("5.00", "USD")) for c in "ABC"]
    shares = allocate(Money.from_major("10.00", "USD"), lines)
    for ln, share in zip(lines, shares):
        _line(f"{ln.sku} share", str(share))
    _line("returned to the customer in total", str(Money(sum(s.minor for s in shares), "USD")))


def report_iban() -> None:
    print("\nPAYOUT ACCOUNTS — validation at onboarding")
    for iban in ("GB82WEST12345698765432",          # United Kingdom
                 "DE89370400440532013000",          # Germany
                 "MT84MALT011000012345MTLCAST001S", # Malta
                 "GB82WEST12345698765433"):         # a transposed digit
        _line(format_iban(iban), "accepted" if validate_iban(iban) else "rejected")


def report_idempotency() -> None:
    print("\nAPI — a client retrying a payment it never got a response to")
    reset_state()
    app = build_app()
    first = app.dispatch(Request("POST", "/v1/payments",
                                 {"merchant_id": "m_1", "amount_minor": 2500, "currency": "USD"},
                                 {"Idempotency-Key": "key-1"}))
    _line("first attempt", f"{first.status} {first.body.get('id', first.body)}")
    retry = app.dispatch(Request("POST", "/v1/payments",
                                 {"amount_minor": 2500, "currency": "USD", "merchant_id": "m_1"},
                                 {"Idempotency-Key": "key-1"}))
    _line("retry, same key, same payment", f"{retry.status} {retry.body.get('id', retry.body)}")


def report_capture() -> None:
    print("\nCAPTURE — partial captures against a 100.00 USD authorization")
    auth = authorize("m_1", Money.from_major("100.00", "USD"))
    for attempt in ("80.00", "80.00"):
        try:
            capture(auth, Money.from_major(attempt, "USD"))
            _line(f"capture {attempt}", "accepted")
        except Exception as exc:                    # noqa: BLE001
            _line(f"capture {attempt}", f"refused — {type(exc).__name__}")
    _line("held / captured", f"{auth.amount} held, {auth.captured_total()} captured")


def report_periods() -> None:
    print("\nSTATEMENT PERIODS")
    for year, month in ((2024, 1), (2024, 2), (2024, 4), (2024, 12)):
        _line(f"{year}-{month:02d} statement covers", month_period(year, month).label())
    _line("capture at 2024-03-01 21:30 UTC settles", settlement_date(
        datetime(2024, 3, 1, 21, 30, tzinfo=timezone.utc)).isoformat())
    _line("capture at 2024-03-01 22:30 UTC settles", settlement_date(
        datetime(2024, 3, 1, 22, 30, tzinfo=timezone.utc)).isoformat())


def report_fx() -> None:
    print("\nFX — converting a 100.00 USD payment for settlement")
    table = RateTable(as_of=date(2024, 3, 1))
    table.put("USD", "EUR", "0.92")
    table.put("USD", "GBP", "0.79")
    amount = Money.from_major("100.00", "USD")
    for quote in ("EUR", "GBP", "SEK"):
        try:
            _line(f"USD → {quote}", str(convert(amount, quote, table)))
        except Exception as exc:                    # noqa: BLE001
            _line(f"USD → {quote}", f"refused — {type(exc).__name__}")


def report_export() -> None:
    print("\nSETTLEMENT EXPORT — every settled transaction for a merchant")
    conn = connect(":memory:")
    migrate(conn)
    conn.execute("INSERT INTO merchants VALUES ('m_1','Northwind','USD','standard','2024-03-01')")
    repo = TransactionRepository(conn)
    settled = 0
    for i in range(12):
        status = "settled" if i % 3 else "authorized"
        settled += status == "settled"
        repo.add(Transaction(f"txn_{i:03d}", "m_1", Money(1000 + i, "USD"), status,
                             f"2024-03-{i + 1:02d}T10:00:00+00:00",
                             f"2024-03-{i + 2:02d}T10:00:00+00:00" if status == "settled" else None))
    exported = repo.export_settled("m_1", page_size=5)
    _line("settled transactions in the database", settled)
    _line("rows the export produced", len(exported))


REPORTS = {
    "fees": report_fees, "refund": report_refund, "iban": report_iban,
    "idempotency": report_idempotency, "capture": report_capture,
    "periods": report_periods, "fx": report_fx, "export": report_export,
}


def main(argv: list[str]) -> int:
    names = argv[1:] or list(REPORTS)
    for name in names:
        fn = REPORTS.get(name)
        if fn is None:
            print(f"unknown report {name!r}; known: {', '.join(REPORTS)}")
            return 2
        fn()
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
