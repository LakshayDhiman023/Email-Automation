"""Template CRUD endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.schemas import TemplateCreate, TemplateOut

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("", response_model=list[TemplateOut])
def list_templates(db: Session = Depends(get_db)):
    rows = db.execute(
        text("SELECT * FROM templates WHERE is_active ORDER BY id")
    ).mappings().all()
    return [dict(r) for r in rows]


@router.post("", response_model=TemplateOut, status_code=201)
def create_template(payload: TemplateCreate, db: Session = Depends(get_db)):
    row = db.execute(
        text(
            """
            INSERT INTO templates (name, kind, subject, body)
            VALUES (:name, :kind, :subject, :body)
            RETURNING *
            """
        ),
        payload.model_dump(),
    ).mappings().first()
    db.commit()
    return dict(row)


@router.put("/{template_id}", response_model=TemplateOut)
def update_template(template_id: int, payload: TemplateCreate,
                    db: Session = Depends(get_db)):
    row = db.execute(
        text(
            """
            UPDATE templates SET name=:name, kind=:kind, subject=:subject, body=:body
            WHERE id=:id RETURNING *
            """
        ),
        {**payload.model_dump(), "id": template_id},
    ).mappings().first()
    if not row:
        raise HTTPException(404, "template not found")
    db.commit()
    return dict(row)
