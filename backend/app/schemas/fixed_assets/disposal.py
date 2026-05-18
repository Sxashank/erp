"""Schemas for the fixed-assets disposal register and actions."""

from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional
from uuid import UUID

from pydantic import Field

from app.core.constants import ApprovalRequestStatus, AssetDisposalType
from app.schemas.base import CamelSchema
from app.schemas.fixed_assets.common import OffsetPaginatedResponse
from app.schemas.fixed_assets.fixed_asset import AssetDisposeRequest, FixedAssetResponse


class DisposalRegisterItem(CamelSchema):
    """Disposal register row sourced from assets plus approval metadata."""

    asset_id: UUID
    organization_id: UUID
    asset_code: str
    asset_name: str
    category_id: UUID
    category_name: Optional[str] = None
    disposal_type: Optional[AssetDisposalType] = None
    disposal_date: Optional[date] = None
    request_date: Optional[datetime] = None
    requested_by: Optional[UUID] = None
    requested_by_name: Optional[str] = None
    approval_request_id: Optional[UUID] = None
    approval_request_number: Optional[str] = None
    approval_status: Optional[ApprovalRequestStatus] = None
    original_cost: Decimal
    accumulated_depreciation: Decimal
    book_value: Decimal
    disposal_value: Optional[Decimal] = None
    disposal_gain_loss: Optional[Decimal] = None
    remarks: Optional[str] = None
    buyer_name: Optional[str] = None
    status: str
    source: Literal["DISPOSED_ASSET", "APPROVAL_REQUEST"]


class DisposalRegisterListResponse(OffsetPaginatedResponse[DisposalRegisterItem]):
    """Paginated disposal register response."""


class DisposalRegisterActionResponse(CamelSchema):
    """Result of submitting a disposal action."""

    mode: Literal["disposed", "submitted_for_approval"]
    message: str
    asset: Optional[FixedAssetResponse] = None
    disposal: DisposalRegisterItem
    approval_request_id: Optional[UUID] = None
    approval_request_number: Optional[str] = None
    approval_status: Optional[ApprovalRequestStatus] = None


class DisposalApprovalPayload(CamelSchema):
    """Payload stored in approval-request details for disposal execution."""

    disposal: AssetDisposeRequest
    asset_code: str
    asset_name: str
    category_name: Optional[str] = None
