"""Shared schema helpers for fixed-assets frontend APIs."""

from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from app.schemas.base import CamelSchema


class FixedAssetsAuditSchema(CamelSchema):
    """CamelCase audit fields for fixed-assets responses."""

    created_at: datetime
    updated_at: datetime | None = None
    created_by: UUID | None = None
    updated_by: UUID | None = None
    is_active: bool = True
    version: int = 1


T = TypeVar("T")


class OffsetPaginatedResponse(CamelSchema, Generic[T]):
    """Offset-based paginated response used by fixed-assets list APIs."""

    items: list[T]
    total: int
    skip: int
    limit: int
