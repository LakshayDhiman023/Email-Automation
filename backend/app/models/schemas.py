"""Pydantic request/response schemas."""
from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field, computed_field

from app.services.outreach import extract_variables


# ---- Templates ----
class TemplateCreate(BaseModel):
    name: str
    kind: str = "generic"  # official_company | startup | generic
    subject: str
    body: str  # supports any {variable}, e.g. {recruiter_name} {company} {role}


class TemplateOut(BaseModel):
    id: int
    name: str
    kind: str
    subject: str
    body: str
    is_active: bool
    created_at: datetime

    @computed_field
    @property
    def variables(self) -> list[str]:
        """The {placeholders} this template uses, for the Add-contact form to render."""
        return extract_variables(self.subject, self.body)


# ---- Contacts / outreach ----
class ContactCreate(BaseModel):
    name: str = ""  # optional — some templates address "Hiring Manager"
    company: str
    email: EmailStr
    template_id: int
    # per-application fills for the template's extra {placeholders} (role, hr_name, …).
    # recruiter_name/company come from name/company and need not be repeated here.
    variables: dict[str, str] = Field(default_factory=dict)
    # override the per-contact cooldown for a deliberate re-contact (does NOT override
    # the suppression list — that's a hard stop).
    force: bool = False


class SendEdit(BaseModel):
    subject: str | None = None
    body: str | None = None


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
    attempts: int = 0                     # retry count (Phase 8 audit)
    gmail_message_id: str | None = None   # delivered Gmail Message-Id


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


# ---- Reply labeling ----
class ReplyLabel(BaseModel):
    label: str = Field(pattern="^(positive|negative|out_of_office)$")
    # required only when label == "out_of_office": the recruiter's return date,
    # to which the paused follow-up is rescheduled.
    return_date: date | None = None
