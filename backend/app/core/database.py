"""Database session dependency re-exports for backward compatibility."""

from app.database import (
    get_db,
    get_db_context,
    async_session_factory,
    engine,
    Base,
    set_tenant_context,
    clear_tenant_context,
)

# Alias for backward compatibility
get_session = get_db

__all__ = [
    "get_db",
    "get_session",
    "get_db_context",
    "async_session_factory",
    "engine",
    "Base",
    "set_tenant_context",
    "clear_tenant_context",
]
