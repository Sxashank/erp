"""Bulk operations schemas for Fixed Assets."""

from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema
from app.core.constants import AssetDisposalType


class BulkAssetRow(BaseSchema):
    """Single asset row for bulk import."""

    asset_name: str = Field(..., min_length=1, max_length=200)
    category_id: UUID
    acquisition_date: date
    acquisition_cost: Decimal = Field(..., ge=0)
    description: Optional[str] = Field(None, max_length=1000)
    location_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    custodian_employee_id: Optional[UUID] = None
    put_to_use_date: Optional[date] = None
    vendor_id: Optional[UUID] = None
    invoice_number: Optional[str] = Field(None, max_length=50)
    invoice_date: Optional[date] = None
    installation_cost: Decimal = Field(Decimal("0.00"), ge=0)
    other_costs: Decimal = Field(Decimal("0.00"), ge=0)
    residual_value: Optional[Decimal] = Field(None, ge=0)
    useful_life_months: Optional[int] = Field(None, ge=1)
    make: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    quantity: int = Field(1, ge=1)


class BulkAssetImportRequest(BaseSchema):
    """Request for bulk asset import."""

    organization_id: UUID
    assets: List[BulkAssetRow] = Field(..., min_length=1, max_length=500)
    validation_only: bool = Field(
        False,
        description="If true, only validate without creating assets",
    )
    auto_capitalize: bool = Field(
        False,
        description="If true, capitalize assets after creation",
    )


class BulkImportError(BaseSchema):
    """Error details for a single row."""

    row: int
    field: Optional[str] = None
    error: str


class BulkAssetImportResponse(BaseSchema):
    """Response for bulk asset import."""

    total: int
    successful: int
    failed: int
    validation_only: bool
    errors: List[BulkImportError]
    created_asset_ids: List[UUID]


class BulkAssetUpdateRow(BaseSchema):
    """Single row for bulk asset update."""

    asset_id: UUID
    version: int = Field(..., description="Current version for optimistic locking")
    asset_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    location_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    custodian_employee_id: Optional[UUID] = None
    make: Optional[str] = Field(None, max_length=100)
    model: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)


class BulkAssetUpdateRequest(BaseSchema):
    """Request for bulk asset update."""

    organization_id: UUID
    assets: List[BulkAssetUpdateRow] = Field(..., min_length=1, max_length=200)
    validation_only: bool = False


class BulkAssetUpdateResponse(BaseSchema):
    """Response for bulk asset update."""

    total: int
    successful: int
    failed: int
    errors: List[BulkImportError]
    updated_asset_ids: List[UUID]


class BulkTransferRow(BaseSchema):
    """Single row for bulk transfer."""

    asset_id: UUID
    to_location_id: Optional[UUID] = None
    to_department_id: Optional[UUID] = None
    to_custodian_id: Optional[UUID] = None
    reason: Optional[str] = Field(None, max_length=500)


class BulkTransferRequest(BaseSchema):
    """Request for bulk asset transfer."""

    organization_id: UUID
    transfer_date: date
    assets: List[BulkTransferRow] = Field(..., min_length=1, max_length=200)
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Common reason for all transfers (overrides individual reasons)",
    )


class BulkTransferResponse(BaseSchema):
    """Response for bulk transfer."""

    total: int
    successful: int
    failed: int
    errors: List[BulkImportError]
    transfer_ids: List[UUID]


class BulkDisposeRow(BaseSchema):
    """Single row for bulk disposal."""

    asset_id: UUID
    disposal_type: AssetDisposalType
    disposal_value: Decimal = Field(Decimal("0.00"), ge=0)
    disposal_remarks: Optional[str] = Field(None, max_length=500)


class BulkDisposeRequest(BaseSchema):
    """Request for bulk asset disposal."""

    organization_id: UUID
    disposal_date: date
    assets: List[BulkDisposeRow] = Field(..., min_length=1, max_length=200)
    common_disposal_type: Optional[AssetDisposalType] = Field(
        None,
        description="If set, overrides individual disposal types",
    )


class BulkDisposeResponse(BaseSchema):
    """Response for bulk disposal."""

    total: int
    successful: int
    failed: int
    errors: List[BulkImportError]
    disposed_asset_ids: List[UUID]


class ExportFilters(BaseSchema):
    """Filters for asset export."""

    organization_id: UUID
    category_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    department_id: Optional[UUID] = None
    status: Optional[str] = None
    acquisition_date_from: Optional[date] = None
    acquisition_date_to: Optional[date] = None
    include_disposed: bool = False


class ExportResponse(BaseSchema):
    """Response for export request."""

    job_id: UUID
    status: str
    total_records: int
    file_url: Optional[str] = None
