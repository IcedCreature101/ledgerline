from ledgerline.api.errors import ApiError, to_response
from ledgerline.core.currency import UnknownCurrency
from ledgerline.core.money import CurrencyMismatch
from ledgerline.payments.authorization import AuthorizationError
from ledgerline.payments.idempotency import IdempotencyConflict
from ledgerline.payments.refunds import RefundError
from ledgerline.reporting.periods import PeriodError


def test_an_unsupported_currency_is_the_callers_mistake():
    status, body = to_response(UnknownCurrency("ZZZ"))
    assert status == 400 and body["error"]["code"] == "unsupported_currency"


def test_a_reused_idempotency_key_is_a_conflict():
    assert to_response(IdempotencyConflict("k"))[0] == 409


def test_a_refund_that_is_not_allowed_is_unprocessable():
    assert to_response(RefundError("too much"))[0] == 422


def test_an_authorization_problem_is_unprocessable():
    assert to_response(AuthorizationError("expired"))[0] == 422


def test_a_currency_mismatch_is_a_bad_request():
    assert to_response(CurrencyMismatch("USD vs EUR"))[0] == 400


def test_an_invalid_period_is_a_bad_request():
    assert to_response(PeriodError("month 13"))[0] == 400


def test_a_missing_thing_is_404():
    assert to_response(KeyError("no payment"))[0] == 404


def test_an_unmapped_exception_is_a_server_error_and_says_nothing_more():
    status, body = to_response(RuntimeError("connection pool exhausted"))
    assert status == 500
    assert "pool" not in body["error"]["message"]


def test_an_api_error_carries_its_own_status():
    assert ApiError(418, "teapot", "no coffee").as_response()[0] == 418
