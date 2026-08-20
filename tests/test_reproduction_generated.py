import pytest
from datetime import date

from ledgerline.reporting.periods import month_period


def test_month_period_april_2024():
    """April has 30 days; the period should end on April 30, not spill into May."""
    period = month_period(2024, 4)
    assert period.start == date(2024, 4, 1)
    assert period.end == date(2024, 4, 30)
    assert period.days() == 30
