"""Audit trail middleware for tracking user actions."""

import json
from datetime import datetime, timezone
from typing import Callable, Optional

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.middleware.correlation import get_correlation_id
from app.core.security import verify_token
from app.core.constants import TokenType

audit_logger = structlog.get_logger("audit")

# Methods that modify data
AUDIT_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# Paths to exclude from audit
EXCLUDED_PATHS = {
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/docs",
    "/openapi.json",
    "/health",
}


class AuditMiddleware(BaseHTTPMiddleware):
    """Middleware to log audit trail for user actions."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip non-audit methods and excluded paths
        if request.method not in AUDIT_METHODS:
            return await call_next(request)

        if request.url.path in EXCLUDED_PATHS:
            return await call_next(request)

        # Get user info from token
        user_id = None
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = verify_token(token, TokenType.ACCESS)
            if payload:
                user_id = payload.get("sub")

        # Get request info
        correlation_id = get_correlation_id()
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"

        # Try to get request body for POST/PUT/PATCH
        body = None
        if request.method in {"POST", "PUT", "PATCH"}:
            try:
                body_bytes = await request.body()
                if body_bytes:
                    body = body_bytes.decode("utf-8")
                    # Mask sensitive fields
                    body = self._mask_sensitive_data(body)
            except Exception:
                pass

        # Process request
        response = await call_next(request)

        # Determine action type
        action = self._get_action_type(method, path)

        # Truncate body if too long
        truncated_body = body[:500] if body and len(body) > 500 else body

        # Log audit entry with structured logging
        log_method = audit_logger.info if response.status_code < 400 else audit_logger.warning

        log_method(
            "audit_event",
            action=action,
            correlation_id=correlation_id,
            user_id=user_id,
            method=method,
            path=path,
            client_ip=client_ip,
            status_code=response.status_code,
            request_body=truncated_body,
        )

        return response

    def _mask_sensitive_data(self, body: str) -> str:
        """Mask sensitive fields in request body."""
        sensitive_fields = {"password", "current_password", "new_password", "confirm_password", "secret", "token"}

        try:
            data = json.loads(body)
            for field in sensitive_fields:
                if field in data:
                    data[field] = "***MASKED***"
            return json.dumps(data)
        except Exception:
            return body

    def _get_action_type(self, method: str, path: str) -> str:
        """Determine action type from method and path."""
        path_parts = path.strip("/").split("/")

        # Extract resource from path
        resource = "unknown"
        if len(path_parts) >= 3:
            resource = path_parts[2]  # e.g., /api/v1/users -> users

        action_map = {
            "POST": "CREATE",
            "PUT": "UPDATE",
            "PATCH": "UPDATE",
            "DELETE": "DELETE",
        }

        action = action_map.get(method, "UNKNOWN")
        return f"{resource.upper()}_{action}"
