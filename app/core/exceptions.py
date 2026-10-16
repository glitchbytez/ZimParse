"""Application exception hierarchy and global FastAPI exception handlers.

Every error response shares the envelope defined by `ErrorResponse`.
"""

import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import request_id_ctx
from app.schemas.common import ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base class for expected, client-facing application errors."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "internal_error"
    message: str = "An unexpected error occurred."

    def __init__(self, message: str | None = None, *, details: Any = None) -> None:
        self.message = message or self.message
        self.details = details
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "not_found"
    message = "The requested resource was not found."


class InvalidDocumentError(AppError):
    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    error_code = "invalid_document"
    message = "The uploaded document could not be processed."


class PayloadTooLargeError(AppError):
    status_code = status.HTTP_413_CONTENT_TOO_LARGE
    error_code = "payload_too_large"
    message = "The uploaded file exceeds the maximum allowed size."


class UnsupportedMediaTypeError(AppError):
    status_code = status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
    error_code = "unsupported_media_type"
    message = "The uploaded file type is not supported."


class ExtractionError(AppError):
    status_code = status.HTTP_502_BAD_GATEWAY
    error_code = "extraction_failed"
    message = "Data extraction from the document failed."


class UpstreamServiceError(AppError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = "upstream_unavailable"
    message = "A required upstream service is unavailable."


def _error_response(
    status_code: int, code: str, message: str, details: Any = None
) -> JSONResponse:
    body = ErrorResponse(
        error=ErrorDetail(
            code=code,
            message=message,
            details=details,
            request_id=request_id_ctx.get(),
        )
    )
    return JSONResponse(status_code=status_code, content=jsonable_encoder(body))


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    logger.warning(
        "Application error: %s",
        exc.message,
        extra={"error_code": exc.error_code, "status_code": exc.status_code},
    )
    return _error_response(exc.status_code, exc.error_code, exc.message, exc.details)


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    response = _error_response(exc.status_code, "http_error", str(exc.detail))
    if exc.headers:
        response.headers.update(exc.headers)
    return response


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = [
        {"loc": list(err.get("loc", ())), "msg": err.get("msg"), "type": err.get("type")}
        for err in exc.errors()
    ]
    return _error_response(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "validation_error",
        "Request validation failed.",
        errors,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception while processing request")
    return _error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        AppError.error_code,
        AppError.message,
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
