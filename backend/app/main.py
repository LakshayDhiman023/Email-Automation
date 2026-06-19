"""FastAPI application entrypoint.

Phase 1: app skeleton + /health (used by the external cron-ping to keep a free
host awake). Routers for recruiters, templates, sends, replies are wired in later
phases.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import health
from app.services import scheduler

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()  # starts APScheduler + runs catch-up on missed sends
    yield
    scheduler.shutdown()


app = FastAPI(
    title="Recruiter Outreach Automation Platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
