"""Base model classes with audit trail support."""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, declared_attr

from app.database import Base


class AuditMixin:
    """Mixin for audit trail fields."""

    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        )

    @declared_attr
    def created_by(cls) -> Mapped[Optional[UUID]]:
        return mapped_column(
            PGUUID(as_uuid=True),
            ForeignKey("mst_user.id", ondelete="SET NULL"),
            nullable=True,
        )

    @declared_attr
    def updated_at(cls) -> Mapped[Optional[datetime]]:
        return mapped_column(
            DateTime(timezone=True),
            onupdate=func.now(),
            nullable=True,
        )

    @declared_attr
    def updated_by(cls) -> Mapped[Optional[UUID]]:
        return mapped_column(
            PGUUID(as_uuid=True),
            ForeignKey("mst_user.id", ondelete="SET NULL"),
            nullable=True,
        )


class SoftDeleteMixin:
    """Mixin for soft delete functionality."""

    @declared_attr
    def deleted_at(cls) -> Mapped[Optional[datetime]]:
        return mapped_column(
            DateTime(timezone=True),
            nullable=True,
        )

    @declared_attr
    def deleted_by(cls) -> Mapped[Optional[UUID]]:
        return mapped_column(
            PGUUID(as_uuid=True),
            ForeignKey("mst_user.id", ondelete="SET NULL"),
            nullable=True,
        )

    @declared_attr
    def is_active(cls) -> Mapped[bool]:
        return mapped_column(
            Boolean,
            default=True,
            nullable=False,
        )

    def soft_delete(self, deleted_by: Optional[UUID] = None) -> None:
        """Mark record as deleted."""
        from datetime import timezone
        self.deleted_at = datetime.now(timezone.utc)
        self.deleted_by = deleted_by
        self.is_active = False

    def restore(self) -> None:
        """Restore soft-deleted record."""
        self.deleted_at = None
        self.deleted_by = None
        self.is_active = True


class VersionedMixin:
    """Mixin for optimistic locking via version field.

    This provides concurrency control by tracking record versions.
    When updating a record, the version must match the expected version,
    otherwise a ConcurrencyConflictError should be raised.
    """

    @declared_attr
    def version(cls) -> Mapped[int]:
        return mapped_column(
            Integer,
            default=1,
            nullable=False,
            comment="Record version for optimistic locking",
        )


class BaseModel(Base, AuditMixin, SoftDeleteMixin, VersionedMixin):
    """Base model with UUID primary key and audit fields."""

    __abstract__ = True

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id})>"


class TimestampMixin:
    """Simple timestamp mixin without user tracking."""

    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        )

    @declared_attr
    def updated_at(cls) -> Mapped[Optional[datetime]]:
        return mapped_column(
            DateTime(timezone=True),
            onupdate=func.now(),
            nullable=True,
        )
