import pytest

from ledgerline.validation.iban import (checksum_ok, country_of, format_iban, is_supported_country,
                                        normalize, validate_iban)

VALID = ["GB82WEST12345698765432", "DE89370400440532013000", "FR1420041010050500013M02606",
         "NL91ABNA0417164300", "ES9121000418450200051332"]


@pytest.mark.parametrize("iban", VALID)
def test_published_examples_validate(iban):
    assert validate_iban(iban)


def test_grouping_and_case_do_not_change_the_answer():
    assert validate_iban("gb82 west 1234 5698 7654 32")
    assert normalize("gb82 west 1234 5698 7654 32") == "GB82WEST12345698765432"


def test_a_transposed_digit_is_caught_by_the_checksum():
    assert not validate_iban("GB82WEST12345698765433")
    assert not checksum_ok("GB82WEST12345698765433")


def test_the_wrong_length_for_the_country_is_refused():
    assert not validate_iban("GB82WEST123456987654")        # two characters short for GB


def test_nonsense_is_refused_rather_than_raising():
    for bad in ("", "  ", "GB", "1234", "GB82!!!!12345698765432"):
        assert not validate_iban(bad)


def test_a_non_string_is_refused():
    assert not validate_iban(None)
    assert not validate_iban(1234)


def test_country_and_support_are_readable_separately():
    assert country_of("GB82WEST12345698765432") == "GB"
    assert is_supported_country("DE89370400440532013000")


def test_formatting_groups_into_fours():
    assert format_iban("GB82WEST12345698765432") == "GB82 WEST 1234 5698 7654 32"
