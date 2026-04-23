"""Optimistic locking utilities for concurrent modification detection."""

from typing import Any, Dict, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.core.exceptions import ConcurrentModificationError

T = TypeVar("T", bound=DeclarativeBase)


async def optimistic_update(
    session: AsyncSession,
    model_class: Type[T],
    record_id: UUID,
    expected_version: int,
    update_data: Dict[str, Any],
    updated_by: Optional[UUID] = None,
) -> int:
    """
    Perform an optimistic locking update.

    This function updates a record only if the current version matches
    the expected version, preventing lost updates in concurrent scenarios.

    Args:
        session: The database session
        model_class: The SQLAlchemy model class
        record_id: The UUID of the record to update
        expected_version: The version the record should currently have
        update_data: Dictionary of field-value pairs to update
        updated_by: Optional UUID of the user performing the update

    Returns:
        The new version number after update

    Raises:
        ConcurrentModificationError: If the record was modified by another user
    """
    new_version = expected_version + 1

    # Add version and audit info to update data
    update_data["version"] = new_version
    if updated_by is not None:
        update_data["updated_by"] = updated_by

    # Build and execute update with version check
    stmt = (
        update(model_class)
        .where(
            model_class.id == record_id,
            model_class.version == expected_version,
        )
        .values(**update_data)
    )

    result = await session.execute(stmt)

    if result.rowcount == 0:
        raise ConcurrentModificationError(
            f"{model_class.__name__} was modified by another user. "
            "Please refresh and try again."
        )

    return new_version


async def check_version(
    session: AsyncSession,
    model_class: Type[T],
    record_id: UUID,
    expected_version: int,
) -> bool:
    """
    Check if a record's version matches the expected version.

    Args:
        session: The database session
        model_class: The SQLAlchemy model class
        record_id: The UUID of the record to check
        expected_version: The version to check against

    Returns:
        True if version matches, False otherwise
    """
    from sqlalchemy import select

    stmt = select(model_class.version).where(model_class.id == record_id)
    result = await session.execute(stmt)
    current_version = result.scalar_one_or_none()

    return current_version == expected_version


def increment_version(record: T) -> None:
    """
    Increment the version of a record in-memory.

    Use this when updating a record directly through the ORM
    rather than using optimistic_update.

    Args:
        record: The record to increment version for
    """
    if hasattr(record, "version"):
        record.version = (record.version or 0) + 1
