"""Deliverability & safety guards — the single source of truth for "may we email
this address right now?".

These encode the lessons that sink most cold-outreach setups:
  * suppression / opt-out list  — never email someone who bounced, went negative,
    or asked to stop (CAN-SPAM / GDPR hygiene, and basic decency).
  * daily send cap              — a free Gmail account that blasts hundreds/day gets
    flagged or suspended; stay well under the limit.
  * per-contact cooldown        — don't re-email the same person within N days even
    across separate threads (looks desperate / spammy).

All functions are pure DB reads (except suppress()) so they can be called from the
add-contact path AND re-checked at send time.
"""
from __future__ import annotations

import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings

log = logging.getLogger("guards")
_settings = get_settings()


def is_suppressed(db: Session, email: str) -> str | None:
    """Return the suppression reason if `email` is on the opt-out list, else None."""
    row = db.execute(
        text("SELECT reason FROM suppression_list WHERE email=:e"),
        {"e": email.strip().lower()},
    ).first()
    return row[0] if row else None


def suppress(db: Session, email: str, reason: str = "manual",
            note: str | None = None) -> None:
    """Add an address to the opt-out list (idempotent). Does NOT commit."""
    db.execute(
        text(
            """
            INSERT INTO suppression_list (email, reason, note)
            VALUES (:e, :r, :n)
            ON CONFLICT (email) DO UPDATE SET reason=EXCLUDED.reason,
                                              note=COALESCE(EXCLUDED.note, suppression_list.note)
            """
        ),
        {"e": email.strip().lower(), "r": reason, "n": note},
    )
    log.info("suppressed %s (%s)", email, reason)


def within_cooldown(db: Session, email: str) -> bool:
    """True if we emailed this address within contact_cooldown_days (so we should
    hold off). 0 disables the cooldown."""
    days = _settings.contact_cooldown_days
    if days <= 0:
        return False
    row = db.execute(
        text(
            """
            SELECT 1 FROM recruiters
            WHERE email=:e AND last_contacted_at IS NOT NULL
              AND last_contacted_at > now() - make_interval(days => :d)
            LIMIT 1
            """
        ),
        {"e": email.strip().lower(), "d": days},
    ).first()
    return row is not None


def sends_in_last_24h(db: Session) -> int:
    """How many emails have actually gone out in the trailing 24h (for the cap)."""
    return db.execute(
        text("SELECT count(*) FROM sends WHERE status='sent' "
             "AND sent_at > now() - interval '24 hours'")
    ).scalar_one()


def daily_cap_remaining(db: Session) -> int:
    """Remaining sends allowed in the current rolling 24h window. A very large number
    means 'effectively unlimited' (cap disabled)."""
    cap = _settings.daily_send_cap
    if cap <= 0:
        return 10**9
    return max(cap - sends_in_last_24h(db), 0)
