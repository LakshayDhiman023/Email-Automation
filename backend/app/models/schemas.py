"""Pydantic request/response schemas."""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field


# ---- Templates ----
class TemplateCreate(BaseModel):
    name: str
    kind: str = "generic"  # official_company | startup | generic
    subject: str
    body: str  # supports {recruiter_name} and {company}


class TemplateOut(BaseModel):
    id: int
    name: str
    kind: str
    subject: str
    body: str
    is_active: bool
    created_at: datetime


# ---- Contacts / outreach ----
class ContactCreate(BaseModel):
    name: str
    company: str
    email: EmailStr
    template_id: int


class SendOut(BaseModel):
    id: int
    thread_id: int
    type: str
    subject: str
    body: str
    scheduled_at: datetime | None
    sent_at: datetime | None
    status: str
    error: str | None


class ThreadOut(BaseModel):
    id: int
    recruiter_id: int
    recruiter_name: str
    company: str
    email: str
    template_id: int
    status: str
    gmail_thread_id: str | None
    ooo_return_date: date | None
    created_at: datetime
    latest_send: SendOut | None = None


# ---- Reply labeling (Phase 5 uses these) ----
class ReplyLabel(BaseModel):
    label: str = Field(pattern="^(positive|negative|ooo)$")
    ooo_return_date: date | None = None  # required when label == "ooo"
