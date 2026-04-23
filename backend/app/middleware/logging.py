"""Structured request/response logging middleware."""

import time
from typing import Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.middleware.correlation import get_correlation_id

logger = structlog.get_logger("api.access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for structured HTTP request logging."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Bind request context
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            correlation_id=get_correlation_id(),
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else "unknown",
        )

        # Log request start
        logger.info(
            "request_started",
            query_params=str(request.query_params) if request.query_params else None,
            user_agent=request.headers.get("user-agent"),
        )

        try:
            response = await call_next(request)
            duration_ms = round((time.time() - start_time) * 1000, 2)

            # Select log level based on status code
            log_method = logger.info if response.status_code < 400 else logger.warning
            if response.status_code >= 500:
                log_method = logger.error

            log_method(
                "request_completed",
                status_code=response.status_code,
                duration_ms=duration_ms,
            )

            return response

        except Exception as e:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            logger.exception(
                "request_failed",
                duration_ms=duration_ms,
                error_type=type(e).__name__,
                error_message=str(e),
            )
            raise
