"""User-configurable scheduling settings (the single app_settings row).

Read on demand and cached in-process; the cache is cleared when settings are saved,
so scheduling picks up changes without a restart. Falls back to the .env defaults if
the row/table isn't present yet (e.g. migration 003 not applied).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy import text

from app.core.config import get_settings
from app.core.db import SessionLocal

log = logging.getLogger("app_settings")
_env = get_settings()


@dataclass(frozen=True)
class SchedulingSettings:
    timezone: str
    window_a_start: str
    window_a_end: str
    window_b_start: str
    window_b_end: str
    working_days: tuple[int, ...]          # ISO weekdays, 1=Mon … 7=Sun
    followup_after_working_days: int
    holiday_mode: str                      # 'none' | 'country'
    holiday_country: str                   # ISO code, e.g. 'IN', 'US'


def _env_defaults() -> SchedulingSettings:
    return SchedulingSettings(
        timezone=_env.timezone,
        window_a_start=_env.window_a_start,
        window_a_end=_env.window_a_end,
        window_b_start=_env.window_b_start,
        window_b_end=_env.window_b_end,
        working_days=(1, 2, 3, 4, 5),
        followup_after_working_days=_env.followup_after_working_days,
        holiday_mode="none",
        holiday_country="IN",
    )


_cache: SchedulingSettings | None = None


def get() -> SchedulingSettings:
    """Current scheduling settings (cached). Falls back to .env if the row is missing."""
    global _cache
    if _cache is not None:
        return _cache
    db = SessionLocal()
    try:
        row = db.execute(
            text("SELECT timezone, window_a_start, window_a_end, window_b_start, "
                 "window_b_end, working_days, followup_after_working_days, "
                 "holiday_mode, holiday_country FROM app_settings WHERE id=1")
        ).mappings().first()
        if not row:
            _cache = _env_defaults()
        else:
            _cache = SchedulingSettings(
                timezone=row["timezone"],
                window_a_start=row["window_a_start"],
                window_a_end=row["window_a_end"],
                window_b_start=row["window_b_start"],
                window_b_end=row["window_b_end"],
                working_days=tuple(row["working_days"]),
                followup_after_working_days=row["followup_after_working_days"],
                holiday_mode=row["holiday_mode"],
                holiday_country=row["holiday_country"],
            )
    except Exception as e:  # noqa: BLE001 — table may not exist yet; use env defaults
        log.warning("app_settings unavailable (%s); using .env defaults", e)
        _cache = _env_defaults()
    finally:
        db.close()
    return _cache


def invalidate() -> None:
    """Drop the cache so the next get() re-reads the DB (call after saving)."""
    global _cache
    _cache = None
