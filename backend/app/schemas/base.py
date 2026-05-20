"""Base Pydantic schemas and utilities."""

from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class BaseSchema(BaseModel):
    """Base schema with common API configuration.

    Python fields stay snake_case inside backend code. Any schema returned to
    frontend clients must be serialized by FastAPI with
    ``response_model_by_alias=True``, which emits camelCase aliases from this
    shared base. Keeping the alias generator here prevents older schemas from
    leaking snake_case just because they inherited ``BaseSchema`` instead of a
    newer domain-specific response class.
    """

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        alias_generator=to_camel,
        str_strip_whitespace=True,
    )


class CamelSchema(BaseSchema):
    """Compatibility alias for schemas that explicitly document camelCase I/O.

    ``BaseSchema`` now owns the same alias contract, so this class remains as a
    semantic marker for modules already migrated to explicit camelCase schemas.
    """


class TimestampSchema(BaseSchema):
    """Schema with timestamp fields."""

    created_at: datetime
    updated_at: datetime | None = None


class AuditSchema(TimestampSchema):
    """Schema with full audit fields."""

    created_by: UUID | None = None
    updated_by: UUID | None = None
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
    """Paginated response wrapper.

    Supports both pagination idioms in the codebase:
      - skip/limit (CLAUDE.md §6.5 canonical; used by HRIS, payroll, etc.)
      - page/page_size (legacy; used by GST and a handful of others)

    Both are emitted on the wire so the FE can pick either shape; callers
    construct with the idiom they natively work in.  `total_pages` is
    derived from the limit (or page_size, whichever was supplied).
    """

    items: list[T]
    total: int
    # `skip`/`limit` idiom (CLAUDE.md §6.5).
    skip: int = 0
    limit: int = 0
    # `page`/`page_size`/`total_pages` idiom (legacy).
    page: int = 1
    page_size: int = 0
    total_pages: int = 0

    def model_post_init(self, __context: object) -> None:  # noqa: D401
        """Backfill the missing pagination idiom from whichever was provided."""
        # If the caller passed skip/limit (the §6.5 canonical idiom), derive
        # page/page_size/total_pages from it. If they passed page/page_size,
        # derive skip/limit.
        if self.limit and not self.page_size:
            object.__setattr__(self, "page_size", self.limit)
            object.__setattr__(self, "page", (self.skip // self.limit) + 1)
        if self.page_size and not self.limit:
            object.__setattr__(self, "limit", self.page_size)
            object.__setattr__(self, "skip", (self.page - 1) * self.page_size)
        page_size = self.page_size or self.limit
        if page_size and not self.total_pages:
            object.__setattr__(
                self, "total_pages", (self.total + page_size - 1) // page_size
            )

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        """Create paginated response from page/page_size (legacy callers)."""
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )


class MessageResponse(BaseSchema):
    """Simple message response."""

    message: str
    success: bool = True
    data: dict | None = None
