from datetime import date, datetime, timezone

import pytest

from ledgerline.reporting.settlement import batch_key, next_business_day, settlement_date


def test_a_capture_before_the_cutoff_settles_the_same_day():
    assert settlement_date(datetime(2024, 3, 6, 21, 30, tzinfo=timezone.utc)) == date(2024, 3, 6)


def test_a_capture_after_the_cutoff_rolls_to_the_next_day():
    assert settlement_date(datetime(2024, 3, 6, 22, 30, tzinfo=timezone.utc)) == date(2024, 3, 7)


def test_a_friday_night_capture_settles_on_monday():
    assert settlement_date(datetime(2024, 3, 8, 23, 0, tzinfo=timezone.utc)) == date(2024, 3, 11)


def test_a_saturday_capture_settles_on_monday():
    assert settlement_date(datetime(2024, 3, 9, 10, 0, tzinfo=timezone.utc)) == date(2024, 3, 11)


def test_the_cutoff_hour_is_configurable():
    when = datetime(2024, 3, 6, 18, 0, tzinfo=timezone.utc)
    assert settlement_date(when, cutoff_hour_utc=17) == date(2024, 3, 7)


def test_a_naive_timestamp_is_refused():
    with pytest.raises(ValueError):
        settlement_date(datetime(2024, 3, 6, 10, 0))


def test_a_non_utc_timestamp_is_converted_before_the_cutoff_is_applied():
    from datetime import timedelta
    tokyo = timezone(timedelta(hours=9))
    # 2024-03-07 06:00 in Tokyo is 2024-03-06 21:00 UTC — before the cutoff, so it settles on the 6th
    assert settlement_date(datetime(2024, 3, 7, 6, 0, tzinfo=tokyo)) == date(2024, 3, 6)


def test_next_business_day_skips_the_weekend():
    assert next_business_day(date(2024, 3, 9)) == date(2024, 3, 11)
    assert next_business_day(date(2024, 3, 8)) == date(2024, 3, 8)


def test_the_batch_key_is_the_settlement_date():
    assert batch_key(datetime(2024, 3, 6, 10, 0, tzinfo=timezone.utc)) == "2024-03-06"
