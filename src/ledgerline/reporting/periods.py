"""Reporting periods.

A statement covers a calendar month: the first day of the month through its last day, inclusive. Getting
the boundary right is the whole job — a period that ends a day early drops the busiest day of the month
(month-end is when subscriptions bill), and one that ends a day late double-counts it into the next
statement.
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone


class PeriodError(ValueError):
    """The period asked for does not exist."""


@dataclass(frozen=True)
class Period:
    start: date
    end: date               # INCLUSIVE — the last day covered by the statement

    def contains(self, when: date | datetime) -> bool:
        d = when.date() if isinstance(when, datetime) else when
        return self.start <= d <= self.end

    def days(self) -> int:
        return (self.end - self.start).days + 1

    def label(self) -> str:
        return f"{self.start.isoformat()}..{self.end.isoformat()}"

    def as_utc_bounds(self) -> tuple[datetime, datetime]:
        """Half-open UTC instants [start, end) — the form a timestamp query wants."""
        lo = datetime.combine(self.start, time.min, tzinfo=timezone.utc)
        hi = datetime.combine(self.end + timedelta(days=1), time.min, tzinfo=timezone.utc)
        return lo, hi


def month_period(year: int, month: int) -> Period:
    """The statement period for a calendar month."""
    if not 1 <= month <= 12:
        raise PeriodError(f"month must be 1-12, got {month}")
    start = date(year, month, 1)
    # Determine the actual last day of the month (handles 28, 29, 30, 31 correctly)
    last_day = calendar.monthrange(year, month)[1]
    end = date(year, month, last_day)
    return Period(start, end)


def quarter_period(year: int, quarter: int) -> Period:
    if not 1 <= quarter <= 4:
        raise PeriodError(f"quarter must be 1-4, got {quarter}")
    first_month = (quarter - 1) * 3 + 1
    start = date(year, first_month, 1)
    last_month = first_month + 2
    end = date(year, last_month, calendar.monthrange(year, last_month)[1])
    return Period(start, end)


def previous_month(today: date) -> Period:
    """The month before `today`'s — what a statement run on the 1st should cover."""
    first_of_this = today.replace(day=1)
    last_of_previous = first_of_this - timedelta(days=1)
    return month_period(last_of_previous.year, last_of_previous.month)
