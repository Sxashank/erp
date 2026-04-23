"""Rate-limiting tests (CLAUDE.md §8.3).

Builds a minimal FastAPI app with slowapi wired exactly like `app.main`
and hits endpoints until the limit trips. Uses the same key function as
production so the test surface matches runtime.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.rate_limit import _key_func, rate_limit_exceeded_handler


def _fresh_app() -> FastAPI:
    """Every test gets a FRESH limiter so state doesn't leak across tests."""
    limiter = Limiter(key_func=_key_func)
    app = FastAPI()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    @app.post("/login")
    @limiter.limit("5/minute")
    async def login(request: Request) -> dict:
        return {"ok": True}

    @app.post("/refresh")
    @limiter.limit("20/minute")
    async def refresh(request: Request) -> dict:
        return {"ok": True}

    return app


@pytest.mark.asyncio
async def test_login_limit_allows_up_to_five_requests() -> None:
    app = _fresh_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        responses = [await client.post("/login") for _ in range(5)]
    for r in responses:
        assert r.status_code == 200


@pytest.mark.asyncio
async def test_login_limit_blocks_sixth_request() -> None:
    app = _fresh_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for _ in range(5):
            await client.post("/login")
        r = await client.post("/login")
    assert r.status_code == 429
    assert r.json()["error_code"] == "RATE_LIMIT_EXCEEDED"
    assert "retry_after" in r.headers["retry-after"].lower() or r.headers["retry-after"].isdigit()


@pytest.mark.asyncio
async def test_refresh_has_higher_limit() -> None:
    """/refresh allows 20/min vs login's 5/min — should not 429 on the 6th."""
    app = _fresh_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for _ in range(6):
            r = await client.post("/refresh")
            assert r.status_code == 200


@pytest.mark.asyncio
async def test_limit_is_per_ip_via_xff_header() -> None:
    """Two different X-Forwarded-For sources are counted independently."""
    app = _fresh_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # IP A exhausts its budget.
        for _ in range(5):
            r = await client.post("/login", headers={"X-Forwarded-For": "10.0.0.1"})
            assert r.status_code == 200
        blocked = await client.post("/login", headers={"X-Forwarded-For": "10.0.0.1"})
        assert blocked.status_code == 429

        # IP B has its own budget.
        r = await client.post("/login", headers={"X-Forwarded-For": "10.0.0.2"})
        assert r.status_code == 200


@pytest.mark.asyncio
async def test_429_response_envelope_has_error_code_and_retry_after() -> None:
    app = _fresh_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for _ in range(5):
            await client.post("/login")
        r = await client.post("/login")
    body = r.json()
    assert body["error_code"] == "RATE_LIMIT_EXCEEDED"
    assert "Too many requests" in body["message"]
    assert "retry_after_seconds" in body
    assert isinstance(body["retry_after_seconds"], int)
