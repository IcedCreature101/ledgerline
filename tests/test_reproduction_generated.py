import pytest
from datetime import date

from ledgerline.reporting.periods import month_period, PeriodError


def test_month_period_february_2024_ends_on_last_day():
    """February 2024 has 29 days (leap year). The period should end on 2024‑02‑29,
    not spill into March."""
    period = month_period(2024, 2)
    assert period.start == date(2024, 2, 1)
    assert period.end == date(2024, 2, 29)
    # The number of days in the period should be exactly 29 (inclusive range).
    assert period.days() == 29


def test_month_period_invalid_month_raises():
    """Verify the guard clause still works for out‑of‑range months."""
    with pytest.raises(PeriodError):
        month_period(2024, 0)
    with pytest.raises(PeriodError):
        month_period(2024, 13)
