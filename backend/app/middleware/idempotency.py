"""Idempotency middleware.

CLAUDE.md §6.3 requires every financial mutation (vouchers, disbursements,
receipts, payments, payroll runs, GL postings, adjustments, reversals) to
carry an `Idempotency-Key` header. The server hashes the normalized request
body, stores `(user_id, key, request_hash, response)` for 24h, and:

  - Returns the cached response on a retry that matches key + hash.
  - Rejects 422 if the same key is reused with a different body (mis-use).
  - Requires the header on every request whose path matches `MUTATING_PATHS`.

The middleware intentionally sits BEFORE the DB transaction — reading or
writing the idempotency row is a separate, short transaction so that a
long-running financial endpoint cannot block a retry from finding its cache.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable, Iterable, Pattern
from uuid import UUID

import structlog
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.constants import TokenType
from app.core.security import verify_token
from app import database as app_database
from app.models.core.idempotency_key import IdempotencyKey

logger = structlog.get_logger("idempotency")

IDEMPOTENCY_TTL = timedelta(hours=24)

# Paths that REQUIRE an Idempotency-Key header. Any POST/PUT/PATCH/DELETE
# under `/api/v1/<resource>` where `<resource>` matches one of these is a
# financial mutation per §6.3.
MUTATING_RESOURCES: list[str] = [
    "vouchers",
    "payments",
    "purchase-bills",
    "sales-invoices",
    "receipts",
    "disbursements",
    "payroll",
    "tds/challans",
    "fixed-assets",
    "fixed-deposits",
    "lending/disbursements",
    "lending/receipts",
    "lending/loan-accounts",
    "ap-ar",
]

MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

_PATH_RE: Pattern[str] = re.compile(
    r"^/api/v1/(" + "|".join(re.escape(r) for r in MUTATING_RESOURCES) + r")(/|$)",
)


def _user_id_from_request(request: Request) -> UUID | None:
    auth = request.headers.get("authorization")
    if not auth or not auth.startswith("Bearer "):
        return None
    payload = verify_token(auth.split(" ", 1)[1], TokenType.ACCESS)
    if not payload:
        return None
    sub = payload.get("sub")
    try:
        return UUID(str(sub)) if sub else None
    except (TypeError, ValueError):
        return None


def _hash_body(body: bytes) -> str:
    if not body:
        return hashlib.sha256(b"").hexdigest()
    # Normalize JSON when possible so whitespace-only differences don't
    # break cache lookup.
    try:
        parsed = json.loads(body)
        normalized = json.dumps(parsed, sort_keys=True, separators=(",", ":")).encode()
    except (ValueError, UnicodeDecodeError):
        normalized = body
    return hashlib.sha256(normalized).hexdigest()


def _requires_idempotency(request: Request) -> bool:
    if request.method not in MUTATING_METHODS:
        return False
    return bool(_PATH_RE.match(request.url.path))


def _json_error(status: int, code: str, message: str, correlation_id: str | None = None) -> JSONResponse:
    body: dict[str, object] = {"error_code": code, "message": message}
    if correlation_id:
        body["correlation_id"] = correlation_id
    return JSONResponse(body, status_code=status)


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """Enforce Idempotency-Key on financial mutations and replay cached responses."""

    def __init__(
        self,
        app,
        extra_mutating_patterns: Iterable[str] | None = None,
    ) -> None:
        super().__init__(app)
        extra = list(extra_mutating_patterns or [])
        if extra:
            self._extra_re: Pattern[str] | None = re.compile("|".join(extra))
        else:
            self._extra_re = None

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        path = request.url.path
        matches = _requires_idempotency(request) or (
            self._extra_re is not None and self._extra_re.search(path) is not None
        )
        if not matches:
            return await call_next(request)

        key = request.headers.get("idempotency-key") or request.headers.get("Idempotency-Key")
        if not key:
            return _json_error(
                400,
                "IDEMPOTENCY_KEY_REQUIRED",
                "Idempotency-Key header is required for this endpoint.",
            )
        if len(key) > 255 or len(key) < 8:
            return _json_error(
                400,
                "IDEMPOTENCY_KEY_INVALID",
                "Idempotency-Key must be 8–255 characters.",
            )

        user_id = _user_id_from_request(request)
        body_bytes = await request.body()
        request_hash = _hash_body(body_bytes)

        # Look up cached response.
        async with app_database.async_session_factory() as session:
            row = (
                await session.execute(
                    select(IdempotencyKey).where(
                        IdempotencyKey.user_id == user_id,
                        IdempotencyKey.key == key,
                    )
                )
            ).scalar_one_or_none()

            if row is not None:
                # Normalize both sides of the comparison so this works on
                # Postgres (TIMESTAMPTZ → aware) and SQLite (naive in tests).
                expires_at = row.expires_at
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
                if expires_at < datetime.now(timezone.utc):
                    await session.delete(row)
                    await session.commit()
                elif row.request_hash != request_hash:
                    return _json_error(
                        422,
                        "IDEMPOTENCY_KEY_REUSED",
                        "Idempotency-Key has already been used with a different request body.",
                    )
                else:
                    logger.info(
                        "idempotency_cache_hit",
                        user_id=str(user_id) if user_id else None,
                        key=key,
                        status=row.response_status,
                    )
                    return Response(
                        content=row.response_body or b"",
                        status_code=row.response_status,
                        media_type="application/json",
                    )

        # Rehydrate the body on the existing Request so downstream handlers
        # can still read it. Starlette's BaseHTTPMiddleware is brittle when
        # you reconstruct a Request object (TaskGroup / double-body issues),
        # so we patch the private `_receive` instead.
        body_replayed = False

        async def _receive() -> dict[str, object]:
            nonlocal body_replayed
            if body_replayed:
                return {"type": "http.disconnect"}
            body_replayed = True
            return {"type": "http.request", "body": body_bytes, "more_body": False}

        request._receive = _receive  # type: ignore[attr-defined]

        response = await call_next(request)

        # Only cache successful-ish responses (2xx + 409s that should be
        # stable) so transient failures don't poison retries.
        if response.status_code < 500:
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk

            # Reassemble response with the captured body so the client still gets it.
            new_response = Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

            if 200 <= response.status_code < 300 or response.status_code == 409:
                async with app_database.async_session_factory() as session:
                    try:
                        session.add(
                            IdempotencyKey(
                                key=key,
                                user_id=user_id,
                                method=request.method,
                                path=path,
                                request_hash=request_hash,
                                response_status=response.status_code,
                                response_body=response_body.decode("utf-8", errors="replace"),
                                response_headers=None,
                                expires_at=datetime.now(timezone.utc) + IDEMPOTENCY_TTL,
                            )
                        )
                        await session.commit()
                    except Exception:  # noqa: BLE001
                        # Another concurrent call may have written the row; safe to ignore.
                        await session.rollback()

            return new_response

        return response
