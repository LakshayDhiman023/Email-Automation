"""Apply database migrations in order, tracking which have run.

Runs every backend/migrations/*.sql (sorted by filename) that hasn't been applied
yet, recording each in a schema_migrations table so re-runs are safe and a fresh
clone can set up its database with one command:

    cd backend && .venv/bin/python scripts/migrate.py

Uses DIRECT_URL if set (Supabase session pooler, needed for DDL), else DATABASE_URL.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # backend/ on path

from dotenv import load_dotenv  # noqa: E402
load_dotenv()

from sqlalchemy import create_engine, text  # noqa: E402

MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations"


def _db_url() -> str:
    url = os.getenv("DIRECT_URL") or os.getenv("DATABASE_URL")
    if not url:
        sys.exit("Set DATABASE_URL (or DIRECT_URL) in your .env first.")
    return url


def main() -> None:
    engine = create_engine(_db_url())
    with engine.begin() as conn:
        conn.execute(
            text(
                "CREATE TABLE IF NOT EXISTS schema_migrations ("
                "  filename TEXT PRIMARY KEY,"
                "  applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
            )
        )
        applied = {
            r[0] for r in conn.execute(text("SELECT filename FROM schema_migrations"))
        }

    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not files:
        sys.exit(f"No .sql files found in {MIGRATIONS_DIR}")

    pending = [f for f in files if f.name not in applied]
    if not pending:
        print(f"Up to date — {len(applied)} migration(s) already applied.")
        return

    for f in pending:
        sql = f.read_text()
        print(f"applying {f.name} …", end=" ", flush=True)
        # each migration + its bookkeeping in one transaction
        with engine.begin() as conn:
            conn.execute(text(sql))
            conn.execute(
                text("INSERT INTO schema_migrations (filename) VALUES (:f)"),
                {"f": f.name},
            )
        print("done")

    print(f"Applied {len(pending)} migration(s).")


if __name__ == "__main__":
    main()
