"""Reply detection + labeling.

poll_replies() (called every 15 min by the scheduler) checks each active thread's
Gmail conversation for inbound messages from the recruiter. On the first detected
reply it records the reply, PAUSES follow-ups (thread -> replied_unlabeled), so a
follow-up is never sent to someone who already responded.

Sentiment is NOT inferred here — the user labels each reply in the dashboard via
label_reply(): positive | negative | ooo (with a return date for ooo).
"""
from __future__ import annotations

import logging
from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.services import followups, gmail, scheduling

log = logging.getLogger("replies")
_settings = get_settings()

# Thread statuses that still need reply-polling. Once labeled/dead we stop checking.
_POLLABLE = ("active", "replied_unlabeled")


def poll_replies() -> int:
    """Scan pollable threads for new inbound replies. Returns count of new replies
    stored. Pauses follow-ups on first reply per thread."""
    db = SessionLocal()
    try:
        threads = db.execute(
            text(
                """
                SELECT t.id, t.gmail_thread_id, t.status
                FROM threads t
                WHERE t.gmail_thread_id IS NOT NULL
                  AND t.status = ANY(:statuses)
                """
            ),
            {"statuses": list(_POLLABLE)},
        ).mappings().all()

        new_count = 0
        for t in threads:
            try:
                found = gmail.find_replies(
                    t["gmail_thread_id"], exclude_sender=_settings.gmail_sender
                )
            except Exception as e:  # noqa: BLE001 — one bad thread shouldn't stop the rest
                log.error("poll thread=%s failed: %s", t["id"], e)
                continue

            for msg in found:
                inserted = db.execute(
                    text(
                        """
                        INSERT INTO replies (thread_id, gmail_message_id, snippet)
                        VALUES (:tid, :mid, :snip)
                        ON CONFLICT (gmail_message_id) DO NOTHING
                        RETURNING id
                        """
                    ),
                    {"tid": t["id"], "mid": msg["message_id"], "snip": msg["snippet"]},
                ).first()
                if inserted:
                    new_count += 1

            # if this thread has any reply and isn't labeled yet, pause follow-ups
            if found and t["status"] == "active":
                db.execute(
                    text(
                        "UPDATE threads SET status='replied_unlabeled', updated_at=now() "
                        "WHERE id=:tid"
                    ),
                    {"tid": t["id"]},
                )
                _cancel_pending_followups(db, t["id"])

        db.commit()
        if new_count:
            log.info("poll_replies: %d new repl(y/ies) detected", new_count)
        return new_count
    finally:
        db.close()


def _cancel_pending_followups(db: Session, thread_id: int) -> None:
    """Cancel not-yet-sent follow-ups for a thread (a reply arrived)."""
    db.execute(
        text(
            """
            UPDATE sends SET status='cancelled'
            WHERE thread_id=:tid AND type='followup'
              AND status IN ('pending_approval','approved')
            """
        ),
        {"tid": thread_id},
    )


def label_reply(
    db: Session, thread_id: int, label: str, ooo_return_date: date | None = None
) -> None:
    """Apply the user's sentiment label to a thread's latest reply and route the
    thread:
      positive -> replied_positive (Attention)
      negative -> replied_negative (Dead)
      ooo      -> ooo; schedule a follow-up on the return date
    """
    latest = db.execute(
        text("SELECT id FROM replies WHERE thread_id=:tid ORDER BY id DESC LIMIT 1"),
        {"tid": thread_id},
    ).first()
    if not latest:
        raise ValueError(f"no reply found for thread {thread_id}")

    db.execute(
        text("UPDATE replies SET label=:label WHERE id=:id"),
        {"label": label, "id": latest[0]},
    )

    if label == "positive":
        _set_thread_status(db, thread_id, "replied_positive")
    elif label == "negative":
        _set_thread_status(db, thread_id, "replied_negative")
    elif label == "ooo":
        if ooo_return_date is None:
            raise ValueError("ooo label requires ooo_return_date")
        _set_thread_status(db, thread_id, "ooo", ooo_return_date=ooo_return_date)
        _schedule_ooo_followup(db, thread_id, ooo_return_date)
    else:
        raise ValueError(f"invalid label: {label}")

    db.commit()


def _set_thread_status(
    db: Session, thread_id: int, status: str, ooo_return_date: date | None = None
) -> None:
    db.execute(
        text(
            "UPDATE threads SET status=:s, ooo_return_date=:d, updated_at=now() "
            "WHERE id=:tid"
        ),
        {"s": status, "d": ooo_return_date, "tid": thread_id},
    )


def _schedule_ooo_followup(db: Session, thread_id: int, return_date: date) -> None:
    """Create a pending-approval follow-up timed to the recruiter's return date."""
    when = scheduling.followup_time_from(return_date)
    followups.create_followup(db, thread_id, when)
