"""ASGI middleware: request-id propagation and structured access logging."""

import logging
import time
import uuid

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.logging import request_id_ctx

logger = logging.getLogger("app.access")

REQUEST_ID_HEADER = "X-Request-ID"


class RequestLoggingMiddleware:
    """Assigns a request id, exposes it in the response headers and logs each request.

    Implemented as pure ASGI middleware (rather than BaseHTTPMiddleware) so it
    does not buffer streaming responses or break contextvars propagation.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        incoming = dict(scope["headers"]).get(REQUEST_ID_HEADER.lower().encode())
        request_id = incoming.decode("latin-1")[:128] if incoming else uuid.uuid4().hex
        token = request_id_ctx.set(request_id)
        scope.setdefault("state", {})["request_id"] = request_id

        status_code = 500
        start = time.perf_counter()

        async def send_wrapper(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                MutableHeaders(scope=message)[REQUEST_ID_HEADER] = request_id
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            client = scope.get("client")
            logger.info(
                "%s %s %s",
                scope["method"],
                scope["path"],
                status_code,
                extra={
                    "method": scope["method"],
                    "path": scope["path"],
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                    "client_ip": client[0] if client else None,
                },
            )
            request_id_ctx.reset(token)
