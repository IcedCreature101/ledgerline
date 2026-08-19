"""Data access for merchants and transactions.

Everything the reporting and export paths need comes through here. The methods that PAGE are the ones to
read carefully: an export walks pages until it sees a short one, so a page that comes back short for any
reason other than "there is no more data" ends the export early and silently loses rows.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime

from ledgerline.core.money import Money


@dataclass(frozen=True)
class Transaction:
    id: str
    merchant_id: str
    amount: Money
    status: str
    created_at: str
    settled_at: str | None = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Transaction":
        return cls(
            id=row["id"],
            merchant_id=row["merchant_id"],
            amount=Money(int(row["amount_minor"]), row["currency"]),
            status=row["status"],
            created_at=row["created_at"],
            settled_at=row["settled_at"],
        )


class TransactionRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self.conn = conn

    # ── writes ──────────────────────────────────────────────────────────────────────────────────
    def add(self, txn: Transaction) -> None:
        self.conn.execute(
            "INSERT INTO transactions (id, merchant_id, amount_minor, currency, status, "
            "created_at, settled_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (txn.id, txn.merchant_id, txn.amount.minor, txn.amount.currency, txn.status,
             txn.created_at, txn.settled_at))
        self.conn.commit()

    def mark_settled(self, txn_id: str, settled_at: datetime) -> None:
        self.conn.execute(
            "UPDATE transactions SET status = 'settled', settled_at = ? WHERE id = ?",
            (settled_at.isoformat(), txn_id))
        self.conn.commit()

    # ── reads ───────────────────────────────────────────────────────────────────────────────────
    def get(self, txn_id: str) -> Transaction | None:
        row = self.conn.execute("SELECT * FROM transactions WHERE id = ?", (txn_id,)).fetchone()
        return Transaction.from_row(row) if row else None

    def count_for_merchant(self, merchant_id: str) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) AS n FROM transactions WHERE merchant_id = ?", (merchant_id,)).fetchone()
        return int(row["n"])

    def list_settled(self, merchant_id: str, *, limit: int = 50, offset: int = 0) -> list[Transaction]:
        """One page of this merchant's SETTLED transactions, oldest first.

        Used by the settlement export, which pages until it receives fewer rows than it asked for.
        """
        rows = self.conn.execute(
            "SELECT * FROM transactions WHERE merchant_id = ? "
            "ORDER BY created_at ASC, id ASC LIMIT ? OFFSET ?",
            (merchant_id, limit, offset)).fetchall()
        return [Transaction.from_row(r) for r in rows if r["status"] == "settled"]

    def export_settled(self, merchant_id: str, *, page_size: int = 50) -> list[Transaction]:
        """Every settled transaction for a merchant, walked one page at a time."""
        out: list[Transaction] = []
        offset = 0
        while True:
            page = self.list_settled(merchant_id, limit=page_size, offset=offset)
            out.extend(page)
            if len(page) < page_size:
                return out
            offset += page_size
