"""Reply detection (presence only) + manual labeling. Detecting a reply pauses
follow-ups; sentiment is labeled by the user via label_reply()."""
from __future__ import annotations

import logging
from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.services import gmail, scheduling

log = logging.getLogger("replies")
_settings = get_settings()

# still worth polling; OOO stays in so an early return before the return date surfaces
_POLLABLE = ("active", "replied_unlabeled", "ooo")


def poll_replies() -> int:
    """Scan pollable threads; record new replies, pause follow-ups, handle bounces."""
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
                analysis = gmail.analyze_thread(
                    t["gmail_thread_id"], exclude_sender=_settings.gmail_sender
                )
            except Exception as e:  # noqa: BLE001 — one bad thread shouldn't stop the rest
                log.error("poll thread=%s failed: %s", t["id"], e)
                continue

            found = analysis["replies"]

            # bounce: delivery failed. Halt everything and suppress the address so we
            # never waste sends / reputation on a dead inbox again.
            if analysis["bounced"] and t["status"] in ("active", "ooo"):
                _handle_bounce(db, t["id"])
                continue

            new_here = 0
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
                    new_here += 1

            # a NEWLY seen inbound message pauses follow-ups and routes to review:
            #   'active' -> replied_unlabeled; 'ooo' -> replied_unlabeled (back early).
            # 'replied_unlabeled' already needs review; nothing to change.
            if t["status"] == "active" and new_here:
                db.execute(
                    text(
                        "UPDATE threads SET status='replied_unlabeled', updated_at=now() "
                        "WHERE id=:tid"
                    ),
                    {"tid": t["id"]},
                )
                _cancel_pending_followups(db, t["id"])
            elif t["status"] == "ooo" and new_here:
                db.execute(
                    text(
                        "UPDATE threads SET status='replied_unlabeled', "
                        "ooo_return_date=NULL, updated_at=now() WHERE id=:tid"
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


def _handle_bounce(db: Session, thread_id: int) -> None:
    """A delivery-failure was detected on the thread: mark it bounced, cancel any
    unsent mail, and suppress the recruiter's address so we never re-contact it."""
    from app.services import guards

    row = db.execute(
        text("SELECT r.email FROM threads t JOIN recruiters r ON r.id=t.recruiter_id "
             "WHERE t.id=:tid"),
        {"tid": thread_id},
    ).first()
    db.execute(
        text("UPDATE sends SET status='cancelled' WHERE thread_id=:tid "
             "AND status IN ('pending_approval','approved')"),
        {"tid": thread_id},
    )
    db.execute(
        text("UPDATE threads SET status='bounced', updated_at=now() WHERE id=:tid"),
        {"tid": thread_id},
    )
    if row:
        guards.suppress(db, row[0], reason="bounced",
                       note=f"auto-suppressed on bounce (thread {thread_id})")
    log.warning("thread=%s bounced -> suppressed", thread_id)


def label_reply(db: Session, thread_id: int, label: str,
                return_date: date | None = None) -> None:
    """Apply the user's sentiment label to a thread's latest reply and route it:
      positive       -> replied_positive (Attention; follow-ups stay off)
      negative       -> replied_negative (Dead; follow-ups off)
      out_of_office  -> ooo; follow-up is RE-SCHEDULED to the recruiter's return
                        date (requires return_date). Unlike positive/negative,
                        OOO does not halt the conversation.
    """
    latest = db.execute(
        text("SELECT id FROM replies WHERE thread_id=:tid ORDER BY id DESC LIMIT 1"),
        {"tid": thread_id},
    ).first()
    if not latest:
        raise ValueError(f"no reply found for thread {thread_id}")

    if label == "positive":
        status = "replied_positive"
    elif label == "negative":
        status = "replied_negative"
    elif label == "out_of_office":
        if return_date is None:
            raise ValueError("out_of_office requires a return_date")
        if return_date < scheduling.now_ist().date():
            raise ValueError("return_date must not be in the past")
        status = "ooo"
    else:
        raise ValueError(f"invalid label: {label}")

    db.execute(
        text("UPDATE replies SET label=:label WHERE id=:id"),
        {"label": label, "id": latest[0]},
    )
    db.execute(
        text("UPDATE threads SET status=:s, ooo_return_date=:rd, updated_at=now() "
             "WHERE id=:tid"),
        {"s": status, "rd": return_date if label == "out_of_office" else None,
         "tid": thread_id},
    )

    if label == "out_of_office":
        # OOO does not halt: re-open the (previously cancelled-on-reply) follow-up
        # path and schedule a fresh follow-up for the recruiter's return date.
        from app.services.followups import create_followup

        due = scheduling.followup_time_from(return_date)
        create_followup(db, thread_id, due)
    elif label == "negative":
        # dead lead: suppress so we never re-contact them (and cancel any queued mail)
        from app.services import guards

        db.execute(
            text("UPDATE sends SET status='cancelled' WHERE thread_id=:tid "
                 "AND status IN ('pending_approval','approved')"),
            {"tid": thread_id},
        )
        row = db.execute(
            text("SELECT r.email FROM threads t JOIN recruiters r ON r.id=t.recruiter_id "
                 "WHERE t.id=:tid"),
            {"tid": thread_id},
        ).first()
        if row:
            guards.suppress(db, row[0], reason="negative",
                           note=f"auto-suppressed on negative label (thread {thread_id})")

    db.commit()
