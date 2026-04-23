"""Base Pydantic schemas and utilities."""

from datetime import datetime
from typing import Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
    )


class TimestampSchema(BaseSchema):
    """Schema with timestamp fields."""

    created_at: datetime
    updated_at: Optional[datetime] = None


class AuditSchema(TimestampSchema):
    """Schema with full audit fields."""

    created_by: Optional[UUID] = None
    updated_by: Optional[UUID] = None
    is_active: bool = True
    version: int = 1


class VersionedUpdateSchema(BaseSchema):
    """Base schema for updates with optimistic locking.

    Include this in update schemas that require concurrent modification detection.
    """

    version: int = Field(
        ...,
        description="Current record version for optimistic locking. "
        "If the version doesn't match, the update will be rejected.",
    )


class IDSchema(BaseSchema):
    """Schema with ID field."""

    id: UUID


class PaginationParams(BaseSchema):
    """Pagination parameters."""

    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.page_size


class SortParams(BaseSchema):
    """Sort parameters."""

    sort_by: str = "created_at"
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


T = TypeVar("T")


class PaginatedResponse(BaseSchema, Generic[T]):
    """Paginated response wrapper."""

    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        """Create paginated response."""
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


class MessageResponse(BaseSchema):
    """Simple message response."""

    message: str
    success: bool = True
    data: Optional[dict] = None
