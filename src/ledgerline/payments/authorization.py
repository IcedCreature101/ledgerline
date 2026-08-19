"""Card authorizations — the hold placed on a customer's funds before anything is captured."""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from ledgerline.core.money import Money

_seq = itertools.count(1)

AUTH_VALIDITY = timedelta(days=7)


class AuthorizationError(ValueError):
    """The authorization cannot be used the way the caller is trying to use it."""


@dataclass
class Authorization:
    merchant_id: str
    amount: Money                      # the amount held
    auth_id: str = field(default_factory=lambda: f"auth_{next(_seq):06d}")
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    captured: list = field(default_factory=list)     # Money, one per capture
    voided: bool = False

    @property
    def currency(self) -> str:
        return self.amount.currency

    def captured_total(self) -> Money:
        out = Money.zero(self.currency)
        for c in self.captured:
            out = out + c
        return out

    def remaining(self) -> Money:
        return self.amount - self.captured_total()

    def is_expired(self, now: datetime | None = None) -> bool:
        now = now or datetime.now(timezone.utc)
        return now > self.created_at + AUTH_VALIDITY

    def is_open(self, now: datetime | None = None) -> bool:
        return not self.voided and not self.is_expired(now) and not self.remaining().is_zero()


def authorize(merchant_id: str, amount: Money) -> Authorization:
    if amount.is_negative() or amount.is_zero():
        raise AuthorizationError("an authorization must be for a positive amount")
    return Authorization(merchant_id=merchant_id, amount=amount)
