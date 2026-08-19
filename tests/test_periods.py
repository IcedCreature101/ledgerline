from datetime import date, datetime, timezone

import pytest

from ledgerline.reporting.periods import PeriodError, month_period, previous_month, quarter_period


def test_january_covers_the_whole_month():
    p = month_period(2024, 1)
    assert (p.start, p.end) == (date(2024, 1, 1), date(2024, 1, 31))
    assert p.days() == 31


def test_a_31_day_month_later_in_the_year():
    p = month_period(2024, 7)
    assert (p.start, p.end) == (date(2024, 7, 1), date(2024, 7, 31))


def test_december_does_not_spill_into_the_new_year():
    assert month_period(2024, 12).end == date(2024, 12, 31)


def test_a_date_inside_the_period_is_contained():
    p = month_period(2024, 1)
    assert p.contains(date(2024, 1, 17))
    assert p.contains(datetime(2024, 1, 31, 23, 0, tzinfo=timezone.utc))
    assert not p.contains(date(2023, 12, 31))


def test_utc_bounds_are_half_open():
    lo, hi = month_period(2024, 1).as_utc_bounds()
    assert lo == datetime(2024, 1, 1, tzinfo=timezone.utc)
    assert hi == datetime(2024, 2, 1, tzinfo=timezone.utc)


def test_a_month_outside_1_to_12_is_refused():
    for bad in (0, 13, -1):
        with pytest.raises(PeriodError):
            month_period(2024, bad)


def test_quarters_end_on_the_last_day_of_their_last_month():
    assert quarter_period(2024, 1) .end == date(2024, 3, 31)
    assert quarter_period(2024, 4).end == date(2024, 12, 31)


def test_a_quarter_outside_1_to_4_is_refused():
    with pytest.raises(PeriodError):
        quarter_period(2024, 5)


def test_previous_month_of_an_august_run_is_july():
    assert previous_month(date(2024, 8, 3)).label() == "2024-07-01..2024-07-31"


def test_the_period_label_is_readable():
    assert month_period(2024, 1).label() == "2024-01-01..2024-01-31"
