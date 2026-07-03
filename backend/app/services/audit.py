"""Append-only audit trail: who did what, when, from where — one row per
state-changing action. Read-side of "who" is trivial here (single operator per
deployment); the log exists to answer WHICH action, WHEN, and FROM WHICH ip.
"""
from __future__ import annotations

import json
import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.logging import client_ip_ctx, request_id_ctx

log = logging.getLogger("audit")


def record(db: Session, action: str, *, entity: str | None = None,
          entity_id: str | int | None = None, detail: dict | None = None) -> None:
    """Insert one audit row. Call within the same transaction as the action it
    records (does not commit) so the two succeed or fail together. Never store
    email bodies/PII blobs in `detail` — ids and short context only."""
    db.execute(
        text(
            """
            INSERT INTO audit_log (action, entity, entity_id, client_ip, request_id, detail)
            VALUES (:action, :entity, :entity_id, :ip, :rid, :detail)
            """
        ),
        {
            "action": action,
            "entity": entity,
            "entity_id": str(entity_id) if entity_id is not None else None,
            "ip": client_ip_ctx.get(),
            "rid": request_id_ctx.get(),
            "detail": json.dumps(detail) if detail is not None else None,
        },
    )
    log.info("audit: %s", action, extra={"audit_action": action, "audit_entity": entity})
