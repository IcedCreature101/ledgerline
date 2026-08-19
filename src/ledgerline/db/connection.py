"""SQLite connection handling.

SQLite because the demo has to run anywhere with no service to stand up; the access pattern is the same
one a real deployment uses against Postgres, so the repository layer above is unchanged by the swap.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager


def connect(database: str = ":memory:") -> sqlite3.Connection:
    conn = sqlite3.connect(database)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def transaction(conn: sqlite3.Connection):
    """Commit on success, roll back on any exception. A half-written transfer is worse than none."""
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
