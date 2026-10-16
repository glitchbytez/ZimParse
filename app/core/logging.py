"""Logging setup with request-id correlation and optional JSON output."""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime

from app.core.config import LogFormat

request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)

# Attributes present on every LogRecord; anything else was passed via `extra=`.
_RESERVED_ATTRS = frozenset(
    logging.LogRecord("", 0, "", 0, "", None, None).__dict__.keys()
    | {"message", "asctime", "request_id"}
)


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
        }
        payload.update(
            {k: v for k, v in record.__dict__.items() if k not in _RESERVED_ATTRS}
        )
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO", fmt: LogFormat = LogFormat.JSON) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(RequestIdFilter())
    if fmt is LogFormat.JSON:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)-8s [%(request_id)s] %(name)s: %(message)s"
            )
        )

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())

    # Route uvicorn logs through our handler; drop its access log in favour of
    # the request logging middleware.
    for name in ("uvicorn", "uvicorn.error"):
        logging.getLogger(name).handlers.clear()
        logging.getLogger(name).propagate = True
    logging.getLogger("uvicorn.access").disabled = True
