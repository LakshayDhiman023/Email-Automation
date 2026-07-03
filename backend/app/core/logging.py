"""Structured (JSON) logging so every log line is machine-parseable and carries
enough context (request id, client ip, path) to reconstruct who-did-what-when —
the shape audit trails and log aggregators expect, without adding a dependency.
"""
from __future__ import annotations

import json
import logging
from contextvars import ContextVar

# Set by the request-context middleware for the duration of one request; read by
# JsonFormatter so every log emitted while handling it carries the same request id.
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
client_ip_ctx: ContextVar[str | None] = ContextVar("client_ip", default=None)

_RESERVED = frozenset(logging.LogRecord(
    "", 0, "", 0, "", (), None
).__dict__.keys()) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        rid = request_id_ctx.get()
        ip = client_ip_ctx.get()
        if rid:
            payload["request_id"] = rid
        if ip:
            payload["client_ip"] = ip
        # any extra=... fields passed to the log call ride along verbatim
        for key, value in record.__dict__.items():
            if key not in _RESERVED:
                payload[key] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
    # our own request_context middleware logs one structured line per request
    # (method, path, status, duration, request_id, client_ip) — disable uvicorn's
    # unstructured access log so requests aren't logged twice in two formats.
    logging.getLogger("uvicorn.access").disabled = True
