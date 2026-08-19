"""LGR-103 — an IBAN from a corridor we do not process is refused at onboarding."""
from ledgerline.api.app import build_app, reset_state
from ledgerline.api.router import Request
from ledgerline.validation.iban import is_supported_country, validate_iban

# Real, correctly-checksummed IBANs from countries absent from the published-length table.
UNSUPPORTED = [
    "MT84MALT011000012345MTLCAST001S",   # Malta
    "BR9700360305000010009795493P1",     # Brazil
    "TR330006100519786457841326",        # Türkiye
]
SUPPORTED = ["GB82WEST12345698765432", "DE89370400440532013000"]


def test_an_unsupported_country_is_refused_even_though_it_checksums():
    for iban in UNSUPPORTED:
        assert not is_supported_country(iban)
        assert not validate_iban(iban), f"{iban} was accepted for an unsupported corridor"


def test_supported_countries_are_unaffected():
    for iban in SUPPORTED:
        assert validate_iban(iban)


def test_the_api_refuses_to_store_an_unsupported_payout_account():
    reset_state()
    app = build_app()
    resp = app.dispatch(Request("POST", "/v1/accounts",
                                {"merchant_id": "m_1", "iban": UNSUPPORTED[0]}))
    assert resp.status == 422
    assert resp.body["error"]["code"] == "invalid_iban"
