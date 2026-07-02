"""Send-time scheduling (IST): two weekday windows A=09:00-10:00, B=14:00-15:00, each
send at a random second inside its window; added before A/B end -> that window today,
else next working day A; weekends/holidays roll forward; missed sends roll to the next
valid window."""
from __future__ import annotations

import random
from datetime import date, datetime, time, timedelta

import holidays as holidays_lib
import pytz

from app.core.config import get_settings

_settings = get_settings()
_TZ = pytz.timezone(_settings.timezone)

_NATIONAL_FIXED = {(1, 26), (8, 15), (10, 2)}   # gazetted national holidays (always closed)
_IN_HOLIDAYS = holidays_lib.country_holidays("IN")  # full calendar, used when mode="all"


def _is_holiday(d: date) -> bool:
    """Non-working holiday per holiday_mode: "national" (3 gazetted) or "all" (full)."""
    if _settings.holiday_mode == "all":
        return d in _IN_HOLIDAYS
    return (d.month, d.day) in _NATIONAL_FIXED


def _parse_hhmm(value: str) -> time:
    h, m = value.split(":")
    return time(int(h), int(m))


WINDOW_A = (_parse_hhmm(_settings.window_a_start), _parse_hhmm(_settings.window_a_end))
WINDOW_B = (_parse_hhmm(_settings.window_b_start), _parse_hhmm(_settings.window_b_end))


def now_ist() -> datetime:
    """Current time in the configured timezone."""
    return datetime.now(_TZ)


def working_days_between(start: date, end: date) -> int:
    """Working days after `start` through `end` inclusive."""
    if end <= start:
        return 0
    count = 0
    d = start
    while d < end:
        d += timedelta(days=1)
        if is_working_day(d):
            count += 1
    return count


def is_working_day(d: date) -> bool:
    """Mon–Fri and not an Indian public holiday."""
    if d.weekday() >= 5:  # 5=Sat, 6=Sun
        return False
    return not _is_holiday(d)


def next_working_day(d: date) -> date:
    d += timedelta(days=1)
    while not is_working_day(d):
        d += timedelta(days=1)
    return d


def _random_dt_in_window(d: date, window: tuple[time, time]) -> datetime:
    """Tz-aware datetime at a random second within the window on day `d`."""
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
        if now.time() < WINDOW_A[1]:
            return _random_dt_in_window(today, WINDOW_A)
        if now.time() < WINDOW_B[1]:
            return _random_dt_in_window(today, WINDOW_B)
    return _random_dt_in_window(next_working_day(today), WINDOW_A)


def reschedule_if_past(scheduled_at: datetime, now: datetime | None = None) -> datetime:
    """Roll a past-due time to the next valid window; keep it if still in the future."""
    if now is None:
        now = datetime.now(_TZ)
    if scheduled_at.tzinfo is None:
        scheduled_at = _TZ.localize(scheduled_at)
    if scheduled_at > now:
        return scheduled_at
    return compute_send_time(now)


def followup_time_from(return_date: date) -> datetime:
    """OOO follow-up time: the return date (or next working day), window A."""
    d = return_date if is_working_day(return_date) else next_working_day(return_date)
    return _random_dt_in_window(d, WINDOW_A)
