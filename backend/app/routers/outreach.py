"""Contact / send / thread endpoints (the dashboard's main surface)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.schemas import ContactCreate, SendOut, ThreadOut
from app.services import outreach

router = APIRouter(tags=["outreach"])


@router.post("/contacts", response_model=SendOut, status_code=201)
def add_contact(payload: ContactCreate, db: Session = Depends(get_db)):
    """Add a recruiter, render their template, schedule a pending-approval send."""
    try:
        send = outreach.add_contact(
            db, name=payload.name, company=payload.company,
            email=payload.email, template_id=payload.template_id,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return send


@router.post("/sends/{send_id}/approve", status_code=204)
def approve(send_id: int, db: Session = Depends(get_db)):
    try:
        outreach.approve_send(db, send_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/sends/{send_id}/cancel", status_code=204)
def cancel(send_id: int, db: Session = Depends(get_db)):
    outreach.cancel_send(db, send_id)


@router.get("/sends", response_model=list[SendOut])
def list_sends(status: str | None = None, db: Session = Depends(get_db)):
    q = "SELECT * FROM sends"
    params = {}
    if status:
        q += " WHERE status=:status"
        params["status"] = status
    q += " ORDER BY scheduled_at NULLS LAST, id DESC"
    rows = db.execute(text(q), params).mappings().all()
    return [dict(r) for r in rows]


@router.get("/threads", response_model=list[ThreadOut])
def list_threads(status: str | None = None, db: Session = Depends(get_db)):
    """Threads joined with recruiter + their latest send (for dashboard sections)."""
    q = """
        SELECT t.id, t.recruiter_id, r.name AS recruiter_name, r.company, r.email,
               t.template_id, t.status, t.gmail_thread_id, t.ooo_return_date,
               t.created_at
        FROM threads t JOIN recruiters r ON r.id = t.recruiter_id
    """
    params = {}
    if status:
        q += " WHERE t.status=:status"
        params["status"] = status
    q += " ORDER BY t.created_at DESC"
    threads = db.execute(text(q), params).mappings().all()

    out = []
    for t in threads:
        latest = db.execute(
            text("SELECT * FROM sends WHERE thread_id=:tid ORDER BY id DESC LIMIT 1"),
            {"tid": t["id"]},
        ).mappings().first()
        d = dict(t)
        d["latest_send"] = dict(latest) if latest else None
        out.append(d)
    return out
