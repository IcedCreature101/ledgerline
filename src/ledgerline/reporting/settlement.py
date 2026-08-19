"""Settlement dates.

Money captured today does not settle today. Anything after the daily cutoff rolls to the next settlement
date, and settlement only happens on business days — a capture late on Friday settles on Monday.

Everything here is computed in UTC. A merchant in Auckland and one in Los Angeles settle on the same
schedule, and deriving the date from a server's local clock is how a batch ends up on the wrong day
twice a year when the server's timezone shifts.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

WEEKEND = {5, 6}          # Saturday, Sunday


def next_business_day(d: date) -> date:
    while d.weekday() in WEEKEND:
        d += timedelta(days=1)
    return d


def settlement_date(captured_at: datetime, *, cutoff_hour_utc: int = 22) -> date:
    """The date on which a capture at `captured_at` settles."""
    if captured_at.tzinfo is None:
        raise ValueError("captured_at must be timezone-aware — a naive timestamp has no cutoff")
    utc = captured_at.astimezone(timezone.utc)
    d = utc.date()
    if utc.hour >= cutoff_hour_utc:
        d += timedelta(days=1)
    return next_business_day(d)


def batch_key(captured_at: datetime, *, cutoff_hour_utc: int = 22) -> str:
    return settlement_date(captured_at, cutoff_hour_utc=cutoff_hour_utc).isoformat()
