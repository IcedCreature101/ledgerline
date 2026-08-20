from datetime import date

import pytest

from ledgerline.reporting.periods import month_period


def test_february_month_period_has_correct_end():
    # February 2024 is a leap year and has 29 days.
    period = month_period(2024, 2)
    # The period should end on the last day of February, not spill into March.
    assert period.end == date(2024, 2, 29)
    # The number of days in the period should be exactly 29.
    assert period.days() == 29
