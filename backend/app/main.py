"""FastAPI entrypoint: wires routers, auth, CORS, logging, and the scheduler lifespan."""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.security import require_api_token
from app.routers import (
    export,
    health,
    outreach,
    replies,
    stats,
    suppression,
    tasks,
    templates,
)
from app.services import scheduler

settings = get_settings()

# make the services' log.info/warning/error actually surface under uvicorn
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # loud warning if the resume attachment is missing — otherwise every send fails silently
    if not Path(settings.resume_path).exists():
        log.warning("resume attachment not found at %s — sends will FAIL until it exists",
                    settings.resume_path)
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

# /health stays open — the external cron-ping keeps the free host awake and must not
# need a token. Everything else is guarded by the shared API token (if configured).
app.include_router(health.router)

_guarded = [Depends(require_api_token)]
app.include_router(templates.router, dependencies=_guarded)
app.include_router(outreach.router, dependencies=_guarded)
app.include_router(replies.router, dependencies=_guarded)
app.include_router(stats.router, dependencies=_guarded)
app.include_router(suppression.router, dependencies=_guarded)
# export has its OWN stronger, always-on token gate (see routers/export.py)
app.include_router(export.router)
# tasks has its OWN header-token check (callable by external cron even if the
# in-process scheduler was asleep) — see routers/tasks.py
app.include_router(tasks.router)
