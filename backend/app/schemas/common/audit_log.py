"""Audit Log schemas for API request/response validation."""

from datetime import datetime, date
from typing import Optional, List, Any
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, PaginatedResponse


class LineItemHistoryResponse(BaseSchema):
    """Response schema for line item history."""

    id: UUID
    parent_audit_id: UUID
    entity_type: str
    line_id: UUID
    line_number: int
    action: str
    old_values: Optional[dict] = None
    new_values: Optional[dict] = None
    created_at: datetime


class AuditLogResponse(BaseSchema):
    """Response schema for audit log entry."""

    id: UUID
    organization_id: UUID
    entity_type: str
    entity_id: UUID
    entity_reference: Optional[str] = None
    action: str
    changed_by: UUID
    changed_by_name: Optional[str] = None  # Populated via join
    changed_at: datetime
    old_values: Optional[dict] = None
    new_values: Optional[dict] = None
    changed_fields: Optional[List[str]] = None
    change_reason: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    line_item_changes: Optional[List[LineItemHistoryResponse]] = None


class AuditLogListResponse(PaginatedResponse[AuditLogResponse]):
    """Paginated list of audit log entries."""
    pass


class AuditLogFilter(BaseSchema):
    """Filter parameters for audit log queries."""

    organization_id: Optional[UUID] = None
    entity_type: Optional[str] = None
    entity_id: Optional[UUID] = None
    action: Optional[str] = None
    changed_by: Optional[UUID] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    search: Optional[str] = Field(
        None,
        description="Search in entity_reference and change_reason"
    )


class EntityHistoryResponse(BaseSchema):
    """Complete history for a specific entity."""

    entity_type: str
    entity_id: UUID
    entity_reference: Optional[str] = None
    total_changes: int
    first_created: datetime
    last_modified: datetime
    history: List[AuditLogResponse]


class AuditLogCreate(BaseSchema):
    """Internal schema for creating audit log entries (not exposed via API)."""

    organization_id: UUID
    entity_type: str
    entity_id: UUID
    entity_reference: Optional[str] = None
    action: str
    changed_by: UUID
    old_values: Optional[dict] = None
    new_values: Optional[dict] = None
    changed_fields: Optional[List[str]] = None
    change_reason: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class LineItemHistoryCreate(BaseSchema):
    """Internal schema for creating line item history entries."""

    parent_audit_id: UUID
    entity_type: str
    line_id: UUID
    line_number: int
    action: str
    old_values: Optional[dict] = None
    new_values: Optional[dict] = None
