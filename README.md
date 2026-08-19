# Ledgerline

Payment processing, double-entry ledger and settlement reporting.

Ledgerline authorizes and captures card payments, prices them against a merchant's fee schedule, keeps
the double-entry books behind them, and produces the monthly statements and settlement exports that
merchants reconcile their own accounts against.

```
src/ledgerline/
  api/          HTTP surface — routing, request validation, error mapping
    routes/     payments · payout accounts · reports
  core/         money in minor units, the currency table, settings
  ledger/       journal entries and posting; the balance invariant
  payments/     authorization, capture, refunds, idempotency
  fees/         the tiered pricing schedules
  fx/           rates and conversion
  validation/   IBAN and request validation
  db/           SQLite connection, schema, repositories
  reporting/    statement periods, settlement dates, statements
  runtime/      the clock seam and the retry helper
```

## Running it

Nothing to install but the test runner — Ledgerline is standard library only.

```bash
pip install -r requirements.txt
pytest                                  # the shipped suite
python -m ledgerline.demo               # the operator console
python -m ledgerline.demo fees          # one report
```

`python -m ledgerline.demo` prints what the application currently reports — fees, refunds, payout-account
validation, idempotent retries, captures, statement periods, FX conversions and the settlement export.
Whether those numbers are what a merchant's contract entitles them to is a separate question, and the one
a support ticket asks.

## Conventions worth knowing before you change anything

**Money is an integer of minor units.** `Money(1234, "USD")` is $12.34. Floats never appear; a ledger
that represents 0.10 + 0.20 as 0.30000000000000004 eventually fails to balance. Rates are applied through
`Money.apply_rate`, which quantises back to whole minor units with banker's rounding — over enough
transactions, ROUND_HALF_UP is biased and the merchant is systematically overcharged.

**The currency decides the exponent.** USD has 2 minor digits, JPY has 0, BHD has 3. Any hard-coded 100
is a bug waiting for a Japanese merchant.

**A journal entry that does not balance cannot be posted.** That invariant is why the books can be
trusted; `Ledger.is_healthy()` asserts the whole thing sums to zero.

**Everything is UTC.** Settlement dates and statement periods are derived from UTC instants, never a
server's local clock, and `runtime.clock` exists so a test can freeze time rather than wait for
month-end.

**Only idempotent operations may be retried.** `runtime.retry` refuses to retry anything not explicitly
declared idempotent, because retrying a capture is how a customer gets charged twice.

## Tests

```bash
pytest                    # the whole shipped suite
pytest tests/test_fees.py
```

`pyproject.toml` sets `testpaths = ["tests"]`, so a bare `pytest` collects the shipped suite and nothing
else.

## About `.demo/`

This repository is also the fixture for an autonomous-maintenance demonstration. `.demo/` holds the
tickets and the held-out tests they are graded against; `scripts/verify_demo.sh` reports whether the
checkout is a valid baseline and `scripts/reset_demo.sh` restores it. See `.demo/README.md`.

Nothing under `.demo/` is imported by the application, and `testpaths` keeps it out of the shipped suite.
