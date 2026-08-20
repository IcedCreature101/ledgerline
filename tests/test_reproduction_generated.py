import pytest
from datetime import date

from ledgerline.reporting.periods import month_period


def test_february_2024_month_period_has_correct_end():
    """
    A statement period for February 2024 should start on 2024‑02‑01 and end on 2024‑02‑29
    (29 days, because 2024 is a leap year). The buggy implementation extends the period
    into March, so this test will fail until the bug is fixed.
    """
    period = month_period(2024, 2)

    assert period.start == date(2024, 2, 1), "Period should start on the first of February"
    assert period.end == date(2024, 2, 29), "Period should end on the last day of February"
    assert period.days() == 29, "February 2024 has 29 days"
