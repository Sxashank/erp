"""Treasury and ALM schemas for the lending module."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, PaginatedResponse


# ============================================================================
# Lender Schemas
# ============================================================================


class LenderBase(BaseSchema):
    """Base schema for lender."""

    lender_name: str = Field(..., max_length=200)
    lender_type: str = Field(..., max_length=50)
    pan: Optional[str] = Field(None, max_length=20)
    cin: Optional[str] = Field(None, max_length=25)
    gstin: Optional[str] = Field(None, max_length=20)
    rbi_registration: Optional[str] = Field(None, max_length=50)
    registered_address: Optional[str] = None
    contact_person: Optional[str] = Field(None, max_length=100)
    contact_email: Optional[str] = Field(None, max_length=100)
    contact_phone: Optional[str] = Field(None, max_length=20)
    bank_name: Optional[str] = Field(None, max_length=100)
    bank_branch: Optional[str] = Field(None, max_length=100)
    bank_account_number: Optional[str] = Field(None, max_length=30)
    bank_ifsc: Optional[str] = Field(None, max_length=15)
    external_rating: Optional[str] = Field(None, max_length=20)
    rating_agency: Optional[str] = Field(None, max_length=50)
    rating_date: Optional[date] = None
    total_sanction_limit: Optional[Decimal] = None
    remarks: Optional[str] = None


class LenderCreate(LenderBase):
    """Schema for creating a lender."""

    pass


class LenderUpdate(BaseSchema):
    """Schema for updating a lender."""

    lender_name: Optional[str] = Field(None, max_length=200)
    lender_type: Optional[str] = Field(None, max_length=50)
    pan: Optional[str] = Field(None, max_length=20)
    cin: Optional[str] = Field(None, max_length=25)
    gstin: Optional[str] = Field(None, max_length=20)
    rbi_registration: Optional[str] = Field(None, max_length=50)
    registered_address: Optional[str] = None
    contact_person: Optional[str] = Field(None, max_length=100)
    contact_email: Optional[str] = Field(None, max_length=100)
    contact_phone: Optional[str] = Field(None, max_length=20)
    bank_name: Optional[str] = Field(None, max_length=100)
    bank_branch: Optional[str] = Field(None, max_length=100)
    bank_account_number: Optional[str] = Field(None, max_length=30)
    bank_ifsc: Optional[str] = Field(None, max_length=15)
    external_rating: Optional[str] = Field(None, max_length=20)
    rating_agency: Optional[str] = Field(None, max_length=50)
    rating_date: Optional[date] = None
    total_sanction_limit: Optional[Decimal] = None
    status: Optional[str] = Field(None, max_length=20)
    remarks: Optional[str] = None


class LenderResponse(LenderBase):
    """Schema for lender response."""

    lender_id: UUID
    organization_id: UUID
    lender_code: str
    status: str
    available_limit: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime


class LenderListResponse(PaginatedResponse):
    """Paginated response for lenders."""

    items: List[LenderResponse]


# ============================================================================
# Borrowing Schemas
# ============================================================================


class BorrowingBase(BaseSchema):
    """Base schema for borrowing."""

    lender_id: UUID
    borrowing_type: str = Field(..., max_length=50)
    sanction_date: date
    sanction_reference: Optional[str] = Field(None, max_length=100)
    sanctioned_amount: Decimal
    currency: str = Field(default="INR", max_length=3)
    rate_type: str = Field(..., max_length=30)
    base_rate_name: Optional[str] = Field(None, max_length=50)
    base_rate_value: Optional[Decimal] = None
    spread_bps: int = 0
    effective_rate: Decimal
    rate_reset_frequency: Optional[str] = Field(None, max_length=30)
    day_count_convention: str = Field(default="ACT_365", max_length=20)
    interest_payment_frequency: str = Field(default="MONTHLY", max_length=20)
    principal_payment_frequency: str = Field(default="QUARTERLY", max_length=20)
    tenure_months: int
    moratorium_months: int = 0
    first_interest_date: Optional[date] = None
    first_principal_date: Optional[date] = None
    maturity_date: date
    security_type: str = Field(default="UNSECURED", max_length=30)
    security_description: Optional[str] = None
    security_cover_required: Optional[Decimal] = None
    processing_fee_percent: Optional[Decimal] = None
    commitment_fee_percent: Optional[Decimal] = None
    prepayment_penalty_percent: Optional[Decimal] = None
    financial_covenants: Optional[Dict[str, Any]] = None
    reporting_requirements: Optional[Dict[str, Any]] = None
    remarks: Optional[str] = None


class BorrowingCreate(BorrowingBase):
    """Schema for creating a borrowing."""

    pass


class BorrowingUpdate(BaseSchema):
    """Schema for updating a borrowing."""

    sanction_reference: Optional[str] = Field(None, max_length=100)
    base_rate_value: Optional[Decimal] = None
    spread_bps: Optional[int] = None
    effective_rate: Optional[Decimal] = None
    next_rate_reset_date: Optional[date] = None
    security_description: Optional[str] = None
    financial_covenants: Optional[Dict[str, Any]] = None
    reporting_requirements: Optional[Dict[str, Any]] = None
    sanction_letter_path: Optional[str] = Field(None, max_length=500)
    agreement_date: Optional[date] = None
    agreement_path: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = Field(None, max_length=30)
    remarks: Optional[str] = None


class BorrowingResponse(BorrowingBase):
    """Schema for borrowing response."""

    borrowing_id: UUID
    organization_id: UUID
    borrowing_number: str
    drawn_amount: Decimal
    available_amount: Decimal
    principal_outstanding: Decimal
    next_rate_reset_date: Optional[date] = None
    sanction_letter_path: Optional[str] = None
    agreement_date: Optional[date] = None
    agreement_path: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    # Nested lender info
    lender_name: Optional[str] = None
    lender_code: Optional[str] = None


class BorrowingListResponse(PaginatedResponse):
    """Paginated response for borrowings."""

    items: List[BorrowingResponse]


class BorrowingDetailResponse(BorrowingResponse):
    """Detailed borrowing response with nested data."""

    tranches: List["BorrowingTrancheResponse"] = []
    schedule: List["BorrowingScheduleResponse"] = []
    covenants: List["BorrowingCovenantResponse"] = []


# ============================================================================
# Borrowing Tranche Schemas
# ============================================================================


class BorrowingTrancheBase(BaseSchema):
    """Base schema for borrowing tranche."""

    request_date: date
    requested_amount: Decimal
    purpose: Optional[str] = None


class BorrowingTrancheCreate(BorrowingTrancheBase):
    """Schema for creating a borrowing tranche."""

    borrowing_id: UUID


class BorrowingTrancheApprove(BaseSchema):
    """Schema for approving a tranche."""

    remarks: Optional[str] = None


class BorrowingTrancheDisbursement(BaseSchema):
    """Schema for disbursing a tranche."""

    disbursement_date: date
    disbursed_amount: Decimal
    effective_rate: Optional[Decimal] = None
    utr_number: Optional[str] = Field(None, max_length=50)
    bank_reference: Optional[str] = Field(None, max_length=100)
    remarks: Optional[str] = None


class BorrowingTrancheResponse(BorrowingTrancheBase):
    """Schema for borrowing tranche response."""

    tranche_id: UUID
    borrowing_id: UUID
    tranche_number: int
    disbursement_date: Optional[date] = None
    disbursed_amount: Optional[Decimal] = None
    principal_outstanding: Decimal
    effective_rate: Optional[Decimal] = None
    utr_number: Optional[str] = None
    bank_reference: Optional[str] = None
    status: str
    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    remarks: Optional[str] = None
    created_at: datetime


class BorrowingTrancheListResponse(PaginatedResponse):
    """Paginated response for borrowing tranches."""

    items: List[BorrowingTrancheResponse]


# ============================================================================
# Borrowing Schedule Schemas
# ============================================================================


class BorrowingScheduleResponse(BaseSchema):
    """Schema for borrowing schedule response."""

    schedule_id: UUID
    borrowing_id: UUID
    tranche_id: Optional[UUID] = None
    installment_number: int
    due_date: date
    principal_due: Decimal
    interest_due: Decimal
    total_due: Decimal
    principal_paid: Decimal
    interest_paid: Decimal
    total_paid: Decimal
    paid_date: Optional[date] = None
    opening_balance: Decimal
    closing_balance: Decimal
    status: str


class BorrowingScheduleListResponse(PaginatedResponse):
    """Paginated response for borrowing schedules."""

    items: List[BorrowingScheduleResponse]


# ============================================================================
# Borrowing Payment Schemas
# ============================================================================


class BorrowingPaymentCreate(BaseSchema):
    """Schema for creating a borrowing payment."""

    borrowing_id: UUID
    schedule_id: Optional[UUID] = None
    payment_type: str = Field(..., max_length=30)
    payment_date: date
    value_date: date
    principal_amount: Decimal = Decimal("0")
    interest_amount: Decimal = Decimal("0")
    fee_amount: Decimal = Decimal("0")
    payment_mode: str = Field(..., max_length=20)
    utr_number: Optional[str] = Field(None, max_length=50)
    bank_reference: Optional[str] = Field(None, max_length=100)
    from_bank_account: Optional[str] = Field(None, max_length=30)
    interest_from_date: Optional[date] = None
    interest_to_date: Optional[date] = None
    remarks: Optional[str] = None


class BorrowingPaymentResponse(BaseSchema):
    """Schema for borrowing payment response."""

    payment_id: UUID
    borrowing_id: UUID
    schedule_id: Optional[UUID] = None
    payment_type: str
    payment_date: date
    value_date: date
    principal_amount: Decimal
    interest_amount: Decimal
    fee_amount: Decimal
    total_amount: Decimal
    payment_mode: str
    utr_number: Optional[str] = None
    bank_reference: Optional[str] = None
    from_bank_account: Optional[str] = None
    interest_from_date: Optional[date] = None
    interest_to_date: Optional[date] = None
    days_counted: Optional[int] = None
    rate_applied: Optional[Decimal] = None
    remarks: Optional[str] = None
    created_at: datetime


class BorrowingPaymentListResponse(PaginatedResponse):
    """Paginated response for borrowing payments."""

    items: List[BorrowingPaymentResponse]


# ============================================================================
# Borrowing Covenant Schemas
# ============================================================================


class BorrowingCovenantCreate(BaseSchema):
    """Schema for creating a borrowing covenant."""

    borrowing_id: UUID
    covenant_type: str = Field(..., max_length=50)
    covenant_description: str
    threshold_type: str = Field(..., max_length=20)  # MIN, MAX, RANGE
    threshold_value: Optional[Decimal] = None
    threshold_min: Optional[Decimal] = None
    threshold_max: Optional[Decimal] = None
    testing_frequency: str = Field(default="QUARTERLY", max_length=20)
    next_test_date: Optional[date] = None
    remarks: Optional[str] = None


class BorrowingCovenantUpdate(BaseSchema):
    """Schema for updating a borrowing covenant."""

    covenant_description: Optional[str] = None
    threshold_value: Optional[Decimal] = None
    threshold_min: Optional[Decimal] = None
    threshold_max: Optional[Decimal] = None
    testing_frequency: Optional[str] = Field(None, max_length=20)
    next_test_date: Optional[date] = None
    current_value: Optional[Decimal] = None
    last_tested_date: Optional[date] = None
    status: Optional[str] = Field(None, max_length=30)
    is_active: Optional[bool] = None
    remarks: Optional[str] = None


class BorrowingCovenantResponse(BaseSchema):
    """Schema for borrowing covenant response."""

    covenant_id: UUID
    borrowing_id: UUID
    covenant_type: str
    covenant_description: str
    threshold_type: str
    threshold_value: Optional[Decimal] = None
    threshold_min: Optional[Decimal] = None
    threshold_max: Optional[Decimal] = None
    testing_frequency: str
    next_test_date: Optional[date] = None
    current_value: Optional[Decimal] = None
    last_tested_date: Optional[date] = None
    status: str
    is_active: bool
    remarks: Optional[str] = None
    created_at: datetime


class BorrowingCovenantListResponse(PaginatedResponse):
    """Paginated response for borrowing covenants."""

    items: List[BorrowingCovenantResponse]


# ============================================================================
# ALM Position Schemas
# ============================================================================


class ALMPositionGenerate(BaseSchema):
    """Schema for generating ALM position."""

    position_date: date
    remarks: Optional[str] = None


class ALMPositionResponse(BaseSchema):
    """Schema for ALM position response."""

    position_id: UUID
    organization_id: UUID
    position_date: date
    total_assets: Decimal
    total_liabilities: Decimal
    net_position: Decimal
    bucket_analysis: Optional[Dict[str, Any]] = None
    cumulative_gap_1_year: Optional[Decimal] = None
    cumulative_gap_percent: Optional[Decimal] = None
    generated_by: Optional[UUID] = None
    generated_at: datetime
    is_final: bool
    remarks: Optional[str] = None
    created_at: datetime


class ALMPositionListResponse(PaginatedResponse):
    """Paginated response for ALM positions."""

    items: List[ALMPositionResponse]


class ALMPositionDetailResponse(ALMPositionResponse):
    """Detailed ALM position response."""

    assets: List["ALMAssetResponse"] = []
    liabilities: List["ALMLiabilityResponse"] = []


# ============================================================================
# ALM Asset Schemas
# ============================================================================


class ALMAssetResponse(BaseSchema):
    """Schema for ALM asset response."""

    asset_id: UUID
    position_id: UUID
    asset_type: str
    alm_bucket: str
    book_value: Decimal
    market_value: Optional[Decimal] = None
    rate_sensitive_amount: Decimal
    non_rate_sensitive_amount: Decimal
    weighted_avg_rate: Optional[Decimal] = None
    weighted_avg_maturity_days: Optional[int] = None
    source_type: Optional[str] = None
    source_count: Optional[int] = None
    remarks: Optional[str] = None


# ============================================================================
# ALM Liability Schemas
# ============================================================================


class ALMLiabilityResponse(BaseSchema):
    """Schema for ALM liability response."""

    liability_id: UUID
    position_id: UUID
    liability_type: str
    alm_bucket: str
    book_value: Decimal
    rate_sensitive_amount: Decimal
    non_rate_sensitive_amount: Decimal
    weighted_avg_rate: Optional[Decimal] = None
    weighted_avg_maturity_days: Optional[int] = None
    source_type: Optional[str] = None
    source_count: Optional[int] = None
    remarks: Optional[str] = None


# ============================================================================
# IRS Analysis Schemas
# ============================================================================


class IRSAnalysisGenerate(BaseSchema):
    """Schema for generating IRS analysis."""

    analysis_date: date
    shock_type: str = Field(..., max_length=30)
    shock_bps: int
    remarks: Optional[str] = None


class IRSAnalysisResponse(BaseSchema):
    """Schema for IRS analysis response."""

    analysis_id: UUID
    organization_id: UUID
    position_id: Optional[UUID] = None
    analysis_date: date
    shock_type: str
    shock_bps: int
    rate_sensitive_assets: Decimal
    rate_sensitive_liabilities: Decimal
    rate_sensitivity_gap: Decimal
    nii_impact: Decimal
    nii_impact_percent: Decimal
    ev_impact: Optional[Decimal] = None
    ev_impact_percent: Optional[Decimal] = None
    bucket_analysis: Optional[Dict[str, Any]] = None
    generated_by: Optional[UUID] = None
    generated_at: datetime
    remarks: Optional[str] = None
    created_at: datetime


class IRSAnalysisListResponse(PaginatedResponse):
    """Paginated response for IRS analyses."""

    items: List[IRSAnalysisResponse]


# ============================================================================
# Exposure Limit Schemas
# ============================================================================


class ExposureLimitCreate(BaseSchema):
    """Schema for creating an exposure limit."""

    limit_type: str = Field(..., max_length=50)
    limit_key: str = Field(..., max_length=100)
    limit_description: Optional[str] = None
    regulatory_limit_percent: Optional[Decimal] = None
    regulatory_limit_amount: Optional[Decimal] = None
    internal_limit_percent: Optional[Decimal] = None
    internal_limit_amount: Optional[Decimal] = None
    warning_threshold_percent: Decimal = Decimal("80")
    effective_from: date
    effective_to: Optional[date] = None
    remarks: Optional[str] = None


class ExposureLimitUpdate(BaseSchema):
    """Schema for updating an exposure limit."""

    limit_description: Optional[str] = None
    regulatory_limit_percent: Optional[Decimal] = None
    regulatory_limit_amount: Optional[Decimal] = None
    internal_limit_percent: Optional[Decimal] = None
    internal_limit_amount: Optional[Decimal] = None
    warning_threshold_percent: Optional[Decimal] = None
    effective_to: Optional[date] = None
    is_active: Optional[bool] = None
    remarks: Optional[str] = None


class ExposureLimitResponse(BaseSchema):
    """Schema for exposure limit response."""

    limit_id: UUID
    organization_id: UUID
    limit_type: str
    limit_key: str
    limit_description: Optional[str] = None
    regulatory_limit_percent: Optional[Decimal] = None
    regulatory_limit_amount: Optional[Decimal] = None
    internal_limit_percent: Optional[Decimal] = None
    internal_limit_amount: Optional[Decimal] = None
    warning_threshold_percent: Decimal
    current_exposure: Decimal
    current_exposure_percent: Decimal
    exposure_count: int
    last_calculated_at: Optional[datetime] = None
    status: str
    is_active: bool
    effective_from: date
    effective_to: Optional[date] = None
    approved_by: Optional[UUID] = None
    remarks: Optional[str] = None
    created_at: datetime


class ExposureLimitListResponse(PaginatedResponse):
    """Paginated response for exposure limits."""

    items: List[ExposureLimitResponse]


# ============================================================================
# Exposure Tracking Schemas
# ============================================================================


class ExposureTrackingResponse(BaseSchema):
    """Schema for exposure tracking response."""

    tracking_id: UUID
    limit_id: UUID
    entity_id: Optional[UUID] = None
    loan_account_id: Optional[UUID] = None
    borrowing_id: Optional[UUID] = None
    exposure_amount: Decimal
    funded_exposure: Decimal
    non_funded_exposure: Decimal
    as_of_date: date
    remarks: Optional[str] = None

    # Additional info for display
    entity_name: Optional[str] = None
    loan_account_number: Optional[str] = None


class ExposureTrackingListResponse(PaginatedResponse):
    """Paginated response for exposure tracking."""

    items: List[ExposureTrackingResponse]


# ============================================================================
# Summary/Dashboard Schemas
# ============================================================================


class BorrowingSummary(BaseSchema):
    """Summary of borrowings."""

    total_sanctioned: Decimal = Decimal("0")
    total_drawn: Decimal = Decimal("0")
    total_available: Decimal = Decimal("0")
    total_outstanding: Decimal = Decimal("0")
    active_borrowings: int = 0
    lender_count: int = 0
    weighted_avg_rate: Optional[Decimal] = None
    upcoming_repayments_30d: Decimal = Decimal("0")
    upcoming_maturities_90d: int = 0


class ALMGapAnalysis(BaseSchema):
    """ALM gap analysis summary."""

    bucket: str
    assets: Decimal
    liabilities: Decimal
    gap: Decimal
    cumulative_gap: Decimal
    gap_percent: Decimal


class ALMSummary(BaseSchema):
    """ALM summary."""

    position_date: date
    total_assets: Decimal
    total_liabilities: Decimal
    net_position: Decimal
    cumulative_gap_1_year: Decimal
    cumulative_gap_percent: Decimal
    gap_analysis: List[ALMGapAnalysis] = []


class ExposureSummary(BaseSchema):
    """Exposure summary."""

    total_limits: int = 0
    within_limit: int = 0
    near_limit: int = 0
    breach_count: int = 0
    total_exposure: Decimal = Decimal("0")
    top_exposures: List[Dict[str, Any]] = []


class TreasurySummary(BaseSchema):
    """Overall treasury summary."""

    borrowing_summary: BorrowingSummary
    alm_summary: Optional[ALMSummary] = None
    exposure_summary: ExposureSummary


# Forward references for nested models
BorrowingDetailResponse.model_rebuild()
ALMPositionDetailResponse.model_rebuild()
