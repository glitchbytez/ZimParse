"""FastAPI application entrypoint."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_v1_router
from app.api.routes import health
from app.core.config import Settings, get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestLoggingMiddleware

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level, settings.log_format)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        logger.info(
            "Starting %s v%s (%s)",
            settings.app_name,
            settings.app_version,
            settings.environment.value,
        )
        yield
        logger.info("Shutting down %s", settings.app_name)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Structured data extraction from Zimbabwean identity documents.",
        debug=settings.debug,
        lifespan=lifespan,
    )

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    # Added last so it is the outermost middleware and times the full request.
    app.add_middleware(RequestLoggingMiddleware)

    register_exception_handlers(app)

    app.include_router(health.router)
    app.include_router(api_v1_router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
