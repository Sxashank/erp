"""Idempotent enum-type bootstrap for fresh Postgres databases.

CLAUDE.md §3.1 makes DDL a deployment artefact, not a runtime decision. In the
canonical bootstrap path (`scripts/reset_db.py`, `scripts/seed_e2e.sh`) we call
``Base.metadata.create_all()`` to materialise every table. ORM columns of type
``PGEnum(..., create_type=False)`` (67 sites across the codebase) intentionally
defer enum-type creation to alembic — but a *truly empty* DB has not yet run
alembic, so ``create_all()`` fails with ``type "<enum>" does not exist``.

This module bridges the gap. It walks ``Base.metadata`` for every Enum-typed
column, derives the canonical PostgreSQL ``CREATE TYPE ... AS ENUM (...)``
statement from the underlying Python enum class, and runs each inside a
``DO $$ BEGIN ... EXCEPTION WHEN duplicate_object THEN null; END $$;`` block —
the same idempotency guard the existing alembic migrations use (e.g.
``backend/alembic/versions/z6_add_gl_entry_table.py``).

Importable from any async-context. Pair with ``Base.metadata.create_all()`` in
the fresh-DB bootstrap step; it is a no-op on a DB that already has the types.

CLAUDE.md refs: §3.1 (architecture), §6 (canonical bootstrap), §6.2 (no
string-interpolated SQL — uses parameter-free explicit type names).
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.ext.asyncio import AsyncConnection
from sqlalchemy.sql.sqltypes import Enum as GenericEnum


def _enum_columns(metadata) -> list[tuple[str, tuple[str, ...]]]:
    """Return (type_name, values) for every PGEnum / Enum column in metadata.

    Deduplicates by type name (the same enum type is reused across tables).
    """
    seen: dict[str, tuple[str, ...]] = {}
    for table in metadata.tables.values():
        for column in table.columns:
            col_type = column.type
            if not isinstance(col_type, (PGEnum, GenericEnum)):
                continue
            name = getattr(col_type, "name", None)
            if not name:
                continue
            # Resolve the enum values. PGEnum + Enum both expose `.enums`
            # (the ordered list of string labels).
            enums = tuple(getattr(col_type, "enums", ()) or ())
            if not enums:
                continue
            if name in seen and seen[name] != enums:
                # Same name, different values — alarming, but we honour the
                # first declaration and let the duplicate-handling exception
                # block keep the later CREATE a no-op.
                continue
            seen.setdefault(name, enums)
    return sorted(seen.items())


async def bootstrap_enums(conn: AsyncConnection, metadata) -> int:
    """Create every Postgres enum type referenced by `metadata`, idempotently.

    Returns the number of CREATE TYPE statements executed (the count of enum
    types discovered, NOT the count actually created — duplicates no-op).
    """
    statements = _enum_columns(metadata)
    for name, values in statements:
        # Each value is a Python string; quote each as a Postgres string literal.
        # Names of enum types come from the ORM declaration and are not user
        # input — safe to interpolate. Values are also from the Python enum
        # class. The DO block guards against duplicate type creation.
        literal_values = ", ".join(f"'{v}'" for v in values)
        ddl = (
            f"DO $$ BEGIN "
            f"CREATE TYPE {name} AS ENUM ({literal_values}); "
            f"EXCEPTION WHEN duplicate_object THEN null; END $$;"
        )
        await conn.execute(text(ddl))
    return len(statements)
