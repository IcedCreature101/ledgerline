import pytest
from datetime import date

def test_month_period_february_2024():
    from ledgerline.reporting.periods import month_period
    period = month_period(2024, 2)
    # The period should end on the last day of February (leap year)
    assert period.end == date(2024, 2, 29), "February period end date is incorrect"
    # The number of days in the period should match the month length
    assert period.days() == 29, "February period length is incorrect"
