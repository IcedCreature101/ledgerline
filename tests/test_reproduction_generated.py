import pytest
from ledgerline.db.connection import connect
from ledgerline.db.migrations import migrate
from ledgerline.db.repository import Transaction, TransactionRepository
from ledgerline.core.money import Money


def test_export_settled_returns_all_settled_transactions():
    # Set up in‑memory DB and schema
    conn = connect(":memory:")
    migrate(conn)

    # Insert a merchant (schema: id, name, currency, fee_schedule, created_at)
    conn.execute(
        "INSERT INTO merchants VALUES ('m_1','Test Merchant','USD','standard','2024-01-01')"
    )

    repo = TransactionRepository(conn)

    # Create a mix of authorized and settled transactions.
    # Pattern: authorized, settled, authorized, settled, authorized, settled
    statuses = ["authorized", "settled", "authorized", "settled", "authorized", "settled"]
    for i, status in enumerate(statuses):
        created_at = f"2024-01-{i+1:02d}T10:00:00+00:00"
        settled_at = (
            f"2024-01-{i+2:02d}T10:00:00+00:00" if status == "settled" else None
        )
        txn = Transaction(
            f"txn_{i}",
            "m_1",
            Money(1000 + i, "USD"),
            status,
            created_at,
            settled_at,
        )
        repo.add(txn)

    # Export with a page size that forces paging.
    exported = repo.export_settled("m_1", page_size=2)

    # All three settled transactions should be present, in order of creation.
    expected_ids = ["txn_1", "txn_3", "txn_5"]
    assert [t.id for t in exported] == expected_ids
    assert len(exported) == 3
