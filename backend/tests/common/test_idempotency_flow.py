"""End-to-end flow tests for IdempotencyMiddleware.

Exercises the middleware against a minimal FastAPI app. Uses an in-memory
SQLite store (via monkeypatch of app.database.async_session_factory) so the
test does not require Docker, does not share event loops between tests,
and can assert full request/response behaviour.

See CLAUDE.md §6.3 and §10.3.
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app import database as app_database
from app.middleware.idempotency import IdempotencyMiddleware
from app.models.core.idempotency_key import IdempotencyKey

# Importing app.main forces the full SQLAlchemy model registry to resolve,
# which is required because the first DB query triggers mapper configuration
# and some relationships (LegalCase, etc.) reference classes that only
# register when their module is imported.
import app.main  # noqa: F401, E402


@pytest_asyncio.fixture
async def idempotency_engine(monkeypatch):
    """Spin a SQLite engine for the idempotency_key table only.

    Rebinds `app.database.async_session_factory` so the middleware picks
    this engine up via its lazy lookup. Function-scoped so every test gets
    a fresh DB on its own event loop — this prevents the 'Future attached
    to a different loop' failure we hit trying to share a postgres engine
    across tests.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(IdempotencyKey.__table__.create)

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    monkeypatch.setattr(app_database, "async_session_factory", factory)

    try:
        yield engine
    finally:
        await engine.dispose()


def _build_app() -> tuple[FastAPI, dict[str, int]]:
    """Minimal FastAPI app with the idempotency middleware + a counter endpoint."""
    app = FastAPI()
    app.add_middleware(IdempotencyMiddleware)

    counter: dict[str, int] = {"calls": 0}

    @app.post("/api/v1/vouchers")
    async def create_voucher(body: dict) -> dict:
        counter["calls"] += 1
        return {"id": f"v-{counter['calls']}", "echo": body, "calls": counter["calls"]}

    @app.get("/api/v1/vouchers/ping")
    async def ping() -> dict:
        return {"ok": True}

    return app, counter


@pytest.mark.asyncio
async def test_idempotency_key_required(idempotency_engine):  # noqa: ARG001
    """POST on a mutating path without the header is rejected."""
    app, _ = _build_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/api/v1/vouchers", json={"amount": 100})
    assert r.status_code == 400
    assert r.json()["error_code"] == "IDEMPOTENCY_KEY_REQUIRED"


@pytest.mark.asyncio
async def test_idempotency_short_key_rejected(idempotency_engine):  # noqa: ARG001
    app, _ = _build_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/v1/vouchers",
            json={"amount": 100},
            headers={"Idempotency-Key": "short"},
        )
    assert r.status_code == 400
    assert r.json()["error_code"] == "IDEMPOTENCY_KEY_INVALID"


@pytest.mark.asyncio
async def test_idempotency_replay_returns_cached_response(idempotency_engine):  # noqa: ARG001
    """Same key + same body → handler runs ONCE; second call replays cache."""
    app, counter = _build_app()
    transport = ASGITransport(app=app)
    headers = {"Idempotency-Key": "idem-0001-same-body"}
    body = {"amount": 100, "narration": "test"}

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r1 = await client.post("/api/v1/vouchers", json=body, headers=headers)
        r2 = await client.post("/api/v1/vouchers", json=body, headers=headers)

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json() == r2.json()
    assert counter["calls"] == 1, "handler must run exactly once on retry"


@pytest.mark.asyncio
async def test_idempotency_reuse_with_different_body_rejected(idempotency_engine):  # noqa: ARG001
    """Same key with different body → 422."""
    app, _ = _build_app()
    transport = ASGITransport(app=app)
    headers = {"Idempotency-Key": "idem-0002-diff-body"}

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r1 = await client.post("/api/v1/vouchers", json={"amount": 100}, headers=headers)
        r2 = await client.post("/api/v1/vouchers", json={"amount": 999}, headers=headers)

    assert r1.status_code == 200
    assert r2.status_code == 422
    assert r2.json()["error_code"] == "IDEMPOTENCY_KEY_REUSED"


@pytest.mark.asyncio
async def test_idempotency_ignored_on_non_mutating_path(idempotency_engine):  # noqa: ARG001
    """GET endpoints are never gated."""
    app, _ = _build_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/api/v1/vouchers/ping")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_idempotency_cache_survives_whitespace_difference(idempotency_engine):  # noqa: ARG001
    """Equivalent-but-reformatted JSON hashes the same → same cache hit."""
    app, counter = _build_app()
    transport = ASGITransport(app=app)
    headers = {"Idempotency-Key": "idem-0003-same-json"}

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r1 = await client.post(
            "/api/v1/vouchers",
            json={"amount": 100, "narration": "x"},
            headers=headers,
        )
        # Different field order, same logical payload.
        r2 = await client.post(
            "/api/v1/vouchers",
            json={"narration": "x", "amount": 100},
            headers=headers,
        )

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert counter["calls"] == 1


@pytest.mark.asyncio
async def test_idempotency_not_required_on_non_financial_mutation(idempotency_engine):  # noqa: ARG001
    """POST to a non-financial resource (e.g. /organizations) does NOT require a key."""
    app = FastAPI()
    app.add_middleware(IdempotencyMiddleware)

    @app.post("/api/v1/organizations")
    async def create_org(body: dict) -> dict:
        return {"id": "org-1", **body}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/api/v1/organizations", json={"name": "Test"})

    assert r.status_code == 200
    assert r.json()["name"] == "Test"
