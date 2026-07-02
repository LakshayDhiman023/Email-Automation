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
"""
from __future__ import annotations

import hmac

from fastapi import Header, HTTPException, status

from app.core.config import get_settings

_settings = get_settings()


def require_api_token(x_api_token: str | None = Header(default=None)) -> None:
    """FastAPI dependency guarding a router. No-op if no token is configured."""
    expected = _settings.api_token
    if not expected:
        return  # auth disabled (local dev)
    if not x_api_token or not hmac.compare_digest(x_api_token, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing or invalid API token",
            headers={"WWW-Authenticate": "X-API-Token"},
        )
