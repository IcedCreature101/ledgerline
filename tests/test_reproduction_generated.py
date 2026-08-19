import pytest

from ledgerline.db.connection import connect
from ledgerline.db.migrations import migrate
from ledgerline.db.repository import Transaction, TransactionRepository
from ledgerline.core.money import Money


def test_export_settled_returns_all_settled_transactions():
    # Set up an in‑memory database with the schema.
    conn = connect(":memory:")
    migrate(conn)

    # Insert a merchant (the columns are id, name, currency, fee_schedule, created_at).
    conn.execute(
        "INSERT INTO merchants VALUES ('m_test', 'Test Merchant', 'USD', 'standard', '2024-01-01')"
    )

    repo = TransactionRepository(conn)

    # Helper to add a transaction.
    def add_txn(idx: int, status: str) -> None:
        txn = Transaction(
            id=f"txn_{idx}",
            merchant_id="m_test",
            amount=Money(1000, "USD"),
            status=status,
            created_at=f"2024-01-{idx+1:02d}T10:00:00+00:00",
            settled_at=(
                f"2024-01-{idx+2:02d}T10:00:00+00:00" if status == "settled" else None
            ),
        )
        repo.add(txn)

    # Create six transactions where only the first and fourth are settled.
    # Pattern: settled, authorized, authorized, settled, authorized, authorized
    statuses = ["settled", "authorized", "authorized", "settled", "authorized", "authorized"]
    for i, st in enumerate(statuses):
        add_txn(i, st)

    # Export settled transactions with a small page size to trigger the bug.
    exported = repo.export_settled("m_test", page_size=2)

    # The export should contain **both** settled transactions.
    assert len(exported) == 2
    exported_ids = {t.id for t in exported}
    assert exported_ids == {"txn_0", "txn_3"}
