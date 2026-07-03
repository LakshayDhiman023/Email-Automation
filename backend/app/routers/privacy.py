"""GDPR-style data-subject erasure: permanently delete everything we hold about
one contact, on request. Distinct from suppression (which stops future emails
but keeps history) — this removes the history too.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services import audit, guards

router = APIRouter(prefix="/privacy", tags=["privacy"])


@router.delete("/contacts/{email}", status_code=204)
def erase_contact(email: str, db: Session = Depends(get_db)):
    """Permanently delete a contact and everything derived from them: threads,
    sends, replies (all cascade from the recruiters row — see migration 001).
    Also adds them to the suppression list so a re-import can't silently
    re-contact someone who asked to be forgotten."""
    e = email.strip().lower()
    row = db.execute(text("SELECT id FROM recruiters WHERE email=:e"), {"e": e}).first()
    if not row:
        raise HTTPException(404, "no contact with that email")
    recruiter_id = row[0]

    guards.suppress(db, e, reason="erased", note="data erased on request")
    db.execute(text("DELETE FROM recruiters WHERE id=:id"), {"id": recruiter_id})
    audit.record(db, "privacy.erase", entity="recruiter", entity_id=e)
    db.commit()
