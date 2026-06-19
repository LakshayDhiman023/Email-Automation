"""Background scheduler.

Runs inside the FastAPI process (APScheduler). Jobs:
  * tick()           every 1m  — send approved emails whose time has passed
  * reply_poll()     every 15m — detect inbound replies, pause follow-ups
  * followup_sweep() every 1h  — queue no-reply follow-ups past the N-day mark

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
    """Send approved emails whose scheduled_at has passed."""
    from app.services.outreach import process_due_sends
    process_due_sends()


def reply_poll() -> None:
    """Poll tracked threads for inbound replies."""
    from app.services.replies import poll_replies
    poll_replies()


def followup_sweep() -> None:
    """Queue no-reply follow-ups for threads past the N-working-day mark."""
    from app.services.followups import generate_due_followups
    generate_due_followups()


def catch_up() -> None:
    """Roll any past-due scheduled sends to the next valid window."""
    from app.services.outreach import reschedule_missed
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
    _scheduler.add_job(followup_sweep, "interval", hours=1, id="followup_sweep",
                       max_instances=1, coalesce=True)
    _scheduler.start()
    catch_up()
    log.info("scheduler started (tick=1m, reply_poll=15m, followup_sweep=1h)")


def shutdown() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
