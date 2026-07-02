"""Reply listing + labeling endpoints, and a manual poll trigger."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.schemas import ReplyLabel
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


@router.get("/replies")
def list_replies(thread_id: int | None = None, db: Session = Depends(get_db)):
    q = "SELECT * FROM replies"
    params = {}
    if thread_id is not None:
        q += " WHERE thread_id=:tid"
        params["tid"] = thread_id
    q += " ORDER BY received_at DESC, id DESC"
    return [dict(r) for r in db.execute(text(q), params).mappings().all()]


@router.post("/replies/poll")
def trigger_poll(db: Session = Depends(get_db)):
    """Manually run a reply poll now (the scheduler also runs this every 15 min)."""
    n = replies.poll_replies()
    return {"new_replies": n}
