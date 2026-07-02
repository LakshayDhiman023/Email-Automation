"""Suppression / opt-out list endpoints.

An address here is never emailed (checked at add-contact and again at send time).
Bounces and 'negative' reply labels add to it automatically; the user can also add
addresses manually (e.g. someone replied "please stop").
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services import guards

router = APIRouter(prefix="/suppression", tags=["suppression"])


class SuppressIn(BaseModel):
    email: EmailStr
    note: str | None = None


@router.get("")
def list_suppressions(db: Session = Depends(get_db)):
    rows = db.execute(
        text("SELECT * FROM suppression_list ORDER BY created_at DESC")
    ).mappings().all()
    return [dict(r) for r in rows]


@router.post("", status_code=201)
def add_suppression(payload: SuppressIn, db: Session = Depends(get_db)):
    guards.suppress(db, payload.email, reason="manual", note=payload.note)
    db.commit()
    return {"email": payload.email.lower(), "reason": "manual"}


@router.delete("/{email}", status_code=204)
def remove_suppression(email: str, db: Session = Depends(get_db)):
    res = db.execute(
        text("DELETE FROM suppression_list WHERE email=:e"),
        {"e": email.strip().lower()},
    )
    db.commit()
    if res.rowcount == 0:
        raise HTTPException(404, "not on suppression list")
