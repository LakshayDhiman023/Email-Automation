"""Seed placeholder templates. Replace the body text later with your real ones.

Run:  cd backend && .venv/bin/python scripts/seed_templates.py
Idempotent: skips templates whose name already exists.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # backend/ on path

from dotenv import load_dotenv  # noqa: E402
load_dotenv()

from sqlalchemy import text  # noqa: E402
from app.core.db import SessionLocal  # noqa: E402

SIGNATURE = (
    "Best regards,\n"
    "Ved Prakash Meena\n"
    "+91 8529608145"
)

PLACEHOLDERS = [
    {
        "name": "Template 1 - Official company",
        "kind": "official_company",
        "subject": "Looking for opportunities at {company}",
        "body": (
            "Hi {recruiter_name}, hope you are well.\n\n"
            "I am currently looking for full-time opportunities in SDE / AI Engineering "
            "as a fresher. I was wondering if there are any relevant openings at "
            "{company}. I have nearly 11 months of internship experience and I am "
            "currently an SDE intern at Mercer Mettl.\n\n"
            "PFA my resume for your reference.\n\n" + SIGNATURE
        ),
    },
    {
        "name": "Template 2 - Startup",
        "kind": "startup",
        "subject": "Keen to contribute at {company}",
        "body": (
            "Hi {recruiter_name}, hope you're doing great.\n\n"
            "I'm reaching out because I'd love to contribute at {company}. I'm a fresher "
            "looking for full-time SDE / AI Engineering roles, with ~11 months of "
            "internship experience (currently an SDE intern at Mercer Mettl).\n\n"
            "PFA my resume — would be happy to chat if there's a fit.\n\n" + SIGNATURE
        ),
    },
    {
        "name": "Template 3 - Generic",
        "kind": "generic",
        "subject": "Full-time SDE / AI Engineering opportunities",
        "body": (
            "Hi {recruiter_name}, hope you are well.\n\n"
            "I am currently looking for full-time opportunities in SDE / AI Engineering "
            "as a fresher. I was wondering if there are any relevant openings at "
            "{company}.\n\n"
            "PFA my resume for your reference.\n\n" + SIGNATURE
        ),
    },
]


def main() -> None:
    db = SessionLocal()
    try:
        for t in PLACEHOLDERS:
            exists = db.execute(
                text("SELECT 1 FROM templates WHERE name=:n"), {"n": t["name"]}
            ).first()
            if exists:
                print(f"skip (exists): {t['name']}")
                continue
            db.execute(
                text(
                    "INSERT INTO templates (name, kind, subject, body) "
                    "VALUES (:name, :kind, :subject, :body)"
                ),
                t,
            )
            print(f"inserted: {t['name']}")
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
