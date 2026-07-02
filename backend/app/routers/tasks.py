"""Externally-triggerable background work.

WHY THIS EXISTS: on a free host (Render/Railway free tier) the web process is
SUSPENDED when idle, and the in-process APScheduler is suspended with it — so it can
miss its 1-minute tick and the 9-10 / 2-3 send windows entirely. Relying on APScheduler
alone silently degrades to "sends go out whenever the box happens to be awake".

The fix: let the SAME external cron-ping that keeps the host awake also DRIVE the work.
Point cron-job.org at POST /tasks/run every few minutes; each call runs exactly what
the scheduler would have, guarded by a token. APScheduler stays as the in-process
driver when the host is always-on; this endpoint makes correctness independent of it.

Idempotent + safe: process_due_sends/poll_replies/generate_due_followups all use row
locks / conflict-guards, so overlapping scheduler-and-cron invocations can't double-act.
"""
from __future__ import annotations

import hmac

from fastapi import APIRouter, Header, HTTPException

from app.core.config import get_settings
from app.services import followups, outreach, replies

router = APIRouter(prefix="/tasks", tags=["tasks"])
_settings = get_settings()


def _authorize(token: str | None) -> None:
    """Guard with API_TOKEN if configured (fail-closed once a token is set)."""
    expected = _settings.api_token
    if not expected:
        return
    if not token or not hmac.compare_digest(token, expected):
        raise HTTPException(401, "missing or invalid API token")


@router.post("/run")
def run_due_work(kind: str = "all", x_api_token: str | None = Header(default=None)):
    """Run due background work now. `kind` = all | sends | replies | followups.

    Designed to be called on a schedule by an external cron (cron-job.org) so the
    system works even when the host's in-process scheduler was asleep.
    """
    _authorize(x_api_token)
    ran = {}
    if kind in ("all", "sends"):
        outreach.process_due_sends()
        ran["sends"] = "ok"
    if kind in ("all", "replies"):
        ran["new_replies"] = replies.poll_replies()
    if kind in ("all", "followups"):
        ran["followups_queued"] = followups.generate_due_followups()
    return {"ran": ran}
