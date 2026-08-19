import pytest

from ledgerline.api.app import build_app, reset_state
from ledgerline.api.router import Request

BODY = {"merchant_id": "m_1", "amount_minor": 2500, "currency": "USD"}


@pytest.fixture()
def app():
    reset_state()
    return build_app()


def _create(app, body=None, key="key-1"):
    return app.dispatch(Request("POST", "/v1/payments", dict(body or BODY), {"Idempotency-Key": key}))


def test_creating_a_payment_authorizes_it(app):
    resp = _create(app)
    assert resp.status == 201
    assert resp.body["status"] == "authorized"
    assert resp.body["amount_minor"] == 2500


def test_the_fee_is_reported_with_the_payment(app):
    # 25.00 @ 2.9% = 0.725, which banker's rounding settles on 0.72, plus the 0.30 fixed component
    assert _create(app).body["fee_minor"] == 102


def test_a_payment_can_be_read_back(app):
    created = _create(app).body
    got = app.dispatch(Request("GET", f"/v1/payments/{created['id']}"))
    assert got.status == 200 and got.body["id"] == created["id"]


def test_an_unknown_payment_is_404(app):
    assert app.dispatch(Request("GET", "/v1/payments/pay_nope")).status == 404


def test_retrying_with_the_same_key_and_the_same_body_returns_the_original(app):
    first = _create(app).body
    again = _create(app)
    assert again.status == 200 and again.body["id"] == first["id"]


def test_reusing_a_key_for_a_different_amount_is_a_conflict(app):
    _create(app)
    clash = _create(app, {**BODY, "amount_minor": 9900})
    assert clash.status == 409


def test_an_unsupported_currency_is_rejected(app):
    assert _create(app, {**BODY, "currency": "ZZZ"}).status == 400


def test_capturing_the_full_amount(app):
    payment = _create(app).body
    resp = app.dispatch(Request("POST", f"/v1/payments/{payment['id']}/capture",
                                {"amount_minor": 2500}))
    assert resp.status == 200
    assert resp.body["status"] == "captured" and resp.body["remaining_minor"] == 0


def test_a_partial_capture_leaves_the_rest_held(app):
    payment = _create(app).body
    resp = app.dispatch(Request("POST", f"/v1/payments/{payment['id']}/capture",
                                {"amount_minor": 1000}))
    assert resp.body["status"] == "partially_captured"
    assert resp.body["remaining_minor"] == 1500


def test_refunding_across_order_lines(app):
    payment = _create(app).body
    resp = app.dispatch(Request("POST", f"/v1/payments/{payment['id']}/refund", {
        "amount_minor": 2500,
        "lines": [{"sku": "A", "amount_minor": 1000}, {"sku": "B", "amount_minor": 1500}]}))
    assert resp.status == 200
    assert resp.body["refunded_minor"] == 2500
    assert [a["amount_minor"] for a in resp.body["allocation"]] == [1000, 1500]
