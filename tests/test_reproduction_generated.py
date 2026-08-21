import pytest

from ledgerline.validation.iban import validate_iban


def test_malta_iban_rejected_because_country_not_licensed_for_payout():
    """
    Malta is a genuine, correctly checksummed IBAN (per the ticket), but the
    company is not licensed to pay out to Malta (nor Brazil nor Turkiye).
    Onboarding must reject IBANs from countries we don't process, even when
    the checksum and shape are otherwise fine.
    """
    malta_iban = "MT84MALT011000012345MTLCAST001S"

    assert validate_iban(malta_iban) is False
