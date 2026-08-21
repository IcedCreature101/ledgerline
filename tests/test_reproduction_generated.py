import pytest

from ledgerline.validation.iban import validate_iban


def test_maltese_iban_rejected_as_unsupported_payout_corridor():
    # A genuine, correctly-formed Maltese IBAN (checksum and length are both valid).
    # Malta is not a corridor we are licensed to pay out to, so onboarding must
    # refuse it even though the IBAN itself is well-formed.
    malta_iban = "MT84MALT011000012345MTLCAST001S"

    assert validate_iban(malta_iban) is False
