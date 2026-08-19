import pytest

from ledgerline.api.app import build_app, reset_state
from ledgerline.api.router import Request


@pytest.fixture()
def app():
    reset_state()
    return build_app()


def test_a_valid_iban_is_registered(app):
    resp = app.dispatch(Request("POST", "/v1/accounts",
                                {"merchant_id": "m_1", "iban": "GB82WEST12345698765432"}))
    assert resp.status == 201
    assert resp.body["iban"] == "GB82WEST12345698765432"
    assert resp.body["verified"] is False


def test_the_stored_iban_is_normalized(app):
    resp = app.dispatch(Request("POST", "/v1/accounts",
                                {"merchant_id": "m_1", "iban": "gb82 west 1234 5698 7654 32"}))
    assert resp.body["iban"] == "GB82WEST12345698765432"
    assert resp.body["iban_formatted"] == "GB82 WEST 1234 5698 7654 32"


def test_a_transposed_digit_is_refused(app):
    resp = app.dispatch(Request("POST", "/v1/accounts",
                                {"merchant_id": "m_1", "iban": "GB82WEST12345698765433"}))
    assert resp.status == 422 and resp.body["error"]["code"] == "invalid_iban"


def test_an_empty_iban_is_refused(app):
    assert app.dispatch(Request("POST", "/v1/accounts",
                                {"merchant_id": "m_1", "iban": ""})).status == 422


def test_an_account_can_be_read_back(app):
    created = app.dispatch(Request("POST", "/v1/accounts",
                                   {"merchant_id": "m_1", "iban": "DE89370400440532013000"})).body
    got = app.dispatch(Request("GET", f"/v1/accounts/{created['id']}"))
    assert got.status == 200 and got.body["merchant_id"] == "m_1"


def test_an_unknown_account_is_404(app):
    assert app.dispatch(Request("GET", "/v1/accounts/acct_nope")).status == 404
