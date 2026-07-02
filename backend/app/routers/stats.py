"""Dashboard stats / counts for the overview and nav badges."""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db import get_db

router = APIRouter(tags=["stats"])


@router.get("/stats")
def stats(db: Session = Depends(get_db)) -> dict:
    send_counts = dict(
        db.execute(
            text("SELECT status, count(*) FROM sends GROUP BY status")
        ).all()
    )
    thread_counts = dict(
        db.execute(
            text("SELECT status, count(*) FROM threads GROUP BY status")
        ).all()
    )
    sent_total = send_counts.get("sent", 0)
    replied = (
        thread_counts.get("replied_unlabeled", 0)
        + thread_counts.get("replied_positive", 0)
        + thread_counts.get("replied_negative", 0)
        + thread_counts.get("ooo", 0)
    )
    reply_rate = round(replied / sent_total * 100) if sent_total else 0

    return {
        "pending_approval": send_counts.get("pending_approval", 0),
        "scheduled": send_counts.get("approved", 0),
        "sent": sent_total,
        "failed": send_counts.get("failed", 0),
        "needs_review": thread_counts.get("replied_unlabeled", 0),
        "positive": thread_counts.get("replied_positive", 0),
        "negative": thread_counts.get("replied_negative", 0),
        "ooo": thread_counts.get("ooo", 0),
        "active": thread_counts.get("active", 0),
        "reply_rate": reply_rate,
    }
