"""The application: every route table mounted onto one router."""
from __future__ import annotations

from ledgerline.api.router import Request, Response, Router
from ledgerline.api.routes import accounts, payments, reports


def build_app(repository=None) -> Router:
    app = Router()
    for module in (payments, accounts, reports):
        app._routes.extend(module.router._routes)
    reports.REPOSITORY = repository
    return app


def reset_state() -> None:
    """Clear the process-local stores. The demo harness calls this between scenarios."""
    payments._reset_state()
    accounts._reset_state()


__all__ = ["build_app", "reset_state", "Request", "Response", "Router"]
