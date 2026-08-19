"""Runtime configuration, read once from the environment with documented defaults."""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    settlement_cutoff_hour_utc: int = 22   # transactions after this land on the next settlement date
    statement_timezone: str = "UTC"
    default_page_size: int = 50
    max_page_size: int = 500
    idempotency_ttl_seconds: int = 24 * 60 * 60
    database_url: str = ":memory:"


def load() -> Settings:
    return Settings(
        settlement_cutoff_hour_utc=int(os.getenv("LEDGERLINE_CUTOFF_HOUR", "22")),
        statement_timezone=os.getenv("LEDGERLINE_TZ", "UTC"),
        default_page_size=int(os.getenv("LEDGERLINE_PAGE_SIZE", "50")),
        max_page_size=int(os.getenv("LEDGERLINE_MAX_PAGE_SIZE", "500")),
        idempotency_ttl_seconds=int(os.getenv("LEDGERLINE_IDEMPOTENCY_TTL", str(24 * 60 * 60))),
        database_url=os.getenv("LEDGERLINE_DB", ":memory:"),
    )
