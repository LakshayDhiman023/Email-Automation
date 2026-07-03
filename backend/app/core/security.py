"""Lightweight API authentication.

This app can send email from the user's Gmail, so every endpoint that mutates state
or exposes recruiter data must be protected once it's deployed on a public host.

Model: a single shared secret (API_TOKEN). The frontend sends it as `X-API-Token`.
  * If API_TOKEN is unset  -> auth is DISABLED (fine for local dev on localhost).
  * If API_TOKEN is set     -> every guarded request must present the matching token,
                               else 401. Health checks stay open (cron-ping needs them).

A single shared token is deliberately simple: this is a single-user personal tool, not
a multi-tenant service. It closes the "anyone on the internet can send mail as me" hole
without the weight of full user accounts.

Hardening (OWASP API2 / A07): failed attempts are logged and throttled per client IP
(10 failures / 5 min -> 429), so the shared token can't be brute-forced for free. The
throttle is in-process — sufficient for a single-instance personal deployment.
"""
from __future__ import annotations

import hmac
import logging
import time
from collections import defaultdict, deque

from fastapi import Header, HTTPException, Request, status

from app.core.config import get_settings

log = logging.getLogger("security")
_settings = get_settings()

_MAX_FAILURES = 10          # failed attempts allowed per IP...
_WINDOW_SECONDS = 300       # ...within this sliding window
_failures: dict[str, deque[float]] = defaultdict(deque)


def _client_ip(request: Request | None) -> str:
    if request is None or request.client is None:
        return "unknown"
    return request.client.host


class SlidingWindowCounter:
    """Per-key sliding-window event counter (in-process; fine for one instance).
    Shared shape used by both the auth-failure throttle below and the general
    per-IP request-rate limiter in main.py, so the two don't duplicate logic."""

    def __init__(self, max_events: int, window_seconds: float):
        self.max_events = max_events
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def hit(self, key: str) -> bool:
        """Record one event for `key`; return True if it's now over the limit."""
        now = time.monotonic()
        q = self._events[key]
        q.append(now)
        while q and now - q[0] > self.window_seconds:
            q.popleft()
        if not q:
            self._events.pop(key, None)  # keep the map from growing unbounded
        return len(q) > self.max_events


def _too_many_failures(ip: str) -> bool:
    now = time.monotonic()
    q = _failures[ip]
    while q and now - q[0] > _WINDOW_SECONDS:
        q.popleft()
    if not q:
        _failures.pop(ip, None)  # keep the map from growing unbounded
        return False
    return len(q) >= _MAX_FAILURES


def verify_shared_token(request: Request | None, presented: str | None,
                        expected: str, *, header_name: str) -> None:
    """Constant-time shared-token check with per-IP failure throttling + logging.
    Raises 429 when an IP keeps guessing, 401 on a bad/missing token."""
    ip = _client_ip(request)
    if _too_many_failures(ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="too many failed authentication attempts; try again later",
        )
    if presented and hmac.compare_digest(presented, expected):
        return
    _failures[ip].append(time.monotonic())
    log.warning("auth failure on %s from %s (%d recent)",
                header_name, ip, len(_failures[ip]))
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"missing or invalid {header_name}",
        headers={"WWW-Authenticate": header_name},
    )


def require_api_token(request: Request,
                      x_api_token: str | None = Header(default=None)) -> None:
    """FastAPI dependency guarding a router. No-op if no token is configured."""
    expected = _settings.api_token
    if not expected:
        return  # auth disabled (local dev)
    verify_shared_token(request, x_api_token, expected, header_name="X-API-Token")
