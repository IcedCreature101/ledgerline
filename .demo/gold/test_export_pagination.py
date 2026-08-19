"""LGR-108 — the settlement export returns every settled transaction."""
import pytest

from ledgerline.core.money import Money
from ledgerline.db.connection import connect
from ledgerline.db.migrations import migrate
from ledgerline.db.repository import Transaction, TransactionRepository


@pytest.fixture()
def repo():
    conn = connect(":memory:")
    migrate(conn)
    conn.execute("INSERT INTO merchants VALUES ('m_1','Northwind','USD','standard','2024-03-01')")
    conn.commit()
    return TransactionRepository(conn)


def _add(repo, count, settled_every=1):
    settled = []
    for i in range(count):
        status = "settled" if (i % settled_every == 0) else "authorized"
        if status == "settled":
            settled.append(f"txn_{i:03d}")
        repo.add(Transaction(f"txn_{i:03d}", "m_1", Money(1000 + i, "USD"), status,
                             f"2024-03-{(i % 28) + 1:02d}T10:00:00+00:00",
                             "2024-04-01T10:00:00+00:00" if status == "settled" else None))
    return settled


def test_an_export_interleaved_with_unsettled_rows_is_complete(repo):
    expected = _add(repo, 30, settled_every=3)
    got = [t.id for t in repo.export_settled("m_1", page_size=5)]
    assert got == expected


def test_a_page_of_mixed_statuses_does_not_end_the_export_early(repo):
    expected = _add(repo, 12, settled_every=2)
    assert len(repo.export_settled("m_1", page_size=4)) == len(expected)


def test_every_exported_row_is_settled(repo):
    _add(repo, 20, settled_every=4)
    assert all(t.status == "settled" for t in repo.export_settled("m_1", page_size=3))


def test_an_all_settled_export_is_unchanged(repo):
    expected = _add(repo, 10)
    assert [t.id for t in repo.export_settled("m_1", page_size=4)] == expected


def test_a_merchant_with_nothing_settled_exports_nothing(repo):
    _add(repo, 5, settled_every=999)
    assert repo.export_settled("m_1") == []
