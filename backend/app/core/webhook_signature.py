"""HMAC webhook signature verification.

CLAUDE.md §8.6:
  - Every inbound webhook (Razorpay, Paytm, CCAvenue, bureau callbacks,
    NACH response uploads) carries an HMAC-SHA256 signature.
  - Timestamp (`X-Timestamp` / `X-Webhook-Timestamp`) must be within ±5 min.
  - Payload-level nonce is checked by the per-vendor handler against a
    short-TTL store (Redis); this module provides the primitive.

This module is INTENTIONALLY vendor-agnostic — each vendor has its own
signature scheme (Razorpay uses `X-Razorpay-Signature`, etc.). Per-vendor
routers call `verify_hmac_signature(...)` with the right header + secret.

Tests in `backend/tests/common/test_webhook_signature.py`.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass
from typing import Iterable

from fastapi import Request

from app.core.exceptions import AppException, BadRequestException

DEFAULT_MAX_CLOCK_SKEW_SECONDS = 300  # ±5 minutes


class InvalidSignatureError(BadRequestException):
    """Webhook signature did not match the computed HMAC."""

    def __init__(self, detail: str = "Invalid webhook signature") -> None:
        super().__init__(detail=detail, error_code="INVALID_WEBHOOK_SIGNATURE")


class ExpiredSignatureError(BadRequestException):
    """Webhook timestamp is outside the accepted skew window."""

    def __init__(self, detail: str = "Webhook timestamp outside accepted window") -> None:
        super().__init__(detail=detail, error_code="WEBHOOK_TIMESTAMP_EXPIRED")


class ReplayedSignatureError(BadRequestException):
    """A previously-seen nonce/timestamp combo was replayed."""

    def __init__(self, detail: str = "Webhook replay detected") -> None:
        super().__init__(detail=detail, error_code="WEBHOOK_REPLAY")


def compute_hmac_sha256(secret: str, payload: bytes, *, encoding: str = "hex") -> str:
    """HMAC-SHA256 of raw payload with secret. Returns hex (default) or base64."""
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256)
    if encoding == "hex":
        return digest.hexdigest()
    if encoding == "base64":
        import base64

        return base64.b64encode(digest.digest()).decode("ascii")
    raise ValueError(f"Unsupported encoding: {encoding}")


def verify_signature(
    secret: str,
    payload: bytes,
    provided_signature: str,
    *,
    encoding: str = "hex",
) -> bool:
    """Constant-time comparison of provided signature to expected HMAC."""
    if not provided_signature:
        return False
    expected = compute_hmac_sha256(secret, payload, encoding=encoding)
    return hmac.compare_digest(expected, provided_signature.strip())


def verify_timestamp(
    provided_timestamp: str | int,
    *,
    now: int | None = None,
    max_skew_seconds: int = DEFAULT_MAX_CLOCK_SKEW_SECONDS,
) -> bool:
    """True if provided_timestamp (Unix seconds) is within ±max_skew of now."""
    if provided_timestamp is None:
        return False
    try:
        ts = int(provided_timestamp)
    except (TypeError, ValueError):
        return False
    current = now if now is not None else int(time.time())
    return abs(current - ts) <= max_skew_seconds


@dataclass
class WebhookVerificationResult:
    """Structured result for observability / audit logging."""

    verified: bool
    reason: str | None = None


def verify_webhook(
    *,
    secret: str,
    payload: bytes,
    provided_signature: str | None,
    provided_timestamp: str | int | None,
    nonce_store: Iterable[str] | None = None,
    nonce: str | None = None,
    now: int | None = None,
    max_skew_seconds: int = DEFAULT_MAX_CLOCK_SKEW_SECONDS,
    encoding: str = "hex",
) -> WebhookVerificationResult:
    """End-to-end webhook check. Raises on failure; returns truthy on success.

    Args:
      secret: shared HMAC secret.
      payload: raw request body bytes (DO NOT re-serialize — bind on receipt).
      provided_signature: the header value from the vendor.
      provided_timestamp: unix seconds from a `X-Timestamp`-style header.
      nonce_store: iterable of recently-seen nonces; if `nonce` is in it,
                   the call raises ReplayedSignatureError.
      nonce: optional unique id from the webhook payload.
      now: override for tests.
      max_skew_seconds: how far the timestamp may be from now.
      encoding: hex (default) or base64.
    """
    if not provided_signature:
        raise InvalidSignatureError("Missing webhook signature header")

    if provided_timestamp is None:
        raise ExpiredSignatureError("Missing webhook timestamp header")

    if not verify_timestamp(
        provided_timestamp, now=now, max_skew_seconds=max_skew_seconds
    ):
        raise ExpiredSignatureError()

    if nonce is not None and nonce_store is not None and nonce in nonce_store:
        raise ReplayedSignatureError()

    if not verify_signature(secret, payload, provided_signature, encoding=encoding):
        raise InvalidSignatureError()

    return WebhookVerificationResult(verified=True)


async def read_raw_body(request: Request) -> bytes:
    """Consume the request body once and cache it for downstream handlers.

    Mirrors the idempotency middleware's body-replay trick. Call this
    from the vendor-specific webhook handler to get the EXACT bytes the
    signature was computed over."""
    body = await request.body()
    # Patch _receive so FastAPI can still parse the JSON later.
    replayed = False

    async def _receive() -> dict[str, object]:
        nonlocal replayed
        if replayed:
            return {"type": "http.disconnect"}
        replayed = True
        return {"type": "http.request", "body": body, "more_body": False}

    request._receive = _receive  # type: ignore[attr-defined]
    return body
