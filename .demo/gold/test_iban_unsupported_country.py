"""LGR-103 — a payout account in a corridor we do not process is refused at onboarding.

WHAT THIS ASSERTS, AND WHAT IT DELIBERATELY DOES NOT

The ticket's claim is about onboarding: "we should not have taken it in the first place... Onboarding is
supposed to refuse any country we do not process, and it is letting them through instead." It says
nothing about which function should hold the check, because a support ticket has no opinion about that.

An earlier version of this file asserted `validate_iban(unsupported) is False` — that the corridor check
lives inside the IBAN validator. A run put it in the onboarding route instead, next to `validate_iban`
and using the `is_supported_country` predicate that already existed for it, which is a defensible reading
and arguably the better separation: one function answers "is this a well-formed IBAN", the other answers
"do we pay out there". Onboarding refused the account, the ticket was satisfied, and the oracle failed it
for putting the check one call away from where the oracle's author had imagined it.

An oracle that grades the location of a fix rather than its effect is testing the author's assumptions.
This one asserts what a merchant would notice.
"""
from ledgerline.api.app import build_app, reset_state
from ledgerline.api.router import Request

# Real, correctly-checksummed IBANs from countries absent from the published-length table.
UNSUPPORTED = [
    "MT84MALT011000012345MTLCAST001S",   # Malta
    "BR9700360305000010009795493P1",     # Brazil
    "TR330006100519786457841326",        # Türkiye
]
SUPPORTED = ["GB82WEST12345698765432", "DE89370400440532013000"]
TRANSPOSED = "GB82WEST12345698765433"


def _add(app, iban):
    return app.dispatch(Request("POST", "/v1/accounts", {"merchant_id": "m_1", "iban": iban}))


def _app():
    reset_state()
    return build_app()


def test_an_unsupported_corridor_is_refused_at_onboarding():
    app = _app()
    for iban in UNSUPPORTED:
        resp = _add(app, iban)
        assert resp.status == 422, f"{iban} was accepted for a corridor we do not process"
        assert resp.body["error"]["code"] == "invalid_iban"


def test_nothing_from_an_unsupported_corridor_is_ever_stored():
    """The consequence the ticket is actually about: a payout file going to a bank that returns it."""
    from ledgerline.api.routes import accounts
    app = _app()
    for iban in UNSUPPORTED:
        _add(app, iban)
    assert accounts.ACCOUNTS == {}, "an unsupported payout destination was stored"


def test_supported_corridors_are_unaffected():
    app = _app()
    for iban in SUPPORTED:
        assert _add(app, iban).status == 201, f"{iban} should still be accepted"


def test_a_transposed_digit_is_still_caught():
    assert _add(_app(), TRANSPOSED).status == 422


def test_formatting_a_supported_iban_still_works():
    resp = _add(_app(), "gb82 west 1234 5698 7654 32")
    assert resp.status == 201
    assert resp.body["iban"] == "GB82WEST12345698765432"
