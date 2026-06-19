"""Outreach core: add contact, render template, schedule, approve, send.

Implements the hooks the scheduler calls:
  * process_due_sends()  — send approved emails whose scheduled_at has passed
  * reschedule_missed()  — roll past-due sends to the next valid window (startup catch-up)
"""
from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.services import gmail, scheduling

log = logging.getLogger("outreach")
_settings = get_settings()


def render(template_subject: str, template_body: str, *, recruiter_name: str,
           company: str) -> tuple[str, str]:
    """Fill {recruiter_name} / {company} placeholders. Unknown placeholders are
    left intact rather than raising, so partial templates don't break a send."""
    mapping = {"recruiter_name": recruiter_name, "company": company}

    def safe_format(s: str) -> str:
        for k, v in mapping.items():
            s = s.replace("{" + k + "}", v)
        return s

    return safe_format(template_subject), safe_format(template_body)


def add_contact(db: Session, *, name: str, company: str, email: str,
                template_id: int) -> dict:
    """Create recruiter + thread + an initial pending-approval send with a
    computed schedule time. Returns the created send row as a dict."""
    tmpl = db.execute(
        text("SELECT subject, body FROM templates WHERE id=:id AND is_active"),
        {"id": template_id},
    ).mappings().first()
    if not tmpl:
        raise ValueError(f"template {template_id} not found / inactive")

    # upsert recruiter by unique email
    recruiter_id = db.execute(
        text(
            """
            INSERT INTO recruiters (name, company, email)
            VALUES (:name, :company, :email)
            ON CONFLICT (email) DO UPDATE SET name=EXCLUDED.name,
                                              company=EXCLUDED.company
            RETURNING id
            """
        ),
        {"name": name, "company": company, "email": email},
    ).scalar_one()

    thread_id = db.execute(
        text(
            """
            INSERT INTO threads (recruiter_id, template_id, status)
            VALUES (:rid, :tid, 'active') RETURNING id
            """
        ),
        {"rid": recruiter_id, "tid": template_id},
    ).scalar_one()

    subject, body = render(tmpl["subject"], tmpl["body"],
                           recruiter_name=name, company=company)
    scheduled_at = scheduling.compute_send_time()

    send = db.execute(
        text(
            """
            INSERT INTO sends (thread_id, type, subject, body, scheduled_at, status)
            VALUES (:tid, 'initial', :subject, :body, :sched, 'pending_approval')
            RETURNING id, thread_id, type, subject, body, scheduled_at, sent_at,
                      status, error
            """
        ),
        {"tid": thread_id, "subject": subject, "body": body, "sched": scheduled_at},
    ).mappings().first()
    db.commit()
    return dict(send)


def approve_send(db: Session, send_id: int) -> None:
    """Flip a pending send to approved so the scheduler will dispatch it."""
    res = db.execute(
        text(
            """
            UPDATE sends SET status='approved'
            WHERE id=:id AND status='pending_approval'
            """
        ),
        {"id": send_id},
    )
    if res.rowcount == 0:
        raise ValueError(f"send {send_id} not found or not pending_approval")
    db.commit()


def cancel_send(db: Session, send_id: int) -> None:
    db.execute(
        text("UPDATE sends SET status='cancelled' WHERE id=:id AND status IN "
             "('pending_approval','approved')"),
        {"id": send_id},
    )
    db.commit()


def reschedule_missed() -> int:
    """Roll approved sends whose scheduled_at is already past to the next valid
    window. Returns count rescheduled. Called at startup (catch-up)."""
    db = SessionLocal()
    try:
        rows = db.execute(
            text(
                "SELECT id, scheduled_at FROM sends "
                "WHERE status='approved' AND scheduled_at < now()"
            )
        ).mappings().all()
        for r in rows:
            new_time = scheduling.reschedule_if_past(r["scheduled_at"])
            db.execute(
                text("UPDATE sends SET scheduled_at=:t WHERE id=:id"),
                {"t": new_time, "id": r["id"]},
            )
        db.commit()
        return len(rows)
    finally:
        db.close()


def process_due_sends() -> None:
    """Send every approved email whose scheduled_at has passed. Called each tick."""
    db = SessionLocal()
    try:
        due = db.execute(
            text(
                """
                SELECT s.id, s.thread_id, s.subject, s.body, r.email,
                       t.gmail_thread_id
                FROM sends s
                JOIN threads t ON t.id = s.thread_id
                JOIN recruiters r ON r.id = t.recruiter_id
                WHERE s.status='approved' AND s.scheduled_at <= now()
                """
            )
        ).mappings().all()

        for row in due:
            try:
                resp = gmail.send_email(
                    to=row["email"],
                    subject=row["subject"],
                    body=row["body"],
                    attachment_path=_settings.resume_path,
                    thread_id=row["gmail_thread_id"],
                )
                db.execute(
                    text(
                        "UPDATE sends SET status='sent', sent_at=now(), error=NULL "
                        "WHERE id=:id"
                    ),
                    {"id": row["id"]},
                )
                # record gmail thread id on first send so we can poll for replies
                if not row["gmail_thread_id"]:
                    db.execute(
                        text("UPDATE threads SET gmail_thread_id=:gt, updated_at=now() "
                             "WHERE id=:tid"),
                        {"gt": resp.get("threadId"), "tid": row["thread_id"]},
                    )
                db.commit()
                log.info("sent send_id=%s to %s", row["id"], row["email"])
            except Exception as e:  # noqa: BLE001 — record and move on
                db.rollback()
                db.execute(
                    text("UPDATE sends SET status='failed', error=:err WHERE id=:id"),
                    {"err": str(e)[:500], "id": row["id"]},
                )
                db.commit()
                log.error("send_id=%s failed: %s", row["id"], e)
    finally:
        db.close()
