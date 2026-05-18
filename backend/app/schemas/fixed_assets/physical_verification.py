"""Physical Verification schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import CamelSchema
from app.schemas.fixed_assets.common import FixedAssetsAuditSchema, OffsetPaginatedResponse


class VerificationScheduleCreate(CamelSchema):
    """Schema for creating a physical verification schedule."""

    schedule_name: str = Field(..., min_length=1, max_length=200)
    financial_year: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}$",
        description="Financial Year in YYYY-YY format",
    )
    location_id: Optional[UUID] = None
    category_ids: Optional[List[UUID]] = None
    scheduled_start_date: date
    scheduled_end_date: date
    assigned_to: Optional[UUID] = None
    team_members: Optional[List[UUID]] = None
    remarks: Optional[str] = Field(None, max_length=1000)
    organization_id: UUID


class VerificationScheduleUpdate(CamelSchema):
    """Schema for updating a physical verification schedule."""

    schedule_name: Optional[str] = Field(None, min_length=1, max_length=200)
    scheduled_start_date: Optional[date] = None
    scheduled_end_date: Optional[date] = None
    assigned_to: Optional[UUID] = None
    team_members: Optional[List[UUID]] = None
    remarks: Optional[str] = Field(None, max_length=1000)


class VerificationScheduleResponse(FixedAssetsAuditSchema):
    """Physical verification schedule response schema."""

    id: UUID
    organization_id: UUID
    schedule_reference: str
    schedule_name: str
    financial_year: str
    location_id: Optional[UUID] = None
    location_name: Optional[str] = None
    category_ids: Optional[List[UUID]] = None
    scheduled_start_date: date
    scheduled_end_date: date
    actual_start_date: Optional[date] = None
    actual_end_date: Optional[date] = None
    assigned_to: Optional[UUID] = None
    assigned_to_name: Optional[str] = None
    team_members: Optional[List[UUID]] = None
    total_assets: int
    verified_count: int
    found_count: int
    missing_count: int
    discrepancy_count: int
    total_value_verified: Decimal
    total_value_missing: Decimal
    status: str
    remarks: Optional[str] = None
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None


class VerificationEntryCreate(CamelSchema):
    """Schema for creating a verification entry result."""

    asset_id: UUID
    verification_date: date
    verification_result: str = Field(
        ...,
        description="FOUND, MISSING, MISPLACED, EXCESS",
    )
    asset_condition: Optional[str] = Field(
        None,
        description="GOOD, FAIR, POOR, DAMAGED, NOT_WORKING",
    )
    actual_location_id: Optional[UUID] = None
    actual_department_id: Optional[UUID] = None
    photo_urls: Optional[List[str]] = None
    barcode_scan: Optional[str] = Field(None, max_length=100)
    condition_notes: Optional[str] = Field(None, max_length=1000)
    remarks: Optional[str] = Field(None, max_length=500)


class VerificationEntryUpdate(CamelSchema):
    """Schema for updating a verification entry."""

    verification_result: Optional[str] = None
    asset_condition: Optional[str] = None
    actual_location_id: Optional[UUID] = None
    actual_department_id: Optional[UUID] = None
    photo_urls: Optional[List[str]] = None
    barcode_scan: Optional[str] = None
    condition_notes: Optional[str] = None
    remarks: Optional[str] = None


class VerificationEntryResponse(FixedAssetsAuditSchema):
    """Physical verification entry response schema."""

    id: UUID
    schedule_id: UUID
    asset_id: UUID
    asset_code: Optional[str] = None
    asset_name: Optional[str] = None
    category_name: Optional[str] = None
    expected_location_id: Optional[UUID] = None
    expected_location_name: Optional[str] = None
    expected_department_id: Optional[UUID] = None
    expected_department_name: Optional[str] = None
    verification_date: Optional[date] = None
    verified_by: Optional[UUID] = None
    verified_by_name: Optional[str] = None
    verification_result: Optional[str] = None
    asset_condition: Optional[str] = None
    actual_location_id: Optional[UUID] = None
    actual_location_name: Optional[str] = None
    actual_department_id: Optional[UUID] = None
    actual_department_name: Optional[str] = None
    book_value: Decimal
    photo_urls: Optional[List[str]] = None
    barcode_scan: Optional[str] = None
    condition_notes: Optional[str] = None
    remarks: Optional[str] = None


class DiscrepancyCreate(CamelSchema):
    """Schema for creating a discrepancy."""

    entry_id: UUID
    discrepancy_type: str = Field(
        ...,
        description="MISSING, LOCATION_MISMATCH, CONDITION_ISSUE, EXCESS",
    )
    description: str = Field(..., min_length=1, max_length=1000)
    value_impact: Decimal = Field(Decimal("0.00"), ge=0)
    remarks: Optional[str] = Field(None, max_length=500)


class DiscrepancyUpdate(CamelSchema):
    """Schema for updating a discrepancy."""

    status: Optional[str] = Field(
        None,
        description="OPEN, INVESTIGATING, RESOLVED, WRITTEN_OFF",
    )
    investigation_notes: Optional[str] = Field(None, max_length=1000)
    resolution: Optional[str] = Field(None, max_length=1000)
    remarks: Optional[str] = Field(None, max_length=500)


class DiscrepancyResponse(FixedAssetsAuditSchema):
    """Discrepancy response schema."""

    id: UUID
    entry_id: UUID
    asset_id: Optional[UUID] = None
    asset_code: Optional[str] = None
    asset_name: Optional[str] = None
    discrepancy_type: str
    description: str
    value_impact: Decimal
    status: str
    investigated_by: Optional[UUID] = None
    investigation_notes: Optional[str] = None
    resolution: Optional[str] = None
    resolved_by: Optional[UUID] = None
    resolved_at: Optional[datetime] = None
    remarks: Optional[str] = None


class VerificationSummaryResponse(CamelSchema):
    """Physical verification summary response."""

    organization_id: UUID
    financial_year: str
    total_schedules: int
    completed_schedules: int
    total_assets_to_verify: int
    total_assets_verified: int
    total_found: int
    total_missing: int
    total_discrepancies: int
    open_discrepancies: int
    total_value_verified: Decimal
    total_value_missing: Decimal
    verification_percentage: Decimal


class StartVerificationRequest(CamelSchema):
    """Request to start a verification schedule."""

    remarks: Optional[str] = Field(None, max_length=500)


class CompleteVerificationRequest(CamelSchema):
    """Request to complete a verification schedule."""

    remarks: Optional[str] = Field(None, max_length=500)


class BulkVerificationEntry(CamelSchema):
    """Single entry for bulk verification update."""

    asset_id: UUID
    verification_result: str
    asset_condition: Optional[str] = None
    actual_location_id: Optional[UUID] = None
    condition_notes: Optional[str] = None
    barcode_scan: Optional[str] = None


class BulkVerificationRequest(CamelSchema):
    """Request for bulk verification update."""

    verification_date: date
    entries: List[BulkVerificationEntry]


class VerificationScheduleListResponse(OffsetPaginatedResponse[VerificationScheduleResponse]):
    """Paginated verification-schedule response."""


class VerificationEntryListResponse(OffsetPaginatedResponse[VerificationEntryResponse]):
    """Paginated verification-entry response."""


class DiscrepancyListResponse(OffsetPaginatedResponse[DiscrepancyResponse]):
    """Paginated discrepancy response."""
