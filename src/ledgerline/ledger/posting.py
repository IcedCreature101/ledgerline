"""Posting journal entries into accounts, and the running balances that result."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from ledgerline.core.money import Money
from ledgerline.ledger.entries import JournalEntry


@dataclass
class Ledger:
    currency: str = "USD"
    entries: list[JournalEntry] = field(default_factory=list)
    _balances: dict = field(default_factory=lambda: defaultdict(int))

    def post(self, entry: JournalEntry) -> JournalEntry:
        entry.validate()
        for line in entry.lines:
            self._balances[line.account] += line.amount.minor
        self.entries.append(entry)
        return entry

    def balance(self, account: str) -> Money:
        return Money(self._balances.get(account, 0), self.currency)

    def accounts(self) -> list[str]:
        return sorted(self._balances)

    def trial_balance(self) -> Money:
        """Every account summed. A healthy ledger totals zero — money is always somewhere."""
        return Money(sum(self._balances.values()), self.currency)

    def is_healthy(self) -> bool:
        return self.trial_balance().is_zero()
