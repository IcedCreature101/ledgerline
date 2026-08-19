import pytest
from datetime import date

from ledgerline.reporting.periods import month_period


def test_february_2024_month_period_has_correct_end_and_length():
    # February 2024 is a leap year, should end on 2024-02-29 (29 days)
    period = month_period(2024, 2)
    assert period.end == date(2024, 2, 29), "February period should end on the last day of February"
    assert period.days() == 29, "February period should span 29 days"


def test_april_2024_month_period_has_correct_end_and_length():
    # April has 30 days, should end on 2024-04-30
    period = month_period(2024, 4)
    assert period.end == date(2024, 4, 30), "April period should end on the last day of April"
    assert period.days() == 30, "April period should span 30 days"
