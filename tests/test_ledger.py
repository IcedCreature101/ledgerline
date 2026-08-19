import pytest

from ledgerline.core.money import CurrencyMismatch, Money
from ledgerline.ledger.entries import JournalEntry, UnbalancedEntry
from ledgerline.ledger.posting import Ledger


def _settlement_entry(major="100.00"):
    amount = Money.from_major(major, "USD")
    return (JournalEntry("stlm-1")
            .add("merchant_payable", -amount, "owed to the merchant")
            .add("cash", amount, "received from the network"))


def test_a_balanced_entry_posts():
    ledger = Ledger()
    ledger.post(_settlement_entry())
    assert ledger.balance("cash") == Money.from_major("100.00", "USD")
    assert ledger.balance("merchant_payable") == Money.from_major("-100.00", "USD")


def test_the_books_total_zero_after_posting():
    ledger = Ledger()
    ledger.post(_settlement_entry())
    ledger.post(_settlement_entry("55.25"))
    assert ledger.is_healthy()


def test_an_unbalanced_entry_is_refused():
    entry = JournalEntry("bad-1").add("cash", Money.from_major("10.00", "USD"))
    with pytest.raises(UnbalancedEntry):
        Ledger().post(entry)


def test_an_empty_entry_is_refused():
    with pytest.raises(UnbalancedEntry):
        Ledger().post(JournalEntry("empty-1"))


def test_a_line_in_the_wrong_currency_is_refused():
    with pytest.raises(CurrencyMismatch):
        JournalEntry("x", currency="USD").add("cash", Money.from_major("1.00", "EUR"))


def test_debits_and_credits_are_reported_separately():
    entry = _settlement_entry()
    assert entry.debits() == Money.from_major("100.00", "USD")
    assert entry.credits() == Money.from_major("100.00", "USD")


def test_accounts_are_listed_in_order():
    ledger = Ledger()
    ledger.post(_settlement_entry())
    assert ledger.accounts() == ["cash", "merchant_payable"]


def test_an_unknown_account_has_a_zero_balance():
    assert Ledger().balance("nothing_here").is_zero()
