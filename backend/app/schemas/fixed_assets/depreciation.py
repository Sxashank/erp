"""Depreciation schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import CamelSchema
from app.schemas.fixed_assets.common import FixedAssetsAuditSchema, OffsetPaginatedResponse
from app.core.constants import (
    DepreciationType,
    DepreciationMethod,
    DepreciationBook,
    ITActAssetBlock,
    ApprovalRequestStatus,
)


class DepreciationRunCreate(CamelSchema):
    """Schema for creating a depreciation run."""

    depreciation_period: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}$",
        description="Period in YYYY-MM format",
    )
    depreciation_book: DepreciationBook = Field(
        default=DepreciationBook.COMPANIES_ACT,
        description="Depreciation book (COMPANIES_ACT or IT_ACT)",
    )
    remarks: Optional[str] = Field(None, max_length=500)
    organization_id: UUID


class DepreciationRunResponse(FixedAssetsAuditSchema):
    """Depreciation run response schema."""

    id: UUID
    organization_id: UUID
    depreciation_book: DepreciationBook = DepreciationBook.COMPANIES_ACT
    depreciation_period: str
    period_from: date
    period_to: date
    total_assets: int
    total_depreciation: Decimal
    processed_assets: int
    skipped_assets: int
    status: str
    run_started_at: Optional[datetime] = None
    run_completed_at: Optional[datetime] = None
    run_by: Optional[UUID] = None
    voucher_id: Optional[UUID] = None
    voucher_number: Optional[str] = None
    posted_at: Optional[datetime] = None
    posted_by: Optional[UUID] = None
    remarks: Optional[str] = None


class DepreciationPostingActionResponse(CamelSchema):
    """Response for posting or submitting a depreciation run."""

    mode: Literal["posted", "submitted_for_approval"]
    message: str
    run: DepreciationRunResponse
    approval_request_id: UUID | None = None
    approval_request_number: str | None = None
    approval_status: ApprovalRequestStatus | None = None


class DepreciationResponse(FixedAssetsAuditSchema):
    """Individual depreciation entry response schema."""

    id: UUID
    asset_id: UUID
    asset_code: Optional[str] = None
    asset_name: Optional[str] = None
    depreciation_run_id: Optional[UUID] = None
    depreciation_period: str
    period_from: date
    period_to: date
    days_in_period: int
    opening_wdv: Decimal
    depreciation_rate: Decimal
    depreciation_amount: Decimal
    accumulated_depreciation: Decimal
    closing_wdv: Decimal
    depreciation_type: DepreciationType
    depreciation_book: DepreciationBook = DepreciationBook.COMPANIES_ACT
    voucher_id: Optional[UUID] = None
    is_posted: bool
    is_reversed: bool
    reversal_of_id: Optional[UUID] = None
    reversed_by_id: Optional[UUID] = None
    remarks: Optional[str] = None


class DepreciationScheduleItem(CamelSchema):
    """Single item in depreciation schedule projection."""

    period: str  # YYYY-MM
    period_from: date
    period_to: date
    opening_wdv: Decimal
    depreciation_rate: Decimal
    depreciation_amount: Decimal
    accumulated_depreciation: Decimal
    closing_wdv: Decimal
    is_fully_depreciated: bool = False


class DepreciationScheduleResponse(CamelSchema):
    """Depreciation schedule projection response."""

    asset_id: UUID
    asset_code: str
    asset_name: str
    total_cost: Decimal
    residual_value: Decimal
    depreciable_value: Decimal
    depreciation_method: DepreciationMethod
    depreciation_rate: Decimal
    useful_life_months: int
    current_wdv: Decimal
    current_accumulated_depreciation: Decimal
    remaining_months: int
    schedule: List[DepreciationScheduleItem]


class DepreciationReverseRequest(CamelSchema):
    """Request to reverse a depreciation entry."""

    reason: str = Field(..., min_length=1, max_length=500)


class DepreciationSummaryItem(CamelSchema):
    """Depreciation summary by category."""

    category_id: UUID
    category_code: str
    category_name: str
    asset_count: int
    total_cost: Decimal
    total_depreciation: Decimal
    accumulated_depreciation: Decimal
    closing_wdv: Decimal


class DepreciationSummaryResponse(CamelSchema):
    """Depreciation summary report response."""

    organization_id: UUID
    depreciation_period: str
    period_from: date
    period_to: date
    total_assets: int
    total_depreciation: Decimal
    by_category: List[DepreciationSummaryItem]


class AssetRegisterItem(CamelSchema):
    """Single item in asset register report."""

    id: UUID
    asset_code: str
    asset_name: str
    category_code: str
    category_name: str
    location_name: Optional[str] = None
    department_name: Optional[str] = None
    acquisition_date: date
    acquisition_cost: Decimal
    additions: Decimal = Decimal("0.00")
    disposals: Decimal = Decimal("0.00")
    revaluation: Decimal = Decimal("0.00")
    depreciation_for_period: Decimal = Decimal("0.00")
    accumulated_depreciation: Decimal
    wdv_value: Decimal
    status: str


class AssetRegisterResponse(CamelSchema):
    """Asset register report response."""

    organization_id: UUID
    as_on_date: date
    total_cost: Decimal
    total_additions: Decimal
    total_disposals: Decimal
    total_revaluation: Decimal
    total_depreciation: Decimal
    total_accumulated_depreciation: Decimal
    total_wdv: Decimal
    assets: List[AssetRegisterItem]


# ============================================
# IT Act Depreciation Schemas
# ============================================


class ITDepreciationRunCreate(CamelSchema):
    """Schema for creating an IT Act depreciation run."""

    financial_year: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}$",
        description="Financial Year in YYYY-YY format (e.g., 2024-25)",
    )
    remarks: Optional[str] = Field(None, max_length=500)
    organization_id: UUID


class ITBlockSummaryResponse(FixedAssetsAuditSchema):
    """IT Act Block Summary response schema."""

    id: UUID
    organization_id: UUID
    it_block: ITActAssetBlock
    it_block_name: Optional[str] = None
    financial_year: str
    opening_wdv: Decimal
    additions_during_year: Decimal
    disposals_during_year: Decimal
    depreciation_rate: Decimal
    depreciation_amount: Decimal
    additional_depreciation: Decimal
    closing_wdv: Decimal
    asset_count: int
    is_finalized: bool
    finalized_at: Optional[datetime] = None
    finalized_by: Optional[UUID] = None
    remarks: Optional[str] = None


class ITBlockSummaryCreate(CamelSchema):
    """Schema for initializing IT Block Summary for a financial year."""

    organization_id: UUID
    financial_year: str = Field(
        ...,
        pattern=r"^\d{4}-\d{2}$",
        description="Financial Year in YYYY-YY format",
    )


class ITBlockDepreciationItem(CamelSchema):
    """Single block depreciation item in IT depreciation report."""

    it_block: ITActAssetBlock
    block_name: str
    depreciation_rate: Decimal
    opening_wdv: Decimal
    additions: Decimal
    disposals: Decimal
    total_before_depreciation: Decimal
    depreciation_amount: Decimal
    additional_depreciation: Decimal = Decimal("0.00")
    closing_wdv: Decimal
    asset_count: int


class ITDepreciationReportResponse(CamelSchema):
    """IT Act Depreciation Report response."""

    organization_id: UUID
    financial_year: str
    blocks: List[ITBlockDepreciationItem]
    total_opening_wdv: Decimal
    total_additions: Decimal
    total_disposals: Decimal
    total_depreciation: Decimal
    total_additional_depreciation: Decimal
    total_closing_wdv: Decimal


class ITDepreciationScheduleItem(CamelSchema):
    """Single item in IT depreciation schedule projection."""

    financial_year: str  # YYYY-YY
    opening_wdv: Decimal
    additions: Decimal = Decimal("0.00")
    disposals: Decimal = Decimal("0.00")
    depreciation_rate: Decimal
    depreciation_amount: Decimal
    additional_depreciation: Decimal = Decimal("0.00")
    closing_wdv: Decimal
    is_block_extinguished: bool = False


class ITDepreciationScheduleResponse(CamelSchema):
    """IT Depreciation schedule projection response."""

    asset_id: UUID
    asset_code: str
    asset_name: str
    it_block: Optional[ITActAssetBlock] = None
    it_block_name: Optional[str] = None
    total_cost: Decimal
    it_act_rate: Decimal
    current_it_wdv: Decimal
    current_it_accumulated_depreciation: Decimal
    is_additional_depreciation_eligible: bool
    additional_depreciation_claimed: Decimal
    schedule: List[ITDepreciationScheduleItem]


class AssetITDepreciationComparison(CamelSchema):
    """Asset-level comparison between Companies Act and IT Act depreciation."""

    asset_id: UUID
    asset_code: str
    asset_name: str
    category_name: str
    acquisition_date: date
    acquisition_cost: Decimal
    # Companies Act
    ca_depreciation_method: DepreciationMethod
    ca_depreciation_rate: Decimal
    ca_accumulated_depreciation: Decimal
    ca_wdv: Decimal
    # IT Act
    it_block: Optional[ITActAssetBlock] = None
    it_depreciation_rate: Decimal
    it_accumulated_depreciation: Decimal
    it_wdv: Decimal
    # Difference
    depreciation_difference: Decimal
    wdv_difference: Decimal


class DepreciationComparisonResponse(CamelSchema):
    """Comparison report between Companies Act and IT Act depreciation."""

    organization_id: UUID
    as_on_date: date
    financial_year: str
    assets: List[AssetITDepreciationComparison]
    total_ca_accumulated_depreciation: Decimal
    total_it_accumulated_depreciation: Decimal
    total_depreciation_difference: Decimal
    total_ca_wdv: Decimal
    total_it_wdv: Decimal
    deferred_tax_liability: Optional[Decimal] = None  # Calculated based on tax rate


# IT Block rate lookup (as per IT Act Schedule II)
IT_BLOCK_RATES = {
    ITActAssetBlock.BLOCK_1: Decimal("5.00"),  # Residential buildings
    ITActAssetBlock.BLOCK_2: Decimal("10.00"),  # Non-residential buildings
    ITActAssetBlock.BLOCK_3: Decimal("40.00"),  # Temporary structures
    ITActAssetBlock.BLOCK_4: Decimal("10.00"),  # Furniture & Fittings
    ITActAssetBlock.BLOCK_5: Decimal("15.00"),  # Machinery - General
    ITActAssetBlock.BLOCK_6: Decimal("30.00"),  # Machinery - High efficiency
    ITActAssetBlock.BLOCK_7: Decimal("20.00"),  # Ships/Vessels
    ITActAssetBlock.BLOCK_8: Decimal("15.00"),  # Motor Vehicles
    ITActAssetBlock.BLOCK_9: Decimal("30.00"),  # Motor Vehicles - Hire/Leasing
    ITActAssetBlock.BLOCK_10: Decimal("40.00"),  # Aircrafts
    ITActAssetBlock.BLOCK_11: Decimal("50.00"),  # Containers
    ITActAssetBlock.BLOCK_12: Decimal("25.00"),  # Intangible Assets
}

IT_BLOCK_NAMES = {
    ITActAssetBlock.BLOCK_1: "Buildings - Residential (5%)",
    ITActAssetBlock.BLOCK_2: "Buildings - Non-residential (10%)",
    ITActAssetBlock.BLOCK_3: "Buildings - Temporary structures (40%)",
    ITActAssetBlock.BLOCK_4: "Furniture & Fittings (10%)",
    ITActAssetBlock.BLOCK_5: "Plant & Machinery - General (15%)",
    ITActAssetBlock.BLOCK_6: "Plant & Machinery - High efficiency (30%)",
    ITActAssetBlock.BLOCK_7: "Ships & Vessels (20%)",
    ITActAssetBlock.BLOCK_8: "Motor Vehicles - General (15%)",
    ITActAssetBlock.BLOCK_9: "Motor Vehicles - Hire/Leasing (30%)",
    ITActAssetBlock.BLOCK_10: "Aircrafts/Helicopters (40%)",
    ITActAssetBlock.BLOCK_11: "Containers (50%)",
    ITActAssetBlock.BLOCK_12: "Intangible Assets (25%)",
}


class DepreciationRunListResponse(OffsetPaginatedResponse[DepreciationRunResponse]):
    """Paginated depreciation-run response."""


class DepreciationEntryListResponse(OffsetPaginatedResponse[DepreciationResponse]):
    """Paginated depreciation-entry response."""


class DepreciationPostingActionResponse(CamelSchema):
    """Result of posting or submitting a depreciation run for approval."""

    mode: Literal["posted", "submitted_for_approval"]
    message: str
    run: DepreciationRunResponse
    approval_request_id: Optional[UUID] = None
    approval_request_number: Optional[str] = None
    approval_status: Optional[ApprovalRequestStatus] = None
