import pytest

from ledgerline.runtime.clock import Clock, FrozenClock
from ledgerline.runtime.retry import RetriesExhausted, retry


def test_a_call_that_succeeds_is_not_repeated():
    calls = []
    assert retry(lambda: calls.append(1) or "ok", idempotent=True, sleep=lambda _: None) == "ok"
    assert len(calls) == 1


def test_a_flaky_call_succeeds_on_a_later_attempt():
    state = {"n": 0}

    def flaky():
        state["n"] += 1
        if state["n"] < 3:
            raise ConnectionError("reset")
        return "ok"

    assert retry(flaky, attempts=3, idempotent=True, sleep=lambda _: None) == "ok"
    assert state["n"] == 3


def test_running_out_of_attempts_says_so():
    def always():
        raise ConnectionError("reset")

    with pytest.raises(RetriesExhausted):
        retry(always, attempts=2, idempotent=True, sleep=lambda _: None)


def test_a_non_idempotent_operation_is_never_retried():
    with pytest.raises(ValueError, match="idempotent"):
        retry(lambda: None, attempts=3)


def test_a_single_attempt_needs_no_idempotency_promise():
    assert retry(lambda: "ok", attempts=1) == "ok"


def test_zero_attempts_is_refused():
    with pytest.raises(ValueError):
        retry(lambda: None, attempts=0, idempotent=True)


def test_the_frozen_clock_does_not_move():
    from datetime import datetime, timezone
    at = datetime(2024, 3, 1, 12, 0, tzinfo=timezone.utc)
    assert FrozenClock(at).now() == at


def test_a_frozen_clock_needs_a_timezone():
    from datetime import datetime
    with pytest.raises(ValueError):
        FrozenClock(datetime(2024, 3, 1, 12, 0))


def test_the_default_clock_is_timezone_aware():
    assert Clock().now().tzinfo is not None
