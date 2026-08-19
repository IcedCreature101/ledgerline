"""LGR-106 — a statement period ends on the last day of its own month."""
import calendar
from datetime import date

from ledgerline.reporting.periods import month_period, previous_month


def test_february_in_a_leap_year():
    assert month_period(2024, 2).end == date(2024, 2, 29)


def test_february_in_a_common_year():
    assert month_period(2023, 2).end == date(2023, 2, 28)


def test_a_thirty_day_month():
    assert month_period(2024, 4).end == date(2024, 4, 30)
    assert month_period(2024, 9).end == date(2024, 9, 30)


def test_every_month_of_a_leap_year_and_a_common_year():
    for year in (2023, 2024):
        for month in range(1, 13):
            period = month_period(year, month)
            last = calendar.monthrange(year, month)[1]
            assert period.end == date(year, month, last), f"{year}-{month:02d}"
            assert period.days() == last


def test_a_period_never_reaches_into_the_next_month():
    for month in range(1, 13):
        period = month_period(2024, month)
        assert period.end.month == month


def test_the_previous_month_of_a_march_run_is_february():
    assert previous_month(date(2024, 3, 1)).label() == "2024-02-01..2024-02-29"
