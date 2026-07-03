"""Read-only view of the audit trail — who did what, when, from where."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db import get_db

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
def list_audit_log(limit: int = Query(default=200, ge=1, le=2000),
                   db: Session = Depends(get_db)):
    rows = db.execute(
        text(
            "SELECT id, action, entity, entity_id, client_ip, request_id, detail, created_at "
            "FROM audit_log ORDER BY created_at DESC, id DESC LIMIT :lim"
        ),
        {"lim": limit},
    ).mappings().all()
    return [dict(r) for r in rows]
