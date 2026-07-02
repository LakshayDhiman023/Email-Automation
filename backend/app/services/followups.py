"""Follow-up engine.

Two ways a follow-up gets created:
  * OOO: when a reply is labeled out-of-office, scheduled on the recruiter's return
    date (created by replies.label_reply -> create_followup).
  * No-reply: generate_due_followups() (run by the scheduler) finds threads still
    'active' whose last send was >= N working days ago with no reply, and queues a
    pending-approval follow-up.

The follow-up subject/body live in ONE place (build_followup_content) so the real
bump text can be dropped in later without touching scheduling/DB logic.
"""
from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.services import scheduling

log = logging.getLogger("followups")
_settings = get_settings()

# "Re: " threads it onto the original conversation in the recipient's client.
_FOLLOWUP_BODY = (
    "Hi {recruiter_name},\n\n"
    "I am writing you this mail to follow up on my application. Pl do let me know "
    "if you have any update on the same. Appreciate your response.\n\n"
    "Best regards,\n"
    "Ved Prakash Meena\n"
    "+91 8529608145"
)


def build_followup_content(original_subject: str) -> tuple[str, str]:
    """Return (subject, body) for a follow-up given the thread's original subject."""
    subject = original_subject
    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"
    return subject, _FOLLOWUP_BODY


def create_followup(db: Session, thread_id: int, scheduled_at: datetime) -> None:
    """Insert a pending-approval follow-up send for a thread at the given time.
    Skips if an unsent follow-up already exists for the thread (no duplicates)."""
    # never create a second follow-up: count sent ones too, matching the no-reply sweep
    existing = db.execute(
        text(
            "SELECT 1 FROM sends WHERE thread_id=:tid AND type='followup' "
            "AND status IN ('pending_approval','approved','sent')"
        ),
        {"tid": thread_id},
    ).first()
    if existing:
        return

    row = db.execute(
        text(
            """
            SELECT s.subject AS subject, r.name AS recruiter_name, r.company AS company
            FROM threads t
            JOIN recruiters r ON r.id = t.recruiter_id
            LEFT JOIN sends s ON s.thread_id = t.id AND s.type='initial'
            WHERE t.id = :tid
            ORDER BY s.id ASC LIMIT 1
            """
        ),
        {"tid": thread_id},
    ).mappings().first()
    subject, body = build_followup_content(row["subject"] or "Following up")
    from app.services.outreach import render

    _, body = render(subject, body,
                     {"recruiter_name": row["recruiter_name"], "company": row["company"]})

    db.execute(
        text(
            """
            INSERT INTO sends (thread_id, type, subject, body, scheduled_at, status)
            VALUES (:tid, 'followup', :subject, :body, :sched, 'pending_approval')
            """
        ),
        {"tid": thread_id, "subject": subject, "body": body, "sched": scheduled_at},
    )


def generate_due_followups() -> int:
    """Queue follow-ups for active threads whose initial send went out >= N working
    days ago and that have had no reply. Returns count created. Run by scheduler."""
    db = SessionLocal()
    try:
        # threads still active (no reply detected), with a sent initial, and no
        # existing pending/approved follow-up
        candidates = db.execute(
            text(
                """
                SELECT t.id AS thread_id, s.sent_at
                FROM threads t
                JOIN sends s ON s.thread_id = t.id
                              AND s.type = 'initial' AND s.status = 'sent'
                WHERE t.status = 'active'
                  AND NOT EXISTS (
                        SELECT 1 FROM sends f
                        WHERE f.thread_id = t.id AND f.type = 'followup'
                          AND f.status IN ('pending_approval','approved','sent')
                  )
                """
            )
        ).mappings().all()

        now = scheduling.now_ist()
        threshold = _settings.followup_after_working_days
        created = 0
        for c in candidates:
            sent_date = c["sent_at"].astimezone(scheduling._TZ).date()  # noqa: SLF001
            elapsed = scheduling.working_days_between(sent_date, now.date())
            if elapsed >= threshold:
                # schedule the follow-up in the next valid window from now
                due_time = scheduling.compute_send_time(now)
                create_followup(db, c["thread_id"], due_time)
                created += 1
        db.commit()
        if created:
            log.info("generate_due_followups: queued %d follow-up(s)", created)
        return created
    finally:
        db.close()
