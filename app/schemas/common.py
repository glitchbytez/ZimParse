"""Shared response schemas."""

from typing import Any

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Any = None
    request_id: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    environment: str
