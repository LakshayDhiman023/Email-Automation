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

from fastapi import APIRouter, Depends

from app.core.security import require_api_token
from app.services import followups, outreach, replies

# Same guard (and failed-attempt throttle) as the rest of the API — no-op locally,
# fail-closed once API_TOKEN is set.
router = APIRouter(prefix="/tasks", tags=["tasks"],
                   dependencies=[Depends(require_api_token)])


@router.post("/run")
def run_due_work(kind: str = "all"):
    """Run due background work now. `kind` = all | sends | replies | followups.

    Designed to be called on a schedule by an external cron (cron-job.org) so the
    system works even when the host's in-process scheduler was asleep.
    """
    ran = {}
    if kind in ("all", "sends"):
        outreach.process_due_sends()
        ran["sends"] = "ok"
    if kind in ("all", "replies"):
        ran["new_replies"] = replies.poll_replies()
    if kind in ("all", "followups"):
        ran["followups_queued"] = followups.generate_due_followups()
    return {"ran": ran}
