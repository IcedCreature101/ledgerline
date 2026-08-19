"""The clock, behind a seam.

Every timestamp in this system comes from here so a test can freeze it. Code that calls
`datetime.now()` directly is code whose month-end behaviour can only be tested in the last week of
the month.
"""
from __future__ import annotations

from datetime import datetime, timezone


class Clock:
    def now(self) -> datetime:
        return datetime.now(timezone.utc)

    def today(self):
        return self.now().date()


class FrozenClock(Clock):
    def __init__(self, at: datetime) -> None:
        if at.tzinfo is None:
            raise ValueError("a frozen clock needs a timezone-aware instant")
        self._at = at

    def now(self) -> datetime:
        return self._at


_default = Clock()


def now() -> datetime:
    return _default.now()
