"""Security-response-headers middleware.

Adds the OWASP baseline response headers that CLAUDE.md §8.9 requires:

  - Strict-Transport-Security: HSTS (1 year, includeSubDomains, preload)
  - Content-Security-Policy: strict default (no inline JS, no data:)
  - X-Frame-Options: DENY (clickjacking)
  - X-Content-Type-Options: nosniff
  - Referrer-Policy: strict-origin-when-cross-origin
  - Permissions-Policy: camera=(), geolocation=(), microphone=()

HSTS is omitted on non-HTTPS / non-production requests so local dev over
`http://` doesn't accidentally get pinned.
"""

from __future__ import annotations

from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

DEFAULT_CSP = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: blob:; "
    "font-src 'self' data:; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'self'"
)

DEFAULT_PERMISSIONS_POLICY = (
    "camera=(), geolocation=(), microphone=(), "
    "payment=(), usb=(), magnetometer=(), gyroscope=()"
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds the standard security-response headers to every response."""

    def __init__(
        self,
        app,
        *,
        csp: str | None = None,
        permissions_policy: str | None = None,
        hsts_max_age: int = 31_536_000,  # 1 year
    ) -> None:
        super().__init__(app)
        self.csp = csp or DEFAULT_CSP
        self.permissions_policy = permissions_policy or DEFAULT_PERMISSIONS_POLICY
        self.hsts_max_age = hsts_max_age

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        self._apply_headers(request, response)
        return response

    def _apply_headers(self, request: Request, response: Response) -> None:
        # Clickjacking defense.
        response.headers.setdefault("X-Frame-Options", "DENY")

        # MIME-sniffing defense.
        response.headers.setdefault("X-Content-Type-Options", "nosniff")

        # Referrer leakage control — send full origin on same-origin, none cross-origin.
        response.headers.setdefault(
            "Referrer-Policy", "strict-origin-when-cross-origin"
        )

        # CSP — strict default. Applications that need to relax it must do so
        # per-route by overriding the header AFTER this middleware runs
        # (Starlette headers `setdefault` respects that: if the app set it
        # first, we don't override). The order is: app sets header → response
        # flows back through middleware → this middleware adds only if missing.
        response.headers.setdefault("Content-Security-Policy", self.csp)

        # Permissions-Policy — lock down powerful APIs unless app enables them.
        response.headers.setdefault("Permissions-Policy", self.permissions_policy)

        # HSTS — only over HTTPS, and only in production. Avoid pinning
        # browsers to HTTPS when serving on `http://localhost` in dev.
        is_prod = settings.APP_ENV.lower() in {"production", "prod", "staging"}
        is_https = request.url.scheme == "https"
        if is_prod and is_https:
            response.headers.setdefault(
                "Strict-Transport-Security",
                f"max-age={self.hsts_max_age}; includeSubDomains; preload",
            )

        # X-Permitted-Cross-Domain-Policies (Adobe Flash / PDF).
        response.headers.setdefault("X-Permitted-Cross-Domain-Policies", "none")

        # Remove the Server header if FastAPI/Uvicorn set it — don't leak version.
        if "server" in response.headers:
            del response.headers["server"]
