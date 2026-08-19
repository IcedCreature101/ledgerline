"""Double-entry journal entries.

Every movement of money is recorded twice — once as a debit, once as a credit — and a journal entry is
only valid if its debits and credits sum to the same amount. That invariant is the reason a ledger can
be trusted: an entry that does not balance cannot be posted, so the books cannot silently drift.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from datetime import datetime, timezone

from ledgerline.core.money import CurrencyMismatch, Money, total

_seq = itertools.count(1)


class UnbalancedEntry(ValueError):
    """Debits and credits do not agree. Never postable."""


@dataclass(frozen=True)
class Line:
    account: str
    amount: Money            # positive = debit, negative = credit
    memo: str = ""

    def is_debit(self) -> bool:
        return self.amount.minor > 0

    def is_credit(self) -> bool:
        return self.amount.minor < 0


@dataclass
class JournalEntry:
    reference: str
    lines: list[Line] = field(default_factory=list)
    currency: str = "USD"
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    entry_id: int = field(default_factory=lambda: next(_seq))

    def add(self, account: str, amount: Money, memo: str = "") -> "JournalEntry":
        if amount.currency != self.currency:
            raise CurrencyMismatch(
                f"entry {self.reference} is in {self.currency}, line is {amount.currency}")
        self.lines.append(Line(account, amount, memo))
        return self

    def debits(self) -> Money:
        return total([ln.amount for ln in self.lines if ln.is_debit()], self.currency)

    def credits(self) -> Money:
        return total([-ln.amount for ln in self.lines if ln.is_credit()], self.currency)

    def is_balanced(self) -> bool:
        return self.debits().minor == self.credits().minor

    def validate(self) -> None:
        if not self.lines:
            raise UnbalancedEntry(f"entry {self.reference} has no lines")
        if not self.is_balanced():
            raise UnbalancedEntry(
                f"entry {self.reference} does not balance: "
                f"debits {self.debits()} vs credits {self.credits()}")
