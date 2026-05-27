"""Treasury and ALM schemas for the lending module."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field, model_validator

from app.schemas.base import CamelSchema, PaginatedResponse

# ============================================================================
# Lender Schemas
# ============================================================================


class LenderBase(CamelSchema):
    """Base schema for lender."""

    lender_name: str = Field(..., max_length=200)
    lender_type: str = Field(..., max_length=50)
    pan: str | None = Field(None, max_length=20)
    cin: str | None = Field(None, max_length=25)
    gstin: str | None = Field(None, max_length=20)
    rbi_registration: str | None = Field(None, max_length=50)
    registered_address: str | None = None
    contact_person: str | None = Field(None, max_length=100)
    contact_email: str | None = Field(None, max_length=100)
    contact_phone: str | None = Field(None, max_length=20)
    bank_name: str | None = Field(None, max_length=100)
    bank_branch: str | None = Field(None, max_length=100)
    bank_account_number: str | None = Field(None, max_length=30)
    bank_ifsc: str | None = Field(None, max_length=15)
    external_rating: str | None = Field(None, max_length=20)
    rating_agency: str | None = Field(None, max_length=50)
    rating_date: date | None = None
    total_sanction_limit: Decimal | None = None
    remarks: str | None = None


class LenderCreate(LenderBase):
    """Schema for creating a lender."""

    pass


class LenderUpdate(CamelSchema):
    """Schema for updating a lender."""

    lender_name: str | None = Field(None, max_length=200)
    lender_type: str | None = Field(None, max_length=50)
    pan: str | None = Field(None, max_length=20)
    cin: str | None = Field(None, max_length=25)
    gstin: str | None = Field(None, max_length=20)
    rbi_registration: str | None = Field(None, max_length=50)
    registered_address: str | None = None
    contact_person: str | None = Field(None, max_length=100)
    contact_email: str | None = Field(None, max_length=100)
    contact_phone: str | None = Field(None, max_length=20)
    bank_name: str | None = Field(None, max_length=100)
    bank_branch: str | None = Field(None, max_length=100)
    bank_account_number: str | None = Field(None, max_length=30)
    bank_ifsc: str | None = Field(None, max_length=15)
    external_rating: str | None = Field(None, max_length=20)
    rating_agency: str | None = Field(None, max_length=50)
    rating_date: date | None = None
    total_sanction_limit: Decimal | None = None
    status: str | None = Field(None, max_length=20)
    remarks: str | None = None


class LenderResponse(LenderBase):
    """Schema for lender response."""

    lender_id: UUID
    organization_id: UUID
    lender_code: str
    status: str
    available_limit: Decimal | None = None
    created_at: datetime
    updated_at: datetime


class LenderListResponse(PaginatedResponse):
    """Paginated response for lenders."""

    items: list[LenderResponse]


class LenderListItemResponse(CamelSchema):
    """Slim list-item for /lending/treasury/lenders (camelCase wire).

    Monetary fields stay Decimal per CLAUDE.md §6.2. Pydantic v2 serializes
    Decimal to JSON as a string; the FE types those fields as `string`.
    """

    id: UUID
    lender_code: str
    lender_name: str
    lender_type: str
    status: str
    external_rating: str | None = None
    rating_agency: str | None = None
    total_sanction_limit: Decimal | None = None
    available_limit: Decimal | None = None
    contact_person: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    pan: str | None = None
    rbi_registration: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _from_orm(cls, obj):
        if isinstance(obj, dict):
            return obj
        return {
            "id": getattr(obj, "lender_id", None) or getattr(obj, "id", None),
            "lender_code": obj.lender_code,
            "lender_name": obj.lender_name,
            "lender_type": obj.lender_type,
            "status": obj.status,
            "external_rating": obj.external_rating,
            "rating_agency": obj.rating_agency,
            "total_sanction_limit": obj.total_sanction_limit,
            "available_limit": getattr(obj, "available_limit", None),
            "contact_person": obj.contact_person,
            "contact_email": obj.contact_email,
            "contact_phone": obj.contact_phone,
            "pan": obj.pan,
            "rbi_registration": obj.rbi_registration,
        }


# ============================================================================
# Borrowing Schemas
# ============================================================================


class BorrowingBase(CamelSchema):
    """Base schema for borrowing."""

    lender_id: UUID
    borrowing_type: str = Field(..., max_length=50)
    sanction_date: date
    sanction_reference: str | None = Field(None, max_length=100)
    sanctioned_amount: Decimal
    currency: str = Field(default="INR", max_length=3)
    rate_type: str = Field(..., max_length=30)
    base_rate_name: str | None = Field(None, max_length=50)
    base_rate_value: Decimal | None = None
    spread_bps: int = 0
    effective_rate: Decimal
    rate_reset_frequency: str | None = Field(None, max_length=30)
    day_count_convention: str = Field(default="ACT_365", max_length=20)
    interest_payment_frequency: str = Field(default="MONTHLY", max_length=20)
    principal_payment_frequency: str = Field(default="QUARTERLY", max_length=20)
    tenure_months: int
    moratorium_months: int = 0
    first_interest_date: date | None = None
    first_principal_date: date | None = None
    maturity_date: date
    security_type: str = Field(default="UNSECURED", max_length=30)
    security_description: str | None = None
    security_cover_required: Decimal | None = None
    processing_fee_percent: Decimal | None = None
    commitment_fee_percent: Decimal | None = None
    prepayment_penalty_percent: Decimal | None = None
    financial_covenants: dict[str, Any] | None = None
    reporting_requirements: dict[str, Any] | None = None
    remarks: str | None = None


class BorrowingCreate(BorrowingBase):
    """Schema for creating a borrowing."""

    pass


class BorrowingUpdate(CamelSchema):
    """Schema for updating a borrowing."""

    lender_id: UUID | None = None
    borrowing_type: str | None = Field(None, max_length=50)
    sanction_date: date | None = None
    sanction_reference: str | None = Field(None, max_length=100)
    sanctioned_amount: Decimal | None = None
    currency: str | None = Field(None, max_length=3)
    rate_type: str | None = Field(None, max_length=30)
    base_rate_name: str | None = Field(None, max_length=50)
    base_rate_value: Decimal | None = None
    spread_bps: int | None = None
    effective_rate: Decimal | None = None
    rate_reset_frequency: str | None = Field(None, max_length=30)
    day_count_convention: str | None = Field(None, max_length=20)
    interest_payment_frequency: str | None = Field(None, max_length=20)
    principal_payment_frequency: str | None = Field(None, max_length=20)
    tenure_months: int | None = None
    moratorium_months: int | None = None
    first_interest_date: date | None = None
    first_principal_date: date | None = None
    maturity_date: date | None = None
    next_rate_reset_date: date | None = None
    security_type: str | None = Field(None, max_length=30)
    security_description: str | None = None
    security_cover_required: Decimal | None = None
    processing_fee_percent: Decimal | None = None
    commitment_fee_percent: Decimal | None = None
    prepayment_penalty_percent: Decimal | None = None
    financial_covenants: dict[str, Any] | None = None
    reporting_requirements: dict[str, Any] | None = None
    sanction_letter_path: str | None = Field(None, max_length=500)
    agreement_date: date | None = None
    agreement_path: str | None = Field(None, max_length=500)
    status: str | None = Field(None, max_length=30)
    remarks: str | None = None


class BorrowingResponse(BorrowingBase):
    """Schema for borrowing response."""

    borrowing_id: UUID
    organization_id: UUID
    borrowing_number: str
    drawn_amount: Decimal
    available_amount: Decimal
    principal_outstanding: Decimal
    next_rate_reset_date: date | None = None
    sanction_letter_path: str | None = None
    agreement_date: date | None = None
    agreement_path: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime

    # Nested lender info
    lender_name: str | None = None
    lender_code: str | None = None


class BorrowingListResponse(PaginatedResponse):
    """Paginated response for borrowings."""

    items: list[BorrowingResponse]


class BorrowingListItemResponse(CamelSchema):
    """Slim list-item for /lending/treasury/borrowings (camelCase wire).

    Monetary + rate fields stay Decimal per CLAUDE.md §6.2.
    """

    id: UUID
    borrowing_number: str
    borrowing_type: str
    lender_id: UUID
    lender_name: str | None = None
    lender_code: str | None = None
    sanction_date: date
    sanctioned_amount: Decimal
    drawn_amount: Decimal
    available_amount: Decimal
    principal_outstanding: Decimal
    effective_rate: Decimal
    rate_type: str
    tenure_months: int
    maturity_date: date
    security_type: str
    currency: str
    status: str

    @model_validator(mode="before")
    @classmethod
    def _from_orm(cls, obj):
        if isinstance(obj, dict):
            return obj
        lender = getattr(obj, "lender", None)
        return {
            "id": getattr(obj, "borrowing_id", None) or getattr(obj, "id", None),
            "borrowing_number": obj.borrowing_number,
            "borrowing_type": obj.borrowing_type,
            "lender_id": obj.lender_id,
            "lender_name": getattr(lender, "lender_name", None),
            "lender_code": getattr(lender, "lender_code", None),
            "sanction_date": obj.sanction_date,
            "sanctioned_amount": obj.sanctioned_amount,
            "drawn_amount": obj.drawn_amount,
            "available_amount": obj.available_amount,
            "principal_outstanding": obj.principal_outstanding,
            "effective_rate": obj.effective_rate,
            "rate_type": obj.rate_type,
            "tenure_months": obj.tenure_months,
            "maturity_date": obj.maturity_date,
            "security_type": obj.security_type,
            "currency": obj.currency,
            "status": obj.status,
        }


class BorrowingDetailResponse(BorrowingResponse):
    """Detailed borrowing response with nested data."""

    tranches: list["BorrowingTrancheResponse"] = []
    schedule: list["BorrowingScheduleResponse"] = []
    covenants: list["BorrowingCovenantResponse"] = []


# ============================================================================
# Borrowing Tranche Schemas
# ============================================================================


class BorrowingTrancheBase(CamelSchema):
    """Base schema for borrowing tranche."""

    request_date: date
    requested_amount: Decimal
    purpose: str | None = None


class BorrowingTrancheCreate(BorrowingTrancheBase):
    """Schema for creating a borrowing tranche."""

    borrowing_id: UUID


class BorrowingTrancheApprove(CamelSchema):
    """Schema for approving a tranche."""

    remarks: str | None = None


class BorrowingTrancheDisbursement(CamelSchema):
    """Schema for disbursing a tranche."""

    disbursement_date: date
    disbursed_amount: Decimal
    effective_rate: Decimal | None = None
    utr_number: str | None = Field(None, max_length=50)
    bank_reference: str | None = Field(None, max_length=100)
    remarks: str | None = None


class BorrowingTrancheResponse(BorrowingTrancheBase):
    """Schema for borrowing tranche response."""

    tranche_id: UUID
    borrowing_id: UUID
    tranche_number: int
    disbursement_date: date | None = None
    disbursed_amount: Decimal | None = None
    principal_outstanding: Decimal
    effective_rate: Decimal | None = None
    utr_number: str | None = None
    bank_reference: str | None = None
    status: str
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    remarks: str | None = None
    created_at: datetime


class BorrowingTrancheListResponse(PaginatedResponse):
    """Paginated response for borrowing tranches."""

    items: list[BorrowingTrancheResponse]


# ============================================================================
# Borrowing Schedule Schemas
# ============================================================================


class BorrowingScheduleResponse(CamelSchema):
    """Schema for borrowing schedule response."""

    schedule_id: UUID
    borrowing_id: UUID
    tranche_id: UUID | None = None
    installment_number: int
    due_date: date
    principal_due: Decimal
    interest_due: Decimal
    total_due: Decimal
    principal_paid: Decimal
    interest_paid: Decimal
    total_paid: Decimal
    paid_date: date | None = None
    opening_balance: Decimal
    closing_balance: Decimal
    status: str


class BorrowingScheduleListResponse(PaginatedResponse):
    """Paginated response for borrowing schedules."""

    items: list[BorrowingScheduleResponse]


# ============================================================================
# Borrowing Payment Schemas
# ============================================================================


class BorrowingPaymentCreate(CamelSchema):
    """Schema for creating a borrowing payment."""

    borrowing_id: UUID
    schedule_id: UUID | None = None
    payment_type: str = Field(..., max_length=30)
    payment_date: date
    value_date: date
    principal_amount: Decimal = Decimal("0")
    interest_amount: Decimal = Decimal("0")
    fee_amount: Decimal = Decimal("0")
    payment_mode: str = Field(..., max_length=20)
    utr_number: str | None = Field(None, max_length=50)
    bank_reference: str | None = Field(None, max_length=100)
    from_bank_account: str | None = Field(None, max_length=30)
    interest_from_date: date | None = None
    interest_to_date: date | None = None
    remarks: str | None = None


class BorrowingPaymentResponse(CamelSchema):
    """Schema for borrowing payment response."""

    payment_id: UUID
    borrowing_id: UUID
    schedule_id: UUID | None = None
    payment_type: str
    payment_date: date
    value_date: date
    principal_amount: Decimal
    interest_amount: Decimal
    fee_amount: Decimal
    total_amount: Decimal
    payment_mode: str
    utr_number: str | None = None
    bank_reference: str | None = None
    from_bank_account: str | None = None
    interest_from_date: date | None = None
    interest_to_date: date | None = None
    days_counted: int | None = None
    rate_applied: Decimal | None = None
    remarks: str | None = None
    created_at: datetime


class BorrowingPaymentListResponse(PaginatedResponse):
    """Paginated response for borrowing payments."""

    items: list[BorrowingPaymentResponse]


# ============================================================================
# Borrowing Covenant Schemas
# ============================================================================


class BorrowingCovenantCreate(CamelSchema):
    """Schema for creating a borrowing covenant."""

    borrowing_id: UUID
    covenant_type: str = Field(..., max_length=50)
    covenant_description: str
    threshold_type: str = Field(..., max_length=20)  # MIN, MAX, RANGE
    threshold_value: Decimal | None = None
    threshold_min: Decimal | None = None
    threshold_max: Decimal | None = None
    testing_frequency: str = Field(default="QUARTERLY", max_length=20)
    next_test_date: date | None = None
    remarks: str | None = None


class BorrowingCovenantUpdate(CamelSchema):
    """Schema for updating a borrowing covenant."""

    covenant_description: str | None = None
    threshold_value: Decimal | None = None
    threshold_min: Decimal | None = None
    threshold_max: Decimal | None = None
    testing_frequency: str | None = Field(None, max_length=20)
    next_test_date: date | None = None
    current_value: Decimal | None = None
    last_tested_date: date | None = None
    status: str | None = Field(None, max_length=30)
    is_active: bool | None = None
    remarks: str | None = None


class BorrowingCovenantResponse(CamelSchema):
    """Schema for borrowing covenant response."""

    covenant_id: UUID
    borrowing_id: UUID
    covenant_type: str
    covenant_description: str
    threshold_type: str
    threshold_value: Decimal | None = None
    threshold_min: Decimal | None = None
    threshold_max: Decimal | None = None
    testing_frequency: str
    next_test_date: date | None = None
    current_value: Decimal | None = None
    last_tested_date: date | None = None
    status: str
    is_active: bool
    remarks: str | None = None
    created_at: datetime


class BorrowingCovenantListResponse(PaginatedResponse):
    """Paginated response for borrowing covenants."""

    items: list[BorrowingCovenantResponse]


# ============================================================================
# ALM Position Schemas
# ============================================================================


class ALMPositionGenerate(CamelSchema):
    """Schema for generating ALM position."""

    position_date: date
    remarks: str | None = None


class ALMPositionResponse(CamelSchema):
    """Schema for ALM position response."""

    position_id: UUID
    organization_id: UUID
    position_date: date
    total_assets: Decimal
    total_liabilities: Decimal
    net_position: Decimal
    bucket_analysis: dict[str, Any] | None = None
    cumulative_gap_1_year: Decimal | None = None
    cumulative_gap_percent: Decimal | None = None
    generated_by: UUID | None = None
    generated_at: datetime
    is_final: bool
    remarks: str | None = None
    created_at: datetime


class ALMPositionListResponse(PaginatedResponse):
    """Paginated response for ALM positions."""

    items: list[ALMPositionResponse]


class ALMPositionDetailResponse(ALMPositionResponse):
    """Detailed ALM position response."""

    assets: list["ALMAssetResponse"] = []
    liabilities: list["ALMLiabilityResponse"] = []


# ============================================================================
# ALM Asset Schemas
# ============================================================================


class ALMAssetResponse(CamelSchema):
    """Schema for ALM asset response."""

    asset_id: UUID
    position_id: UUID
    asset_type: str
    alm_bucket: str
    book_value: Decimal
    market_value: Decimal | None = None
    rate_sensitive_amount: Decimal
    non_rate_sensitive_amount: Decimal
    weighted_avg_rate: Decimal | None = None
    weighted_avg_maturity_days: int | None = None
    source_type: str | None = None
    source_count: int | None = None
    remarks: str | None = None


# ============================================================================
# ALM Liability Schemas
# ============================================================================


class ALMLiabilityResponse(CamelSchema):
    """Schema for ALM liability response."""

    liability_id: UUID
    position_id: UUID
    liability_type: str
    alm_bucket: str
    book_value: Decimal
    rate_sensitive_amount: Decimal
    non_rate_sensitive_amount: Decimal
    weighted_avg_rate: Decimal | None = None
    weighted_avg_maturity_days: int | None = None
    source_type: str | None = None
    source_count: int | None = None
    remarks: str | None = None


# ============================================================================
# IRS Analysis Schemas
# ============================================================================


class IRSAnalysisGenerate(CamelSchema):
    """Schema for generating IRS analysis."""

    analysis_date: date
    shock_type: str = Field(..., max_length=30)
    shock_bps: int
    remarks: str | None = None


class IRSAnalysisResponse(CamelSchema):
    """Schema for IRS analysis response."""

    analysis_id: UUID
    organization_id: UUID
    position_id: UUID | None = None
    analysis_date: date
    shock_type: str
    shock_bps: int
    rate_sensitive_assets: Decimal
    rate_sensitive_liabilities: Decimal
    rate_sensitivity_gap: Decimal
    nii_impact: Decimal
    nii_impact_percent: Decimal
    ev_impact: Decimal | None = None
    ev_impact_percent: Decimal | None = None
    bucket_analysis: dict[str, Any] | None = None
    generated_by: UUID | None = None
    generated_at: datetime
    remarks: str | None = None
    created_at: datetime


class IRSAnalysisListResponse(PaginatedResponse):
    """Paginated response for IRS analyses."""

    items: list[IRSAnalysisResponse]


# ----------------------------------------------------------------------------
# IRS Preview Schemas (non-persisting, dashboard-friendly)
# ----------------------------------------------------------------------------


class IRSShockBucket(CamelSchema):
    """Projected NII impact for one rate-shock bucket.

    Money + rate fields stay Decimal per CLAUDE.md §6.2. On the wire they are
    serialized as JSON strings; the frontend coerces with `Number(...)` at the
    chart input boundary only.
    """

    shock_bps: int
    rsa: Decimal
    rsl: Decimal
    gap: Decimal
    nii_impact: Decimal
    nii_impact_percent: Decimal


class IRSPreviewSummary(CamelSchema):
    """Summary block for an IRS preview computation."""

    rsa: Decimal
    rsl: Decimal
    gap: Decimal
    total_assets: Decimal
    gap_to_total_assets_percent: Decimal


class IRSPreviewResponse(CamelSchema):
    """On-the-fly IRS analysis for the dashboard.

    GET `/lending/treasury/irs/preview?as_of_date=YYYY-MM-DD` returns this
    payload. No rows are written to `trs_irs_analysis`.
    """

    as_of_date: date
    summary: IRSPreviewSummary
    shocks: list[IRSShockBucket]


# ============================================================================
# Exposure Limit Schemas
# ============================================================================


class ExposureLimitCreate(CamelSchema):
    """Schema for creating an exposure limit."""

    limit_type: str = Field(..., max_length=50)
    limit_key: str = Field(..., max_length=100)
    limit_description: str | None = None
    regulatory_limit_percent: Decimal | None = None
    regulatory_limit_amount: Decimal | None = None
    internal_limit_percent: Decimal | None = None
    internal_limit_amount: Decimal | None = None
    warning_threshold_percent: Decimal = Decimal("80")
    effective_from: date
    effective_to: date | None = None
    remarks: str | None = None


class ExposureLimitUpdate(CamelSchema):
    """Schema for updating an exposure limit."""

    limit_description: str | None = None
    regulatory_limit_percent: Decimal | None = None
    regulatory_limit_amount: Decimal | None = None
    internal_limit_percent: Decimal | None = None
    internal_limit_amount: Decimal | None = None
    warning_threshold_percent: Decimal | None = None
    effective_to: date | None = None
    is_active: bool | None = None
    remarks: str | None = None


class ExposureLimitResponse(CamelSchema):
    """Schema for exposure limit response."""

    limit_id: UUID
    organization_id: UUID
    limit_type: str
    limit_key: str
    limit_description: str | None = None
    regulatory_limit_percent: Decimal | None = None
    regulatory_limit_amount: Decimal | None = None
    internal_limit_percent: Decimal | None = None
    internal_limit_amount: Decimal | None = None
    warning_threshold_percent: Decimal
    current_exposure: Decimal
    current_exposure_percent: Decimal
    exposure_count: int
    last_calculated_at: datetime | None = None
    status: str
    is_active: bool
    effective_from: date
    effective_to: date | None = None
    approved_by: UUID | None = None
    remarks: str | None = None
    created_at: datetime


class ExposureLimitListResponse(PaginatedResponse):
    """Paginated response for exposure limits."""

    items: list[ExposureLimitResponse]


# ============================================================================
# Exposure Tracking Schemas
# ============================================================================


class ExposureTrackingResponse(CamelSchema):
    """Schema for exposure tracking response."""

    tracking_id: UUID
    limit_id: UUID
    entity_id: UUID | None = None
    loan_account_id: UUID | None = None
    borrowing_id: UUID | None = None
    exposure_amount: Decimal
    funded_exposure: Decimal
    non_funded_exposure: Decimal
    as_of_date: date
    remarks: str | None = None

    # Additional info for display
    entity_name: str | None = None
    loan_account_number: str | None = None


class ExposureTrackingListResponse(PaginatedResponse):
    """Paginated response for exposure tracking."""

    items: list[ExposureTrackingResponse]


# ============================================================================
# Fund Deployment Schemas
# ============================================================================


class FundDeploymentCreate(CamelSchema):
    """Create a source-of-funds mapping from borrowing to loan deployment."""

    borrowing_id: UUID
    loan_account_id: UUID
    allocated_amount: Decimal
    allocation_date: date
    borrowing_tranche_id: UUID | None = None
    disbursement_id: UUID | None = None
    cost_rate: Decimal | None = None
    lending_rate: Decimal | None = None
    allocation_basis: dict[str, Any] | None = None
    remarks: str | None = None


class FundDeploymentResponse(CamelSchema):
    """Funding deployment response with derived spread details."""

    id: UUID
    organization_id: UUID
    deployment_reference: str
    borrowing_id: UUID
    borrowing_tranche_id: UUID | None = None
    loan_account_id: UUID
    disbursement_id: UUID | None = None
    allocation_date: date
    allocated_amount: Decimal
    cost_rate: Decimal
    lending_rate: Decimal
    spread_bps: Decimal
    allocation_basis: dict[str, Any] | None = None
    status: str
    remarks: str | None = None
    created_at: datetime


class FundDeploymentSummary(CamelSchema):
    """Borrowed-funds deployment summary for treasury cockpit."""

    mapped_deployments: int = 0
    deployed_amount: Decimal = Decimal("0")
    active_drawn_borrowings: Decimal = Decimal("0")
    unmapped_drawn_borrowings: Decimal = Decimal("0")
    weighted_cost_rate: Decimal = Decimal("0")
    weighted_lending_rate: Decimal = Decimal("0")
    weighted_spread_bps: Decimal = Decimal("0")


class FundProfitabilityRow(CamelSchema):
    """Per-loan profitability from mapped source-of-funds records."""

    loan_account_id: UUID
    loan_account_number: str
    entity_name: str | None = None
    deployment_count: int = 0
    deployed_amount: Decimal = Decimal("0")
    weighted_cost_rate: Decimal = Decimal("0")
    weighted_lending_rate: Decimal = Decimal("0")
    spread_bps: Decimal = Decimal("0")
    estimated_annual_interest_income: Decimal = Decimal("0")
    estimated_annual_interest_expense: Decimal = Decimal("0")
    estimated_annual_nii: Decimal = Decimal("0")


class FundProfitabilitySummary(CamelSchema):
    """Portfolio-level profitability rollup from fund deployments."""

    mapped_loans: int = 0
    deployed_amount: Decimal = Decimal("0")
    weighted_cost_rate: Decimal = Decimal("0")
    weighted_lending_rate: Decimal = Decimal("0")
    weighted_spread_bps: Decimal = Decimal("0")
    estimated_annual_interest_income: Decimal = Decimal("0")
    estimated_annual_interest_expense: Decimal = Decimal("0")
    estimated_annual_nii: Decimal = Decimal("0")


class FundProfitabilityResponse(CamelSchema):
    """Profitability analytics for mapped borrowed funds."""

    summary: FundProfitabilitySummary
    rows: list[FundProfitabilityRow]


# ============================================================================
# Summary/Dashboard Schemas
# ============================================================================


class BorrowingSummary(CamelSchema):
    """Summary of borrowings (camelCase wire format).

    Monetary + rate fields stay Decimal per CLAUDE.md §6.2.
    """

    total_sanctioned: Decimal = Decimal("0")
    total_drawn: Decimal = Decimal("0")
    total_available: Decimal = Decimal("0")
    total_outstanding: Decimal = Decimal("0")
    active_borrowings: int = 0
    lender_count: int = 0
    weighted_avg_rate: Decimal | None = None
    upcoming_repayments_30d: Decimal = Decimal("0")
    upcoming_maturities_90d: int = 0


class ALMGapAnalysis(CamelSchema):
    """ALM gap analysis summary (camelCase wire format)."""

    bucket: str
    assets: Decimal
    liabilities: Decimal
    gap: Decimal
    cumulative_gap: Decimal
    gap_percent: Decimal


class ALMSummary(CamelSchema):
    """ALM summary (camelCase wire format)."""

    position_date: date
    total_assets: Decimal
    total_liabilities: Decimal
    net_position: Decimal
    cumulative_gap_1_year: Decimal
    cumulative_gap_percent: Decimal
    gap_analysis: list[ALMGapAnalysis] = []


class ExposureSummary(CamelSchema):
    """Exposure summary (camelCase wire format)."""

    total_limits: int = 0
    within_limit: int = 0
    near_limit: int = 0
    breach_count: int = 0
    total_exposure: Decimal = Decimal("0")
    top_exposures: list[dict[str, Any]] = []


class TreasurySummary(CamelSchema):
    """Overall treasury summary (camelCase wire format)."""

    borrowing_summary: BorrowingSummary
    alm_summary: ALMSummary | None = None
    exposure_summary: ExposureSummary


# Forward references for nested models
BorrowingDetailResponse.model_rebuild()
ALMPositionDetailResponse.model_rebuild()
