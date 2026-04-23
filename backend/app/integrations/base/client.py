"""Integration base client.

Every external-API integration (GSTN, CKYC, CIBIL, Razorpay, NACH, ...)
inherits from this. It provides:

  - `httpx.AsyncClient` lifecycle (created lazily, closed on `aclose()`).
  - Explicit timeouts: connect 5 s, read 30 s, write 10 s, pool 5 s.
  - Exponential-backoff retry with jitter on 5xx / timeouts / connection
    errors; NEVER retries 4xx (those are final, shouldn't loop).
  - Circuit breaker: 5 consecutive failures opens the breaker; half-open
    probe after 60 s; a successful half-open probe closes it again.
  - Structured logging via structlog with the vendor name and correlation id.

Per-vendor clients subclass, set `VENDOR_NAME`, `base_url`, and implement
auth + request-signing via `_prepare_request()`. See CLAUDE.md §6.7.
"""

from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

import httpx
import structlog

logger = structlog.get_logger("integration")

DEFAULT_TIMEOUT = httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0)


class IntegrationError(Exception):
    """Any failure raised by the integration base. Subclasses add shape."""

    def __init__(
        self,
        message: str,
        *,
        vendor: str | None = None,
        status_code: int | None = None,
        response_body: str | None = None,
    ) -> None:
        super().__init__(message)
        self.vendor = vendor
        self.status_code = status_code
        self.response_body = response_body


class IntegrationTimeoutError(IntegrationError):
    """The vendor did not respond within the timeout budget."""


class IntegrationAuthError(IntegrationError):
    """401/403 from the vendor — credential problem. NEVER retried."""


class IntegrationConflictError(IntegrationError):
    """409 from the vendor — caller should NOT retry blindly."""


class CircuitOpenError(IntegrationError):
    """The circuit is open for this vendor; the call was short-circuited.

    Distinct from a timeout / 5xx so callers can decide whether to cache
    a stale value or surface a 503 to their own caller."""


# ---------------------------------------------------------------------------
# Circuit breaker state machine.
# ---------------------------------------------------------------------------

class CircuitState(str, Enum):
    CLOSED = "closed"          # normal; requests flow
    OPEN = "open"              # all requests short-circuit
    HALF_OPEN = "half_open"    # one probe allowed


@dataclass
class CircuitBreaker:
    """Per-vendor circuit breaker. Thread-safe via asyncio Lock.

    Defaults (CLAUDE.md §6.7): fail_threshold=5, recovery_seconds=60."""

    fail_threshold: int = 5
    recovery_seconds: float = 60.0
    state: CircuitState = CircuitState.CLOSED
    consecutive_failures: int = 0
    opened_at: float | None = None
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def allow(self) -> bool:
        """Return True if the next request should be attempted."""
        async with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
            if self.state == CircuitState.OPEN:
                elapsed = time.monotonic() - (self.opened_at or 0.0)
                if elapsed >= self.recovery_seconds:
                    self.state = CircuitState.HALF_OPEN
                    return True
                return False
            # HALF_OPEN — only one probe in flight at a time.
            return False

    async def record_success(self) -> None:
        async with self._lock:
            self.consecutive_failures = 0
            self.state = CircuitState.CLOSED
            self.opened_at = None

    async def record_failure(self) -> None:
        async with self._lock:
            self.consecutive_failures += 1
            if (
                self.state == CircuitState.HALF_OPEN
                or self.consecutive_failures >= self.fail_threshold
            ):
                self.state = CircuitState.OPEN
                self.opened_at = time.monotonic()


# ---------------------------------------------------------------------------
# Base client.
# ---------------------------------------------------------------------------

class IntegrationClient:
    """Subclass and override VENDOR_NAME + base_url (+ optional _prepare_request)."""

    VENDOR_NAME: str = "integration"
    DEFAULT_MAX_RETRIES: int = 3
    DEFAULT_BACKOFF_BASE: float = 0.25   # seconds; 0.25, 0.5, 1.0, 2.0 …
    DEFAULT_BACKOFF_CAP: float = 4.0

    def __init__(
        self,
        base_url: str,
        *,
        timeout: httpx.Timeout = DEFAULT_TIMEOUT,
        max_retries: int | None = None,
        backoff_base: float | None = None,
        backoff_cap: float | None = None,
        circuit_fail_threshold: int = 5,
        circuit_recovery_seconds: float = 60.0,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries if max_retries is not None else self.DEFAULT_MAX_RETRIES
        self.backoff_base = backoff_base if backoff_base is not None else self.DEFAULT_BACKOFF_BASE
        self.backoff_cap = backoff_cap if backoff_cap is not None else self.DEFAULT_BACKOFF_CAP
        self._client = http_client or httpx.AsyncClient(timeout=self.timeout)
        self._owns_client = http_client is None
        self.breaker = CircuitBreaker(
            fail_threshold=circuit_fail_threshold,
            recovery_seconds=circuit_recovery_seconds,
        )

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    # -------- hooks for subclasses --------

    def _prepare_request(
        self,
        method: str,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> httpx.Request:
        """Override to inject auth/signature headers. Default is pass-through."""
        return self._client.build_request(
            method,
            url,
            params=params,
            json=json,
            headers=dict(headers or {}),
        )

    # -------- core request --------

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> httpx.Response:
        """Issue a request with retry + circuit-breaker + structured logs.

        Raises:
          CircuitOpenError:       when the breaker is open.
          IntegrationAuthError:   on 401/403. NOT retried.
          IntegrationTimeoutError: when every retry hits a timeout.
          IntegrationError:       on persistent 5xx or other transport errors.
        """
        if not await self.breaker.allow():
            raise CircuitOpenError(
                f"Circuit is open for vendor '{self.VENDOR_NAME}'",
                vendor=self.VENDOR_NAME,
            )

        url = f"{self.base_url}{path}" if path.startswith("/") else f"{self.base_url}/{path}"
        attempt = 0
        last_error: BaseException | None = None

        while True:
            attempt += 1
            try:
                request = self._prepare_request(
                    method, url, params=params, json=json, headers=headers
                )
                response = await self._client.send(request)
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_error = exc
                await self._on_transport_failure(attempt, exc)
                if attempt > self.max_retries:
                    raise IntegrationTimeoutError(
                        f"{self.VENDOR_NAME}: transport error after {attempt - 1} retries: {exc}",
                        vendor=self.VENDOR_NAME,
                    ) from exc
                await self._sleep_for_backoff(attempt)
                continue

            # 2xx / 3xx → success.
            if response.status_code < 400:
                await self.breaker.record_success()
                return response

            # 4xx → final. 401/403 → auth error subclass.
            if 400 <= response.status_code < 500:
                if response.status_code in (401, 403):
                    await self.breaker.record_failure()
                    raise IntegrationAuthError(
                        f"{self.VENDOR_NAME}: auth error {response.status_code}",
                        vendor=self.VENDOR_NAME,
                        status_code=response.status_code,
                        response_body=_safe_text(response),
                    )
                if response.status_code == 409:
                    raise IntegrationConflictError(
                        f"{self.VENDOR_NAME}: conflict 409",
                        vendor=self.VENDOR_NAME,
                        status_code=response.status_code,
                        response_body=_safe_text(response),
                    )
                # Other 4xx → reset breaker (caller bug, not vendor outage).
                await self.breaker.record_success()
                return response

            # 5xx → retryable.
            last_error = IntegrationError(
                f"{self.VENDOR_NAME}: {response.status_code}",
                vendor=self.VENDOR_NAME,
                status_code=response.status_code,
                response_body=_safe_text(response),
            )
            await self._on_transport_failure(attempt, last_error)
            if attempt > self.max_retries:
                raise last_error
            await self._sleep_for_backoff(attempt)

    async def get(self, path: str, **kwargs) -> httpx.Response:
        return await self.request("GET", path, **kwargs)

    async def post(self, path: str, **kwargs) -> httpx.Response:
        return await self.request("POST", path, **kwargs)

    # -------- backoff + metrics --------

    async def _sleep_for_backoff(self, attempt: int) -> None:
        delay = min(self.backoff_cap, self.backoff_base * (2 ** (attempt - 1)))
        jitter = random.uniform(0, delay / 2)
        await asyncio.sleep(delay + jitter)

    async def _on_transport_failure(self, attempt: int, exc: BaseException) -> None:
        await self.breaker.record_failure()
        logger.warning(
            "integration_attempt_failed",
            vendor=self.VENDOR_NAME,
            attempt=attempt,
            breaker_state=self.breaker.state,
            consecutive_failures=self.breaker.consecutive_failures,
            error_type=type(exc).__name__,
            error=str(exc),
        )


def _safe_text(response: httpx.Response) -> str:
    """Return truncated text for logs; never raw-dump 10MB payloads."""
    try:
        body = response.text
    except Exception:  # noqa: BLE001
        return "<binary>"
    return body[:1000] + ("…" if len(body) > 1000 else "")
