"""Application settings, loaded from environment / .env."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/postgres"

    # Gmail (populated in Phase 2)
    gmail_client_id: str = ""
    gmail_client_secret: str = ""
    gmail_refresh_token: str = ""
    gmail_sender: str = ""

    # App
    timezone: str = "Asia/Kolkata"
    resume_path: str = "resume/resume.pdf"
    cors_origins: str = "http://localhost:5173"

    # Scheduling windows (HH:MM, 24h, in `timezone`)
    window_a_start: str = "09:00"
    window_a_end: str = "10:00"
    window_b_start: str = "14:00"
    window_b_end: str = "15:00"
    followup_after_working_days: int = 5
    # Holiday handling for scheduling: "national" = only India's 3 gazetted national
    # holidays (most firms work through festivals); "all" = full `holidays` India set.
    holiday_mode: str = "national"

    # Shared secret guarding ALL app endpoints (sent as X-API-Token). Empty => auth
    # disabled (local dev only). MUST be set in any public deployment, since the app
    # can send email from the user's Gmail.
    api_token: str = ""

    # Shared secret required to download the outreach CSV export (which contains every
    # recruiter email + message body). Empty => export endpoint is DISABLED (fail-closed)
    # so the data dump is never exposed unauthenticated.
    export_token: str = ""

    # Deliverability / safety guards (Phase 8 hardening)
    daily_send_cap: int = 40          # max emails sent per rolling 24h (0 = unlimited)
    contact_cooldown_days: int = 30   # don't re-email the same person within N days
    max_send_attempts: int = 3        # retry a transient Gmail failure up to N times
    # Sends are naturally spaced: at most _MAX_SENDS_PER_TICK (2) leave per 1-minute
    # tick, so a batch drips out ~30-60s apart without blocking the scheduler thread.

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
