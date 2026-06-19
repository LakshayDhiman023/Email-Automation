"""Send-time scheduling logic.

Rules (all in IST / settings.timezone):
  * Two windows per working day: A = 09:00–10:00, B = 14:00–15:00.
  * Each send gets its OWN random minute/second inside its window (looks human).
  * Working days only: Mon–Fri, excluding Indian public holidays.
  * Slot assignment when a contact is added at local time `now`:
      - before window A end (10:00)      -> today, window A
      - before window B end (15:00)      -> today, window B
      - otherwise (after 15:00)          -> next working day, window A
      - if the chosen day is weekend/holiday, roll forward to next working day
  * Missed windows (host was down) are handled by reschedule_if_past(): a send whose
    time has already passed rolls forward to the next valid window.
"""
from __future__ import annotations

import random
from datetime import date, datetime, time, timedelta

import pytz

from app.core.config import get_settings

_settings = get_settings()
_TZ = pytz.timezone(_settings.timezone)


def _national_holiday(d: date) -> bool:
    """Only India's 3 fixed national holidays, when offices are reliably closed.
    Religious/optional holidays are intentionally excluded since most companies
    work through many of them (and 'estimated' dates are unreliable)."""
    return (d.month, d.day) in {(1, 26), (8, 15), (10, 2)}


def _parse_hhmm(value: str) -> time:
    h, m = value.split(":")
    return time(int(h), int(m))


WINDOW_A = (_parse_hhmm(_settings.window_a_start), _parse_hhmm(_settings.window_a_end))
WINDOW_B = (_parse_hhmm(_settings.window_b_start), _parse_hhmm(_settings.window_b_end))


def is_working_day(d: date) -> bool:
    """Mon–Fri and not an Indian public holiday."""
    if d.weekday() >= 5:  # 5=Sat, 6=Sun
        return False
    return not _national_holiday(d)


def next_working_day(d: date) -> date:
    d += timedelta(days=1)
    while not is_working_day(d):
        d += timedelta(days=1)
    return d


def _random_dt_in_window(d: date, window: tuple[time, time]) -> datetime:
    """A timezone-aware datetime at a random second within [start, end) on day d."""
    start, end = window
    start_dt = _TZ.localize(datetime.combine(d, start))
    end_dt = _TZ.localize(datetime.combine(d, end))
    span = int((end_dt - start_dt).total_seconds())
    return start_dt + timedelta(seconds=random.randint(0, max(span - 1, 0)))


def compute_send_time(now: datetime | None = None) -> datetime:
    """Pick the next valid send datetime for a contact added at `now` (tz-aware)."""
    if now is None:
        now = datetime.now(_TZ)
    elif now.tzinfo is None:
        now = _TZ.localize(now)
    else:
        now = now.astimezone(_TZ)

    today = now.date()

    if is_working_day(today):
        # before window A closes -> window A today
        if now.time() < WINDOW_A[1]:
            return _random_dt_in_window(today, WINDOW_A)
        # before window B closes -> window B today
        if now.time() < WINDOW_B[1]:
            return _random_dt_in_window(today, WINDOW_B)

    # otherwise: next working day, window A
    return _random_dt_in_window(next_working_day(today), WINDOW_A)


def reschedule_if_past(scheduled_at: datetime, now: datetime | None = None) -> datetime:
    """If a scheduled time has already passed (host was down), roll it to the next
    valid window. Returns the same value if it's still in the future."""
    if now is None:
        now = datetime.now(_TZ)
    if scheduled_at.tzinfo is None:
        scheduled_at = _TZ.localize(scheduled_at)
    if scheduled_at > now:
        return scheduled_at
    return compute_send_time(now)


def followup_time_from(return_date: date) -> datetime:
    """For an out-of-office reply: schedule the follow-up on the recruiter's return
    date (rolled to the next working day if needed), window A."""
    d = return_date if is_working_day(return_date) else next_working_day(return_date)
    return _random_dt_in_window(d, WINDOW_A)


def followup_time_after_working_days(
    sent_at: datetime, working_days: int | None = None
) -> datetime:
    """N working days after `sent_at`, window A — the default no-reply follow-up."""
    if working_days is None:
        working_days = _settings.followup_after_working_days
    d = sent_at.astimezone(_TZ).date()
    for _ in range(working_days):
        d = next_working_day(d)
    return _random_dt_in_window(d, WINDOW_A)
