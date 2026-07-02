"""Data export + richer metrics.

/export/outreach.csv — one row per send, joined with recruiter + thread, so the
                       whole pipeline can be pulled into a spreadsheet or backed up.
/metrics             — funnel + deliverability summary beyond the dashboard badges.
"""
import csv
import hmac
import io

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db

router = APIRouter(tags=["export"])
_settings = get_settings()


def _check_export_token(token: str | None) -> None:
    """Fail-closed gate for the CSV dump (contains every recruiter email + body).
    Disabled unless EXPORT_TOKEN is set; compared in constant time."""
    configured = _settings.export_token
    if not configured:
        raise HTTPException(403, "CSV export is disabled; set EXPORT_TOKEN to enable it.")
    if not token or not hmac.compare_digest(token, configured):
        raise HTTPException(403, "invalid or missing export token")


@router.get("/export/outreach.csv")
def export_outreach(token: str | None = Query(default=None),
                    x_export_token: str | None = Header(default=None),
                    db: Session = Depends(get_db)):
    # prefer the header (kept out of logs/history); fall back to query for <a> downloads
    _check_export_token(x_export_token or token)
    rows = db.execute(
        text(
            """
            SELECT r.name AS recruiter, r.company, r.email,
                   t.status AS thread_status, t.ooo_return_date,
                   s.type, s.subject, s.status AS send_status,
                   s.scheduled_at, s.sent_at, s.attempts, s.error
            FROM sends s
            JOIN threads t ON t.id = s.thread_id
            JOIN recruiters r ON r.id = t.recruiter_id
            ORDER BY s.created_at
            """
        )
    ).mappings().all()

    buf = io.StringIO()
    fields = ["recruiter", "company", "email", "thread_status",
              "ooo_return_date", "type", "subject", "send_status", "scheduled_at",
              "sent_at", "attempts", "error"]
    writer = csv.DictWriter(buf, fieldnames=fields)
    writer.writeheader()
    for r in rows:
        writer.writerow({k: r.get(k) for k in fields})
    buf.seek(0)

    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=outreach.csv"},
    )


@router.get("/metrics")
def metrics(db: Session = Depends(get_db)) -> dict:
    """Funnel + deliverability health, computed on the fly.

    Rates use matching units: recipients (threads) over recipients contacted, so a
    thread with an initial + follow-up isn't double-counted in the denominator.
    """
    sends_row = db.execute(
        text(
            "SELECT count(*) FILTER (WHERE status='sent') AS sent_total, "
            "count(*) FILTER (WHERE status='sent' AND sent_at > now() - interval '24 hours') AS sent_24h, "
            "count(DISTINCT thread_id) FILTER (WHERE status='sent') AS threads_mailed "
            "FROM sends"
        )
    ).mappings().one()
    threads_row = db.execute(
        text(
            "SELECT count(*) FILTER (WHERE status='bounced') AS bounced, "
            "count(*) FILTER (WHERE status IN ('replied_unlabeled','replied_positive',"
            "'replied_negative','ooo')) AS replied "
            "FROM threads"
        )
    ).mappings().one()
    suppressed = db.execute(text("SELECT count(*) FROM suppression_list")).scalar_one()

    def pct(n: int, d: int) -> float:
        return round(n / d * 100, 1) if d else 0.0

    # recipients actually mailed = distinct threads with a sent send (bounces arrive
    # after Gmail accepts, so bounced threads are already in this set)
    recipients = sends_row["threads_mailed"]
    bounce_rate = pct(threads_row["bounced"], recipients)
    return {
        "sent_total": sends_row["sent_total"],
        "sent_last_24h": sends_row["sent_24h"],
        "reply_rate": pct(threads_row["replied"], recipients),
        "bounce_rate": bounce_rate,
        "bounce_warning": bounce_rate >= 2.0,
        "suppressed_total": suppressed,
    }
