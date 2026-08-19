"""Retrying an operation against a flaky downstream.

Only idempotent operations may be retried. Retrying a capture because the response timed out is how a
customer is charged twice, so the caller states the property explicitly rather than the helper assuming
it.
"""
from __future__ import annotations

import time
from typing import Callable, TypeVar

T = TypeVar("T")


class RetriesExhausted(RuntimeError):
    def __init__(self, attempts: int, last: BaseException) -> None:
        super().__init__(f"gave up after {attempts} attempts: {last}")
        self.attempts = attempts
        self.last = last


def retry(fn: Callable[[], T], *, attempts: int = 3, base_delay: float = 0.05,
          idempotent: bool = False, on: type[BaseException] = Exception,
          sleep: Callable[[float], None] = time.sleep) -> T:
    """Call `fn`, retrying on `on`. Refuses to retry an operation not declared idempotent."""
    if attempts < 1:
        raise ValueError("attempts must be at least 1")
    if not idempotent and attempts > 1:
        raise ValueError(
            "refusing to retry an operation that is not declared idempotent — "
            "pass idempotent=True once you are sure a repeat cannot double-charge")
    last: BaseException | None = None
    for i in range(attempts):
        try:
            return fn()
        except on as exc:
            last = exc
            if i < attempts - 1:
                sleep(base_delay * (2 ** i))
    raise RetriesExhausted(attempts, last)      # type: ignore[arg-type]
