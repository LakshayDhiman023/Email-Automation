"""Data export + richer metrics.

/export/outreach.csv — one row per send, joined with recruiter + thread, so the
                       whole pipeline can be pulled into a spreadsheet or backed up.
/metrics             — funnel + deliverability summary beyond the dashboard badges.
"""
import csv
import io

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import get_db
from app.core.security import verify_shared_token

router = APIRouter(tags=["export"])
_settings = get_settings()


@router.get("/export/outreach.csv")
def export_outreach(request: Request,
                    x_export_token: str | None = Header(default=None),
                    db: Session = Depends(get_db)):
    # Fail-closed gate for the CSV dump (contains every contact email + body).
    # Header ONLY — a token in the query string would leak into server/proxy logs
    # and browser history (OWASP A09/A02). The frontend downloads via fetch+blob.
    if not _settings.export_token:
        raise HTTPException(403, "CSV export is disabled; set EXPORT_TOKEN to enable it.")
    verify_shared_token(request, x_export_token, _settings.export_token,
                        header_name="X-Export-Token")
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
