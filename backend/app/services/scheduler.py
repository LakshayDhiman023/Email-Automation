"""Background scheduler.

Runs inside the FastAPI process (APScheduler). Two jobs:
  * tick(): every minute, find approved sends whose scheduled_at has passed and
    process them (actual Gmail send is wired in Phase 4 via process_due_sends()).
  * reply_poll(): periodically check tracked threads for inbound replies
    (wired in Phase 5).

On startup, catch_up() rolls any missed (past-due) scheduled sends forward to the
next valid window — covers the host being down during a window.
"""
from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import get_settings

log = logging.getLogger("scheduler")
_settings = get_settings()

_scheduler: BackgroundScheduler | None = None


def tick() -> None:
    """Fire due sends. Phase 4 implements the actual work."""
    try:
        from app.services.outreach import process_due_sends  # lazy: built in Phase 4
    except ImportError:
        return
    process_due_sends()


def reply_poll() -> None:
    """Poll for replies. Phase 5 implements the actual work."""
    try:
        from app.services.replies import poll_replies  # lazy: built in Phase 5
    except ImportError:
        return
    poll_replies()


def catch_up() -> None:
    """Roll any past-due scheduled sends to the next valid window."""
    try:
        from app.services.outreach import reschedule_missed  # lazy: built in Phase 4
    except ImportError:
        return
    n = reschedule_missed()
    if n:
        log.info("catch_up: rescheduled %d missed send(s)", n)


def start() -> None:
    global _scheduler
    if _scheduler is not None:
        return
    _scheduler = BackgroundScheduler(timezone=_settings.timezone)
    _scheduler.add_job(tick, "interval", minutes=1, id="tick", max_instances=1,
                       coalesce=True)
    _scheduler.add_job(reply_poll, "interval", minutes=15, id="reply_poll",
                       max_instances=1, coalesce=True)
    _scheduler.start()
    catch_up()
    log.info("scheduler started (tick=1m, reply_poll=15m)")


def shutdown() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
