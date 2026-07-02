"""Reply listing + labeling endpoints, and a manual poll trigger."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.schemas import ReplyLabel, ReplyOut
from app.services import replies

router = APIRouter(tags=["replies"])


@router.post("/threads/{thread_id}/label", status_code=204)
def label_thread_reply(thread_id: int, payload: ReplyLabel,
                       db: Session = Depends(get_db)):
    """User labels a detected reply: positive | negative | out_of_office.
    out_of_office requires payload.return_date."""
    try:
        replies.label_reply(db, thread_id, payload.label, payload.return_date)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/replies", response_model=list[ReplyOut])
def list_replies(thread_id: int | None = None, limit: int = Query(default=200, ge=1, le=1000),
                 db: Session = Depends(get_db)):
    """Detected replies, newest first. Internal Gmail ids stay server-side."""
    q = "SELECT id, thread_id, snippet, received_at, label FROM replies"
    params: dict = {"lim": limit}
    if thread_id is not None:
        q += " WHERE thread_id=:tid"
        params["tid"] = thread_id
    q += " ORDER BY received_at DESC, id DESC LIMIT :lim"
    return [dict(r) for r in db.execute(text(q), params).mappings().all()]


@router.post("/replies/poll")
def trigger_poll(db: Session = Depends(get_db)):
    """Manually run a reply poll now (the scheduler also runs this every 15 min)."""
    n = replies.poll_replies()
    return {"new_replies": n}
