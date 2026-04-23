"""Integration base-client tests.

Uses `httpx.MockTransport` to simulate vendor responses without network.
CLAUDE.md §6.7.
"""

from __future__ import annotations

import asyncio
import itertools
from typing import Iterable

import httpx
import pytest

from app.integrations.base.client import (
    CircuitBreaker,
    CircuitOpenError,
    CircuitState,
    IntegrationAuthError,
    IntegrationClient,
    IntegrationConflictError,
    IntegrationError,
    IntegrationTimeoutError,
)


def _scripted_transport(responses: Iterable):
    """Build a MockTransport that returns each response in sequence.

    Entries can be either `httpx.Response` (returned) or an exception class /
    instance (raised) to simulate transport errors."""
    it = iter(responses)

    def handler(request: httpx.Request) -> httpx.Response:
        nxt = next(it)
        if isinstance(nxt, BaseException):
            raise nxt
        if isinstance(nxt, type) and issubclass(nxt, BaseException):
            raise nxt("simulated")
        return nxt  # type: ignore[return-value]

    return httpx.MockTransport(handler)


def _fast_client(responses: Iterable) -> IntegrationClient:
    """Build a client with very fast backoffs for testing."""
    transport = _scripted_transport(responses)
    http = httpx.AsyncClient(transport=transport)
    return IntegrationClient(
        base_url="https://vendor.test",
        max_retries=2,
        backoff_base=0.001,
        backoff_cap=0.002,
        circuit_fail_threshold=3,
        circuit_recovery_seconds=0.05,
        http_client=http,
    )


# ---------------------------------------------------------------------------
# Happy path.
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_returns_200_without_retry() -> None:
    client = _fast_client([httpx.Response(200, json={"ok": True})])
    r = await client.get("/status")
    assert r.status_code == 200
    assert r.json() == {"ok": True}
    assert client.breaker.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_post_forwards_json_and_params() -> None:
    seen: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["url"] = str(request.url)
        seen["body"] = request.read()
        return httpx.Response(200, json={"ok": True})

    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    client = IntegrationClient(base_url="https://v.test", http_client=http)

    await client.post("/orders", json={"amount": 100}, params={"x": "y"})
    assert seen["method"] == "POST"
    assert "orders?x=y" in seen["url"]
    assert b'"amount":100' in seen["body"]


# ---------------------------------------------------------------------------
# Retry on transient failures.
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_retries_on_5xx_then_succeeds() -> None:
    client = _fast_client([
        httpx.Response(503),
        httpx.Response(503),
        httpx.Response(200, json={"ok": True}),
    ])
    r = await client.get("/x")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_retries_on_timeout_then_succeeds() -> None:
    client = _fast_client([
        httpx.ConnectTimeout("slow"),
        httpx.Response(200, json={"ok": True}),
    ])
    r = await client.get("/x")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_exhausts_retries_and_raises_timeout() -> None:
    client = _fast_client([
        httpx.ConnectTimeout("slow"),
        httpx.ReadTimeout("slow"),
        httpx.ConnectTimeout("slow"),
    ])
    with pytest.raises(IntegrationTimeoutError):
        await client.get("/x")


@pytest.mark.asyncio
async def test_exhausts_retries_on_persistent_5xx() -> None:
    client = _fast_client([httpx.Response(502) for _ in range(3)])
    with pytest.raises(IntegrationError) as exc:
        await client.get("/x")
    assert exc.value.status_code == 502


# ---------------------------------------------------------------------------
# 4xx behaviour.
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_4xx_is_not_retried() -> None:
    """A 400 on the first attempt is returned as-is; we must NOT loop."""
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(400, json={"error_code": "BAD_INPUT"})

    http = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    client = IntegrationClient(base_url="https://v.test", max_retries=5, http_client=http)

    r = await client.get("/x")
    assert r.status_code == 400
    assert calls["n"] == 1


@pytest.mark.asyncio
async def test_401_raises_auth_error() -> None:
    client = _fast_client([httpx.Response(401, text="unauthorized")])
    with pytest.raises(IntegrationAuthError) as exc:
        await client.get("/x")
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_403_raises_auth_error() -> None:
    client = _fast_client([httpx.Response(403, text="forbidden")])
    with pytest.raises(IntegrationAuthError):
        await client.get("/x")


@pytest.mark.asyncio
async def test_409_raises_conflict_error() -> None:
    client = _fast_client([httpx.Response(409, text="conflict")])
    with pytest.raises(IntegrationConflictError):
        await client.get("/x")


# ---------------------------------------------------------------------------
# Circuit breaker.
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_circuit_opens_after_threshold_consecutive_failures() -> None:
    # Threshold=3 in the fixture. Exhaust 3 attempts inside one call — but
    # each call has max_retries=2 (3 attempts total). One call → 3 fails →
    # breaker opens.
    client = _fast_client([
        httpx.ConnectTimeout("x"),
        httpx.ConnectTimeout("x"),
        httpx.ConnectTimeout("x"),
    ])
    with pytest.raises(IntegrationTimeoutError):
        await client.get("/x")
    assert client.breaker.state == CircuitState.OPEN


@pytest.mark.asyncio
async def test_open_circuit_short_circuits_immediately() -> None:
    # Open the breaker via 3 failures, then any subsequent call in the
    # recovery window raises CircuitOpenError.
    client = _fast_client([
        httpx.ConnectTimeout("x"),
        httpx.ConnectTimeout("x"),
        httpx.ConnectTimeout("x"),
    ])
    with pytest.raises(IntegrationTimeoutError):
        await client.get("/x")
    assert client.breaker.state == CircuitState.OPEN

    with pytest.raises(CircuitOpenError):
        await client.get("/x")


@pytest.mark.asyncio
async def test_breaker_recovers_after_cooldown_and_successful_probe() -> None:
    # Fail 3 times → OPEN. Wait cooldown. Next call becomes HALF_OPEN probe.
    # Success closes the breaker.
    responses = itertools.chain(
        [httpx.ConnectTimeout("x"), httpx.ConnectTimeout("x"), httpx.ConnectTimeout("x")],
        [httpx.Response(200, json={"ok": True})],
    )
    client = _fast_client(responses)

    with pytest.raises(IntegrationTimeoutError):
        await client.get("/x")
    assert client.breaker.state == CircuitState.OPEN

    # Sleep past the 50ms recovery window.
    await asyncio.sleep(0.08)
    r = await client.get("/x")
    assert r.status_code == 200
    assert client.breaker.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_breaker_success_resets_failure_counter() -> None:
    """Two failures then a success → counter back to 0."""
    client = _fast_client([
        httpx.ConnectTimeout("x"),
        httpx.Response(200, json={"ok": True}),
    ])
    r = await client.get("/x")
    assert r.status_code == 200
    assert client.breaker.consecutive_failures == 0


# ---------------------------------------------------------------------------
# CircuitBreaker primitive unit tests.
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_circuit_breaker_starts_closed() -> None:
    cb = CircuitBreaker(fail_threshold=3, recovery_seconds=1.0)
    assert await cb.allow() is True


@pytest.mark.asyncio
async def test_circuit_breaker_opens_on_threshold() -> None:
    cb = CircuitBreaker(fail_threshold=2, recovery_seconds=1.0)
    await cb.record_failure()
    assert cb.state == CircuitState.CLOSED
    await cb.record_failure()
    assert cb.state == CircuitState.OPEN


@pytest.mark.asyncio
async def test_circuit_breaker_half_open_after_recovery() -> None:
    cb = CircuitBreaker(fail_threshold=1, recovery_seconds=0.01)
    await cb.record_failure()
    assert cb.state == CircuitState.OPEN

    await asyncio.sleep(0.02)
    assert await cb.allow() is True
    assert cb.state == CircuitState.HALF_OPEN


@pytest.mark.asyncio
async def test_aclose_is_safe_on_externally_owned_client() -> None:
    http = httpx.AsyncClient()
    client = IntegrationClient(base_url="https://v.test", http_client=http)
    # aclose() must NOT close the externally-owned client.
    await client.aclose()
    assert not http.is_closed
    await http.aclose()
