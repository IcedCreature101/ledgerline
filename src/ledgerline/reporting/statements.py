"""Merchant statements — the monthly document a merchant reconciles their own books against."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ledgerline.core.money import Money
from ledgerline.fees.schedule import calculate_fee, get_schedule
from ledgerline.reporting.periods import Period


@dataclass(frozen=True)
class StatementLine:
    transaction_id: str
    gross: Money
    fee: Money
    net: Money
    settled_on: str


@dataclass(frozen=True)
class Statement:
    merchant_id: str
    period: Period
    lines: tuple[StatementLine, ...]
    currency: str

    def gross(self) -> Money:
        out = Money.zero(self.currency)
        for ln in self.lines:
            out = out + ln.gross
        return out

    def fees(self) -> Money:
        out = Money.zero(self.currency)
        for ln in self.lines:
            out = out + ln.fee
        return out

    def net(self) -> Money:
        return self.gross() - self.fees()

    def as_dict(self) -> dict:
        return {
            "merchant_id": self.merchant_id,
            "period": self.period.label(),
            "transactions": len(self.lines),
            "gross": str(self.gross()),
            "fees": str(self.fees()),
            "net": str(self.net()),
        }


def build_statement(merchant_id: str, period: Period, transactions: list,
                    *, schedule: str = "standard", currency: str = "USD") -> Statement:
    """Assemble a statement from the merchant's settled transactions in `period`."""
    sched = get_schedule(schedule)
    lines = []
    for txn in transactions:
        when = datetime.fromisoformat(txn.created_at)
        if not period.contains(when):
            continue
        fee = calculate_fee(txn.amount, sched)
        lines.append(StatementLine(
            transaction_id=txn.id,
            gross=txn.amount,
            fee=fee,
            net=txn.amount - fee,
            settled_on=(txn.settled_at or "")[:10],
        ))
    return Statement(merchant_id, period, tuple(lines), currency)
