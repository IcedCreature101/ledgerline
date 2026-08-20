import pytest
from datetime import date

from ledgerline.reporting.periods import month_period


def test_february_2024_month_period():
    """February 2024 has 29 days (leap year). The period should end on Feb 29,
    not spill into March."""
    period = month_period(2024, 2)
    assert period.start == date(2024, 2, 1)
    assert period.end == date(2024, 2, 29)


def test_april_2024_month_period():
    """April has 30 days. The period should end on Apr 30,
    not spill into May."""
    period = month_period(2024, 4)
    assert period.start == date(2024, 4, 1)
    assert period.end == date(2024, 4, 30)
