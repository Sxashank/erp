"""Database connection and session management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DB_ECHO,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,
)

# Create async session factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database session (for use outside of FastAPI)."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database (create tables)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()


async def set_tenant_context(session: AsyncSession, organization_id: UUID) -> None:
    """Set the current organization context for Row-Level Security policies.

    This function sets a PostgreSQL session variable that RLS policies use
    to filter data by organization. The SET LOCAL ensures the setting only
    applies to the current transaction.

    Args:
        session: The database session to set context on
        organization_id: The organization UUID to use for RLS filtering
    """
    # PostgreSQL's SET LOCAL does not accept parameter bindings, so we must
    # construct the statement from the string form — but only after validating
    # that the input is a real UUID. The `UUID` type coercion on the argument
    # (enforced by the annotation + explicit constructor below) guarantees the
    # value cannot carry SQL payloads. Do NOT relax this validation.
    org_id = UUID(str(organization_id))
    await session.execute(
        text("SELECT set_config('app.current_org_id', :org_id, true)").bindparams(
            org_id=str(org_id),
        )
    )


async def clear_tenant_context(session: AsyncSession) -> None:
    """Clear the tenant context for the current session.

    This resets the RLS context variable to empty, useful when operating
    as a superuser or when context should be cleared.
    """
    await session.execute(
        text("SELECT set_config('app.current_org_id', '', true)")
    )
