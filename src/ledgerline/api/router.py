"""A minimal request router.

Deliberately small: routes are (method, path) pairs mapped to handlers, path parameters are named in
angle brackets, and a handler returns (status, body). There is no framework here because the interesting
behaviour — validation, idempotency, error mapping — is ours, and a framework would only hide it.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable

from ledgerline.api.errors import to_response

_PARAM = re.compile(r"<([a-z_]+)>")


@dataclass(frozen=True)
class Request:
    method: str
    path: str
    body: dict = field(default_factory=dict)
    headers: dict = field(default_factory=dict)
    query: dict = field(default_factory=dict)

    def header(self, name: str, default: str = "") -> str:
        """Case-insensitive, the way HTTP headers actually behave."""
        lowered = {k.lower(): v for k, v in self.headers.items()}
        return lowered.get(name.lower(), default)


@dataclass(frozen=True)
class Response:
    status: int
    body: Any


class Router:
    def __init__(self) -> None:
        self._routes: list[tuple[str, re.Pattern, Callable]] = []

    def add(self, method: str, path: str, handler: Callable) -> None:
        pattern = "^" + _PARAM.sub(r"(?P<\1>[^/]+)", path) + "$"
        self._routes.append((method.upper(), re.compile(pattern), handler))

    def route(self, method: str, path: str):
        def decorator(fn: Callable) -> Callable:
            self.add(method, path, fn)
            return fn
        return decorator

    def dispatch(self, request: Request) -> Response:
        for method, pattern, handler in self._routes:
            if method != request.method.upper():
                continue
            m = pattern.match(request.path)
            if not m:
                continue
            try:
                status, body = handler(request, **m.groupdict())
                return Response(status, body)
            except Exception as exc:            # noqa: BLE001 — every error becomes a response
                status, body = to_response(exc)
                return Response(status, body)
        return Response(404, {"error": {"code": "no_route",
                                       "message": f"no route for {request.method} {request.path}"}})
