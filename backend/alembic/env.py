"""Alembic migration environment configuration."""

import asyncio
from logging.config import fileConfig

import sqlalchemy as sa
from sqlalchemy import pool, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# Import all models to ensure they're registered with Base.metadata
# This imports all models including Legal and Portal modules
import app.models  # noqa: F401
from alembic import context

# Import settings and models
from app.config import settings
from app.database import Base

# Alembic Config object
config = context.config

# Set the database URL from settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with the given connection."""
    # Alembic's default `version_num VARCHAR(32)` is too short for this
    # repository's descriptive revision identifiers (for example
    # `zza2_add_scheme_portal_dms_linkage`). Widen it before running any
    # migration so fresh and existing databases can advance safely.
    # `version_table_pk_type` propagates the same width to the CREATE TABLE
    # path that `alembic stamp head` takes on a brand-new DB — without it,
    # stamp creates the table at the alembic default (VARCHAR(32)) and the
    # insert of the head revision id then fails.
    connection.execute(
        text("ALTER TABLE IF EXISTS alembic_version ALTER COLUMN version_num TYPE VARCHAR(128)")
    )
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        version_table_pk_type=sa.String(128),
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.begin() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
