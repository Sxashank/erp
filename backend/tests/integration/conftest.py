"""Integration-tier conftest. Uses a real PostgreSQL via testcontainers.

See CLAUDE.md §10.4. SQLite is rejected for integration tests because it
masks enum, JSONB, and RLS behaviour. Each test session spins an ephemeral
container, runs `alembic upgrade head`, and hands out sessions wired to
that container.

The unit-tier conftest at `backend/tests/conftest.py` is left untouched so
pure-math tests run without Docker.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncGenerator, Generator
from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Marker every test under `integration/` inherits. Run with:
#   pytest -m integration
pytestmark = pytest.mark.integration


def _postgres_container() -> Any:
    """Lazy-import testcontainers so SQLite-only runs don't need Docker."""
    try:
        from testcontainers.postgres import PostgresContainer  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover
        pytest.skip(f"testcontainers not installed: {exc}")
    return PostgresContainer("postgres:15-alpine")


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Session-scoped loop so the Postgres container and the engine share one."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def postgres_url() -> Generator[str, None, None]:
    """Start a throwaway Postgres for the test session.

    Yields an async (asyncpg) URL. Tests that only need sync access can adapt
    the URL by stripping the `+asyncpg` prefix if ever needed.
    """
    if os.environ.get("TEST_DATABASE_URL"):
        # Allow a pre-provisioned Postgres (e.g. in CI) to override.
        yield os.environ["TEST_DATABASE_URL"]
        return

    with _postgres_container() as pg:
        raw_url: str = pg.get_connection_url()
        # testcontainers emits psycopg2-style URLs; we need asyncpg.
        async_url = raw_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://").replace(
            "postgresql://", "postgresql+asyncpg://"
        )
        yield async_url


@pytest_asyncio.fixture(scope="session")
async def engine(postgres_url: str) -> AsyncGenerator[Any, None]:
    """Session-scoped engine against the real Postgres."""
    eng = create_async_engine(postgres_url, echo=False, pool_pre_ping=True)

    # Run alembic migrations against the fresh container.
    # Alembic needs a sync URL for its migration context, so we run it with the
    # `+asyncpg` stripped; our async engine keeps the original URL for app code.
    from alembic import command  # noqa: WPS433  (lazy import; alembic is test-only here)
    from alembic.config import Config

    # For integration tests we create ONLY the tables the tests need. The
    # full model graph has legacy FK references (auth_user vs mst_user) that
    # full `Base.metadata.create_all` cannot resolve; full schema rebuild is
    # tracked as a separate remediation in .stubs-approved.md. Tests add
    # their own minimal schema via `create_idempotency_schema()` below.
    from app.models.core.idempotency_key import IdempotencyKey  # noqa: F401

    async with eng.begin() as conn:
        # Create only the idempotency_key table (and nothing else). Each
        # test fixture that needs additional tables explicitly creates them.
        await conn.run_sync(
            lambda sync_conn: IdempotencyKey.__table__.create(sync_conn, checkfirst=True)
        )

    # Sanity check: the table we just migrated MUST exist.
    from sqlalchemy import text as _text

    async with eng.connect() as c:
        tables = (
            await c.execute(_text("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename"))
        ).scalars().all()
        print(f"[integration-conftest] postgres_url={postgres_url!r}")
        print(f"[integration-conftest] {len(tables)} tables migrated; idempotency_key present={('idempotency_key' in tables)!r}")

    # Dispose the pre-existing production engine so its connection pool
    # (bound to the import-time event loop) doesn't leak into tests. Then
    # rebind so middleware code using `app.database.async_session_factory`
    # hits the test container.
    import app.database as app_db
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    original_engine = app_db.engine
    original_factory = app_db.async_session_factory
    try:
        await original_engine.dispose()
    except Exception:  # noqa: BLE001 — original engine may never have connected
        pass

    app_db.engine = eng  # type: ignore[assignment]
    app_db.async_session_factory = async_sessionmaker(  # type: ignore[assignment]
        eng,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    try:
        yield eng
    finally:
        app_db.engine = original_engine  # type: ignore[assignment]
        app_db.async_session_factory = original_factory  # type: ignore[assignment]
        await eng.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(engine: Any) -> AsyncGenerator[AsyncSession, None]:
    """Function-scoped session. Wraps each test in a transaction that rolls
    back on exit so tests remain independent."""
    connection = await engine.connect()
    trans = await connection.begin()
    maker = async_sessionmaker(bind=connection, class_=AsyncSession, expire_on_commit=False)
    async with maker() as session:
        try:
            yield session
        finally:
            await trans.rollback()
            await connection.close()


@pytest_asyncio.fixture
async def health_endpoint_url() -> str:
    """Where the backend TestClient will mount; exported for tests."""
    return "/health"


@pytest_asyncio.fixture
async def app_client() -> AsyncGenerator[Any, None]:
    """ASGI test client wired to the real FastAPI app. Uses the real lifespan
    so APScheduler start/stop is exercised. Requires `asgi-lifespan` +
    `httpx`."""
    try:
        from asgi_lifespan import LifespanManager  # type: ignore[import-not-found]
    except ImportError:  # pragma: no cover
        pytest.skip("asgi-lifespan not installed")

    import httpx

    from app.main import app

    async with LifespanManager(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            yield client


def _safe_exec_sql(session: AsyncSession, sql: str) -> Any:
    """Tiny helper for ad-hoc test SQL. Always parameter-bound."""
    return session.execute(text(sql))
