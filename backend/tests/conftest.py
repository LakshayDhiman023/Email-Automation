"""Test fixtures: pin scheduling settings in-process so no test touches a database."""
import pytest

import app.services.app_settings as app_settings
from app.services.app_settings import SchedulingSettings


@pytest.fixture(autouse=True)
def fixed_settings():
    app_settings._cache = SchedulingSettings(
        timezone="Asia/Kolkata",
        window_a_start="09:00",
        window_a_end="10:00",
        window_b_start="14:00",
        window_b_end="15:00",
        working_days=(1, 2, 3, 4, 5),
        followup_after_working_days=5,
        holiday_mode="none",
        holiday_country="IN",
        sender_name="Test User",
        signature="Best regards,\nTest User",
    )
    yield
    app_settings._cache = None
