"""Seed / update the real templates. Idempotent: upserts by name.

Run:  cd backend && .venv/bin/python scripts/seed_templates.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # backend/ on path

from dotenv import load_dotenv  # noqa: E402
load_dotenv()

from sqlalchemy import text  # noqa: E402
from app.core.db import SessionLocal  # noqa: E402

SIGNATURE = "Best regards,\nVed Prakash Meena\n+91 8529608145"

# Per-application fields you fill in the dashboard: {company}, {recruiter_name},
# {role} (required), and optional {job_id} / {job_link} (their line vanishes if blank).
# Everything else (experience, name, phone, LinkedIn) is constant and stays fixed.
TEMPLATES = [
    {
        "name": "HR outreach - looking for opportunities",
        "kind": "hr_opening",
        "subject": "Looking for {role} Opportunities at {company}",
        "body": (
            "Hi {recruiter_name}, hope you are well.\n\n"
            "I am currently looking for a change ({role}) as a fresher. I was "
            "wondering if there are any relevant openings at {company}. I have nearly "
            "11 months of Internship experience and I am currently a SDE intern at "
            "Mercer Mettl.\n\n"
            "Job ID: {job_id}\n"
            "PFA my resume for your reference.\n\n" + SIGNATURE
        ),
    },
    {
        "name": "Referral request",
        "kind": "referral",
        "subject": "Request for referral for {role} role at {company}",
        "body": (
            "Hi {recruiter_name},\n\n"
            "Hope you are doing well. I wish to apply at {company} for a relevant "
            "opening - {role}, I would be happy if you could refer me for the same. "
            "I can share all the details required from my end.\n\n"
            "Role link: {job_link}\n"
            "PFA my resume attached for your reference. I would be grateful for the "
            "same. Have a nice day ahead.\n\n" + SIGNATURE
        ),
    },
    {
        "name": "Direct inquiry",
        "kind": "inquiry",
        "subject": "Inquiry Regarding {role} Opportunities at {company}",
        "body": (
            "Hi {recruiter_name},\n\n"
            "Hope you are doing well.\n\n"
            "I am currently exploring opportunities for {role} and was wondering if "
            "there are any relevant openings within your team or elsewhere at "
            "{company}.\n\n"
            "Job ID: {job_id}\n"
            "Role link: {job_link}\n"
            "I have nearly 11 months of internship experience and am currently working "
            "as an SDE Intern at Mercer Mettl.\n\n"
            "LinkedIn: https://www.linkedin.com/in/ved-prakash-meena/\n\n"
            "I have attached my resume for your reference. I would appreciate your "
            "support in the same.\n\n"
            "Thank you for your time and consideration.\n\n" + SIGNATURE
        ),
    },
    {
        "name": "Company HR inbox - direct application",
        "kind": "company_hr",
        "subject": "Application for {role} – Ved Prakash Meena",
        "body": (
            "Respected Hiring Manager,\n\n"
            "I hope you are doing well.\n\n"
            "I am interested in applying for the {role} role at {company}. I am "
            "currently an SDE Intern at Mercer Mettl with nearly 11 months of "
            "internship experience.\n\n"
            "Job ID: {job_id}\n"
            "Role link: {job_link}\n"
            "I have attached my resume for your review. Please let me know if any "
            "additional information is required from my end.\n\n"
            "Thank you for your time and consideration.\n\n"
            "Best regards,\n"
            "Ved Prakash Meena\n"
            "+91 8529608145\n"
            "LinkedIn: https://www.linkedin.com/in/ved-prakash-meena/"
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
