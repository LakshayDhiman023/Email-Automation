"""Seed a few neutral example templates so a fresh install isn't empty. Idempotent.

These are generic starting points — edit them (or add your own) in the Templates page.
Any {variable} you write becomes a field on the compose form; {signature} is filled
from the signature you set on the Settings page. Run once after migrations:

    cd backend && .venv/bin/python scripts/seed_templates.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # backend/ on path

from dotenv import load_dotenv  # noqa: E402
load_dotenv()

from sqlalchemy import text  # noqa: E402
from app.core.db import SessionLocal  # noqa: E402

# Per-send fields come from the {variables} in each template; {signature} is pulled
# from your Settings. Edit freely — nothing here is personal to any one user.
TEMPLATES = [
    {
        "name": "Example - Job application",
        "kind": "example",
        "subject": "Application for {role} at {company}",
        "body": (
            "Hi {name},\n\n"
            "I'm reaching out about the {role} role at {company}. I believe my "
            "background is a strong fit and I'd welcome the chance to discuss it.\n\n"
            "Job ID: {job_id}\n"
            "My resume is attached for your reference.\n\n"
            "{signature}"
        ),
    },
    {
        "name": "Example - Referral request",
        "kind": "example",
        "subject": "Referral request for {role} at {company}",
        "body": (
            "Hi {name},\n\n"
            "Hope you're doing well. I'm interested in the {role} opening at "
            "{company} and would be grateful if you could refer me. Happy to share "
            "anything you need from my side.\n\n"
            "Role link: {job_link}\n\n"
            "{signature}"
        ),
    },
    {
        "name": "Example - Sales intro",
        "kind": "example",
        "subject": "Quick idea for {company}",
        "body": (
            "Hi {name},\n\n"
            "I work with teams like {company} on {topic}, and thought there might be "
            "a fit. Would you be open to a short call next week?\n\n"
            "{signature}"
        ),
    },
    {
        "name": "Example - General outreach",
        "kind": "example",
        "subject": "Reaching out from {company}",
        "body": (
            "Hi {name},\n\n"
            "I wanted to connect regarding {topic}. Let me know if this is something "
            "worth exploring together.\n\n"
            "{signature}"
        ),
    },
]


def main() -> None:
    db = SessionLocal()
    try:
        for t in TEMPLATES:
            existing = db.execute(
                text("SELECT id FROM templates WHERE name=:n"), {"n": t["name"]}
            ).first()
            if existing:
                db.execute(
                    text(
                        "UPDATE templates SET kind=:kind, subject=:subject, "
                        "body=:body, is_active=TRUE WHERE name=:name"
                    ),
                    t,
                )
                print(f"updated: {t['name']}")
            else:
                db.execute(
                    text(
                        "INSERT INTO templates (name, kind, subject, body) "
                        "VALUES (:name, :kind, :subject, :body)"
                    ),
                    t,
                )
                print(f"inserted: {t['name']}")

        # deactivate any template not in the current set (old placeholders + renamed
        # rows like "Referral request - Software Developer") so the picker stays clean
        current = [t["name"] for t in TEMPLATES]
        db.execute(
            text("UPDATE templates SET is_active=FALSE WHERE name <> ALL(:keep)"),
            {"keep": current},
        )
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
