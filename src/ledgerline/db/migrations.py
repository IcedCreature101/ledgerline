"""Schema, applied in order. Each migration is idempotent so a restarted deploy is safe."""
from __future__ import annotations

import sqlite3

SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS merchants (
        id          TEXT PRIMARY KEY,
        name        TEXT NOT NULL,
        currency    TEXT NOT NULL,
        fee_schedule TEXT NOT NULL DEFAULT 'standard',
        created_at  TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS transactions (
        id           TEXT PRIMARY KEY,
        merchant_id  TEXT NOT NULL REFERENCES merchants(id),
        amount_minor INTEGER NOT NULL,
        currency     TEXT NOT NULL,
        status       TEXT NOT NULL,        -- authorized | settled | refunded | failed
        created_at   TEXT NOT NULL,        -- ISO-8601 UTC
        settled_at   TEXT
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS ix_transactions_merchant_created
        ON transactions (merchant_id, created_at)
    """,
    """
    CREATE TABLE IF NOT EXISTS payout_accounts (
        id          TEXT PRIMARY KEY,
        merchant_id TEXT NOT NULL REFERENCES merchants(id),
        iban        TEXT NOT NULL,
        verified    INTEGER NOT NULL DEFAULT 0
    )
    """,
]


def migrate(conn: sqlite3.Connection) -> None:
    for statement in SCHEMA:
        conn.execute(statement)
    conn.commit()
