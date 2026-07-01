"""
DSRA V2 — FastAPI Exception Handlers
=======================================
Converts all DSRA custom exceptions and standard FastAPI exceptions
into a consistent JSON error response schema.

Every response follows:
{
  "error": {
    "code": "MACHINE_READABLE_CODE",
    "message": "Human readable message.",
    "details": {...},
    "request_id": "uuid",
    "timestamp": "ISO datetime"
  }
}
"""

from datetime import datetime
from typing import Any
from uuid import uuid4

import structlog
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.exceptions.base import DSRABaseError

log = structlog.get_logger(__name__)


def _error_response(
    code: str,
    message: str,
    http_status: int,
    details: dict[str, Any] | None = None,
    request_id: str | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=http_status,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
                "request_id": request_id or str(uuid4()),
                "timestamp": datetime.utcnow().isoformat(),
            }
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI application."""

    @app.exception_handler(DSRABaseError)
    async def dsra_error_handler(
        request: Request, exc: DSRABaseError
    ) -> JSONResponse:
        request_id = str(uuid4())
        log.warning(
            "dsra_error",
            code=exc.code,
            message=exc.message,
            http_status=exc.http_status,
            request_id=request_id,
            path=str(request.url),
        )
        return _error_response(
            code=exc.code,
            message=exc.message,
            http_status=exc.http_status,
            details=exc.details,
            request_id=request_id,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        request_id = str(uuid4())
        log.warning(
            "validation_error",
            errors=exc.errors(),
            request_id=request_id,
            path=str(request.url),
        )
        return _error_response(
            code="VALIDATION_ERROR",
            message="Request validation failed. Check the details field for specifics.",
            http_status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details={"errors": exc.errors()},
            request_id=request_id,
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        request_id = str(uuid4())
        log.error(
            "unhandled_exception",
            exc_type=type(exc).__name__,
            exc_message=str(exc),
            request_id=request_id,
            path=str(request.url),
            exc_info=True,
        )
        return _error_response(
            code="INTERNAL_ERROR",
            message="An unexpected error occurred. Our team has been notified.",
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            request_id=request_id,
        )
