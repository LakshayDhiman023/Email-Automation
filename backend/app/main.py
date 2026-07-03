"""FastAPI entrypoint: wires routers, auth, CORS, logging, and the scheduler lifespan."""
import logging
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging import client_ip_ctx, configure_logging, request_id_ctx
from app.core.security import require_api_token
from app.routers import (
    audit,
    export,
    health,
    outreach,
    replies,
    settings as settings_router,
    stats,
    suppression,
    tasks,
    templates,
)
from app.services import scheduler

settings = get_settings()

# structured (JSON) logs: every line carries level/logger/message plus, for
# request-scoped log calls, a request id and client ip (see request_context below) —
# the shape an audit trail or log aggregator needs.
configure_logging()
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


# Interactive API docs are only served when auth is disabled (local dev). On a public
# deployment (API_TOKEN set) they'd enumerate every endpoint for attackers (OWASP A05).
_docs_on = not settings.api_token

app = FastAPI(
    title="Email Outreach Automation",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if _docs_on else None,
    redoc_url="/redoc" if _docs_on else None,
    openapi_url="/openapi.json" if _docs_on else None,
)

# Largest legitimate payload is a template body (~20 KB); anything near 1 MB is abuse.
_MAX_BODY_BYTES = 1_000_000


@app.middleware("http")
async def request_context(request: Request, call_next):
    """Stamp every request with an id + client ip (picked up by JsonFormatter so
    every log line emitted while handling it is attributable), and log a single
    structured access line per request — who did what, when, from where."""
    rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
    ip = request.client.host if request.client else "unknown"
    rid_token = request_id_ctx.set(rid)
    ip_token = client_ip_ctx.set(ip)
    started = time.monotonic()
    try:
        response = await call_next(request)
    finally:
        request_id_ctx.reset(rid_token)
        client_ip_ctx.reset(ip_token)
    duration_ms = round((time.monotonic() - started) * 1000, 1)
    logging.getLogger("access").info(
        "%s %s -> %s", request.method, request.url.path, response.status_code,
        extra={"method": request.method, "path": request.url.path,
               "status": response.status_code, "duration_ms": duration_ms,
               "request_id": rid, "client_ip": ip},
    )
    response.headers["X-Request-Id"] = rid
    return response


@app.middleware("http")
async def security_headers(request: Request, call_next):
    """Reject oversized bodies early (OWASP API4) and add standard security headers
    to every response (OWASP A05)."""
    length = request.headers.get("content-length")
    if length and length.isdigit() and int(length) > _MAX_BODY_BYTES:
        return JSONResponse({"detail": "request body too large"}, status_code=413)
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Cache-Control", "no-store")  # API data is private
    if request.url.scheme == "https":
        response.headers.setdefault(
            "Strict-Transport-Security", "max-age=63072000; includeSubDomains"
        )
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# /health stays unversioned and open — infra probes (the external cron-ping that
# keeps a free host awake, container healthchecks) shouldn't have to track an API
# version, and it must not need a token. Everything else lives under /api/v1 so a
# future breaking change has somewhere to go without disturbing this contract.
app.include_router(health.router)

API_V1 = "/api/v1"
_guarded = [Depends(require_api_token)]
app.include_router(templates.router, prefix=API_V1, dependencies=_guarded)
app.include_router(outreach.router, prefix=API_V1, dependencies=_guarded)
app.include_router(replies.router, prefix=API_V1, dependencies=_guarded)
app.include_router(stats.router, prefix=API_V1, dependencies=_guarded)
app.include_router(suppression.router, prefix=API_V1, dependencies=_guarded)
app.include_router(settings_router.router, prefix=API_V1, dependencies=_guarded)
app.include_router(audit.router, prefix=API_V1, dependencies=_guarded)
# export has its OWN stronger, always-on token gate (see routers/export.py)
app.include_router(export.router, prefix=API_V1)
# tasks has its OWN header-token check (callable by external cron even if the
# in-process scheduler was asleep) — see routers/tasks.py
app.include_router(tasks.router, prefix=API_V1)
