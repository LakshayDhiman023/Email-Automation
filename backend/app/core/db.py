"""SQLAlchemy engine / session setup.

Supabase is fronted by a pgbouncer connection pooler. In *transaction* pooling mode
(port 6543) pgbouncer multiplexes many clients onto few server connections, which
breaks psycopg3's server-side prepared statements ("prepared statement already exists"
errors) and any session-level state. We therefore:
  * disable prepared statements (prepare_threshold=None), and
  * let pgbouncer do the pooling — SQLAlchemy uses a NullPool so it doesn't hold its
    own long-lived server connections on top of the pooler.
Run migrations against the DIRECT/session-pooler URL instead (see .env DIRECT_URL).
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import get_settings

settings = get_settings()

# A Supabase pooled URL contains the pooler host (…pooler.supabase.com) or the 6543 port.
_is_pooled = "pooler.supabase" in settings.database_url or ":6543" in settings.database_url

if _is_pooled:
    engine = create_engine(
        settings.database_url,
        poolclass=NullPool,                       # pgbouncer already pools
        connect_args={"prepare_threshold": None},  # pgbouncer txn mode: no prepared stmts
    )
else:
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,  # survive Supabase idle-pause / dropped connections
        pool_recycle=300,
    )

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
