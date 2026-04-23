"""Common API endpoints."""

from app.api.v1.common.audit_logs import router as audit_logs_router

__all__ = [
    "audit_logs_router",
]
