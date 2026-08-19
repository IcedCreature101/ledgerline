from ledgerline.core.money import Money
from ledgerline.db.repository import Transaction
from ledgerline.reporting.periods import month_period
from ledgerline.reporting.statements import build_statement


def _txn(day, major="100.00", txn_id=None):
    return Transaction(txn_id or f"txn_{day:02d}", "m_1", Money.from_major(major, "USD"),
                       "settled", f"2024-01-{day:02d}T12:00:00+00:00",
                       f"2024-01-{day + 1:02d}T12:00:00+00:00")


def test_a_statement_lists_the_transactions_in_its_period():
    period = month_period(2024, 1)
    stmt = build_statement("m_1", period, [_txn(5), _txn(10)])
    assert len(stmt.lines) == 2


def test_transactions_outside_the_period_are_left_out():
    period = month_period(2024, 1)
    outside = Transaction("txn_x", "m_1", Money.from_major("50.00", "USD"), "settled",
                          "2023-12-30T12:00:00+00:00", "2023-12-31T12:00:00+00:00")
    stmt = build_statement("m_1", period, [_txn(5), outside])
    assert [ln.transaction_id for ln in stmt.lines] == ["txn_05"]


def test_gross_fees_and_net_agree():
    stmt = build_statement("m_1", month_period(2024, 1), [_txn(5), _txn(6)])
    assert stmt.gross() == Money.from_major("200.00", "USD")
    assert stmt.net() == stmt.gross() - stmt.fees()


def test_each_line_nets_off_its_own_fee():
    stmt = build_statement("m_1", month_period(2024, 1), [_txn(5)])
    line = stmt.lines[0]
    assert line.net == line.gross - line.fee


def test_an_empty_statement_is_still_a_statement():
    stmt = build_statement("m_1", month_period(2024, 1), [])
    assert stmt.gross().is_zero() and stmt.net().is_zero() and stmt.as_dict()["transactions"] == 0


def test_the_statement_summary_is_serializable():
    stmt = build_statement("m_1", month_period(2024, 1), [_txn(5)])
    d = stmt.as_dict()
    assert d["merchant_id"] == "m_1" and d["period"] == "2024-01-01..2024-01-31"
