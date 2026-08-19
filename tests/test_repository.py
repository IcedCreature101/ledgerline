import pytest

from ledgerline.core.money import Money
from ledgerline.db.connection import connect, transaction
from ledgerline.db.migrations import migrate
from ledgerline.db.repository import Transaction, TransactionRepository


@pytest.fixture()
def repo():
    conn = connect(":memory:")
    migrate(conn)
    conn.execute("INSERT INTO merchants VALUES ('m_1','Northwind','USD','standard','2024-03-01')")
    conn.commit()
    return TransactionRepository(conn)


def _txn(i, status="settled"):
    return Transaction(f"txn_{i:03d}", "m_1", Money(1000 + i, "USD"), status,
                       f"2024-03-{i + 1:02d}T10:00:00+00:00",
                       f"2024-03-{i + 2:02d}T10:00:00+00:00" if status == "settled" else None)


def test_a_transaction_round_trips(repo):
    repo.add(_txn(0))
    got = repo.get("txn_000")
    assert got.amount == Money(1000, "USD") and got.status == "settled"


def test_an_unknown_id_is_none(repo):
    assert repo.get("txn_nope") is None


def test_counting_a_merchants_transactions(repo):
    for i in range(4):
        repo.add(_txn(i))
    assert repo.count_for_merchant("m_1") == 4


def test_marking_settled_records_when(repo):
    from datetime import datetime, timezone
    repo.add(_txn(0, status="authorized"))
    repo.mark_settled("txn_000", datetime(2024, 3, 5, tzinfo=timezone.utc))
    assert repo.get("txn_000").status == "settled"
    assert repo.get("txn_000").settled_at.startswith("2024-03-05")


def test_one_page_of_settled_transactions(repo):
    for i in range(10):
        repo.add(_txn(i))
    page = repo.list_settled("m_1", limit=4)
    assert [t.id for t in page] == ["txn_000", "txn_001", "txn_002", "txn_003"]


def test_paging_walks_the_whole_settled_set(repo):
    for i in range(10):
        repo.add(_txn(i))
    assert len(repo.export_settled("m_1", page_size=4)) == 10


def test_the_export_is_oldest_first(repo):
    for i in range(5):
        repo.add(_txn(i))
    ids = [t.id for t in repo.export_settled("m_1")]
    assert ids == sorted(ids)


def test_a_rolled_back_transaction_leaves_nothing_behind(repo):
    with pytest.raises(RuntimeError):
        with transaction(repo.conn):
            repo.conn.execute(
                "INSERT INTO transactions VALUES ('txn_x','m_1',100,'USD','settled','2024-03-01',NULL)")
            raise RuntimeError("boom")
    assert repo.get("txn_x") is None
