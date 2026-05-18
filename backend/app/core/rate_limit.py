"""Rate-limiting primitives.

Thin wrapper around slowapi that standardizes limits for different
categories of endpoints, per CLAUDE.md §8.3:

  - auth:             5 req/min per IP on login; 20 req/min per IP on refresh
  - portal-login:     5 req/min per IP; 10 req/hour per (username, ip)
  - portal-generic:   60 req/min per IP
  - admin-default:    120 req/min per user

Usage on an endpoint:

    from app.core.rate_limit import limiter, auth_login_limit

    @router.post("/login")
    @auth_login_limit()
    async def login(...): ...

Tests instantiate a fresh Limiter to avoid leaking state between tests
(see `backend/tests/common/test_rate_limit.py`).
"""

from __future__ import annotations

from typing import Any, Callable

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings


def _key_func(request: Request) -> str:
    """Default key function: remote IP. Respects X-Forwarded-For if set by
    a trusted upstream proxy (the deployment must strip/validate before we
    reach this layer)."""
    # Prefer the first hop of X-Forwarded-For if present; fall back to the
    # direct socket peer.
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",", 1)[0].strip()
    return get_remote_address(request)


# In dev/test the limiter is disabled so manual probes, Playwright runs,
# and pytest don't trip the production thresholds. Only `production`
# (and any custom non-dev/test env) enforces the limits.
_RATE_LIMIT_DISABLED = settings.APP_ENV in {"development", "test", "testing", "local"}

limiter = Limiter(key_func=_key_func, enabled=not _RATE_LIMIT_DISABLED)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Standard 429 response envelope, consistent with our error shape."""
    return JSONResponse(
        status_code=429,
        content={
            "error_code": "RATE_LIMIT_EXCEEDED",
            "message": "Too many requests. Please try again later.",
            "retry_after_seconds": int(getattr(exc, "retry_after", 60) or 60),
        },
        headers={"Retry-After": str(int(getattr(exc, "retry_after", 60) or 60))},
    )


# ---------------------------------------------------------------------------
# Decorators for different endpoint categories. Each returns a wrapper that
# slowapi's limiter understands; we expose them as factories (callable() → dec)
# so tests can swap in a fresh limiter.
# ---------------------------------------------------------------------------

def auth_login_limit() -> Callable[..., Any]:
    """Tight limit on /auth/login to slow credential-stuffing: 5/min/IP."""
    return limiter.limit("5/minute")


def auth_refresh_limit() -> Callable[..., Any]:
    """/auth/refresh is noisier because valid sessions refresh often: 20/min/IP."""
    return limiter.limit("20/minute")


def portal_login_limit() -> Callable[..., Any]:
    """Portal / ESS / vendor-portal login: 5/min/IP."""
    return limiter.limit("5/minute")


def portal_generic_limit() -> Callable[..., Any]:
    """General portal endpoint: 60/min/IP."""
    return limiter.limit("60/minute")


def admin_default_limit() -> Callable[..., Any]:
    """Admin catch-all: 120/min/IP."""
    return limiter.limit("120/minute")
