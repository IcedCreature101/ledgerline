import pytest
from datetime import date

from ledgerline.reporting.periods import month_period


def test_february_month_period_ends_on_last_day():
    # February 2024 is a leap year and has 29 days.
    period = month_period(2024, 2)
    assert period.start == date(2024, 2, 1), "Period should start on the first of the month"
    assert period.end == date(2024, 2, 29), "Period should end on the last day of February"
    # Ensure the period length matches the number of days in February 2024.
    assert period.days() == 29, "Period should span exactly 29 days for February 2024"
