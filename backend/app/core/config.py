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

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
