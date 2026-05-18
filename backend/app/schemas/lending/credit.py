"""Credit Bureau Pydantic Schemas.

Schemas for credit bureau pull requests, responses, and report data.
"""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field, validator

from app.schemas.base import CamelSchema

# ============================================================================
# Enums as string types for API
# ============================================================================


class CreditBureauEnum:
    CIBIL = "CIBIL"
    EXPERIAN = "EXPERIAN"
    EQUIFAX = "EQUIFAX"
    CRIF = "CRIF"


class CreditPullTypeEnum:
    SOFT = "SOFT"
    HARD = "HARD"


class CreditPullStatusEnum:
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    NO_HIT = "NO_HIT"
    EXPIRED = "EXPIRED"


# ============================================================================
# Request Schemas
# ============================================================================


class CreditPullRequest(CamelSchema):
    """Request to initiate a credit bureau pull."""

    bureau: str = Field(..., description="Credit bureau: CIBIL, EXPERIAN, EQUIFAX, CRIF")
    pull_type: str = Field(default="SOFT", description="Type of inquiry: SOFT or HARD")

    # Customer identification
    customer_name: str = Field(..., min_length=2, max_length=200)
    pan_number: str | None = Field(None, min_length=10, max_length=10)
    aadhaar_last4: str | None = Field(None, min_length=4, max_length=4)
    mobile_number: str | None = Field(None, max_length=15)
    email: str | None = Field(None, max_length=255)
    date_of_birth: date | None = None

    # Address
    address_line1: str | None = Field(None, max_length=255)
    address_line2: str | None = Field(None, max_length=255)
    city: str | None = Field(None, max_length=100)
    state: str | None = Field(None, max_length=100)
    pincode: str | None = Field(None, max_length=10)

    # Optional links
    entity_id: UUID | None = None
    loan_application_id: UUID | None = None
    purpose: str | None = Field(None, max_length=100)

    @validator("pan_number")
    def validate_pan(cls, v):
        if v and len(v) != 10:
            raise ValueError("PAN must be exactly 10 characters")
        if v:
            v = v.upper()
        return v

    @validator("bureau")
    def validate_bureau(cls, v):
        valid = ["CIBIL", "EXPERIAN", "EQUIFAX", "CRIF"]
        if v.upper() not in valid:
            raise ValueError(f"Bureau must be one of: {valid}")
        return v.upper()


class CreditPullBulkRequest(CamelSchema):
    """Request to pull credit from multiple bureaus."""

    bureaus: list[str] = Field(..., description="List of bureaus to pull from")
    pull_type: str = Field(default="SOFT")
    customer_name: str
    pan_number: str | None = None
    date_of_birth: date | None = None
    mobile_number: str | None = None
    entity_id: UUID | None = None
    loan_application_id: UUID | None = None


# ============================================================================
# Response Schemas
# ============================================================================


class CreditAccountResponse(CamelSchema):
    """Credit account from bureau report."""

    id: UUID
    account_number_masked: str | None = None
    institution_name: str | None = None
    institution_type: str | None = None
    account_type: str
    account_status: str
    ownership: str

    # Financial details
    sanctioned_amount: Decimal | None = None
    current_balance: Decimal | None = None
    overdue_amount: Decimal | None = None
    emi_amount: Decimal | None = None
    credit_limit: Decimal | None = None
    high_credit: Decimal | None = None
    write_off_amount: Decimal | None = None

    # Dates
    opened_date: date | None = None
    closed_date: date | None = None
    last_payment_date: date | None = None
    reported_date: date | None = None

    # Payment behavior
    tenure_months: int | None = None
    remaining_tenure: int | None = None
    max_dpd: int | None = None
    dpd_history: dict[str, int] | None = None

    # Flags
    is_secured: bool = False
    has_dispute: bool = False

    class Config:
        from_attributes = True


class CreditEnquiryResponse(CamelSchema):
    """Credit enquiry from bureau report."""

    id: UUID
    enquiry_date: date | None = None
    institution_name: str | None = None
    enquiry_purpose: str | None = None
    enquiry_amount: Decimal | None = None

    class Config:
        from_attributes = True


class CreditPullResponse(CamelSchema):
    """Credit pull response with full report data."""

    id: UUID
    organization_id: UUID
    entity_id: UUID | None = None
    loan_application_id: UUID | None = None

    # Bureau details
    bureau: str
    pull_type: str
    status: str

    # Customer info
    customer_name: str
    pan_number: str | None = None

    # Reference numbers
    request_reference: str | None = None
    bureau_reference: str | None = None

    # Credit Score
    credit_score: int | None = None
    score_version: str | None = None
    score_date: date | None = None
    score_band: str | None = None

    # Summary
    total_accounts: int | None = None
    active_accounts: int | None = None
    total_sanctioned: Decimal | None = None
    total_outstanding: Decimal | None = None
    total_overdue: Decimal | None = None
    max_dpd_last_12m: int | None = None
    max_dpd_last_24m: int | None = None
    enquiries_last_30d: int | None = None
    enquiries_last_12m: int | None = None

    # Error info
    error_code: str | None = None
    error_message: str | None = None

    # Timestamps
    pulled_at: datetime | None = None
    expires_at: datetime | None = None
    created_at: datetime

    # Related data
    accounts: list[CreditAccountResponse] = []
    enquiries: list[CreditEnquiryResponse] = []

    # Computed fields
    is_valid: bool = False

    class Config:
        from_attributes = True


class CreditPullListResponse(CamelSchema):
    """Credit pull list item (camelCase wire format)."""

    id: UUID
    organization_id: UUID
    entity_id: UUID | None = None
    loan_application_id: UUID | None = None
    bureau: str
    pull_type: str
    status: str
    customer_name: str
    pan_number: str | None = None
    credit_score: int | None = None
    score_band: str | None = None
    pulled_at: datetime | None = None
    expires_at: datetime | None = None
    is_valid: bool = False
    created_at: datetime


class CreditPullSummaryResponse(CamelSchema):
    """Summary of credit pulls for an entity/application."""

    entity_id: UUID | None = None
    loan_application_id: UUID | None = None
    total_pulls: int = 0
    latest_score: int | None = None
    latest_score_date: date | None = None
    latest_bureau: str | None = None
    score_band: str | None = None
    pulls_by_bureau: dict[str, int] = {}
    has_valid_report: bool = False


# ============================================================================
# Report Analysis Schemas
# ============================================================================


class CreditScoreHistory(CamelSchema):
    """Historical credit scores."""

    date: date
    bureau: str
    score: int
    score_band: str


class AccountSummaryByType(CamelSchema):
    """Summary of accounts by type."""

    account_type: str
    count: int
    total_sanctioned: Decimal = Decimal("0")
    total_outstanding: Decimal = Decimal("0")
    total_overdue: Decimal = Decimal("0")
    active_count: int = 0
    closed_count: int = 0


class DPDAnalysis(CamelSchema):
    """DPD (Days Past Due) analysis."""

    max_dpd_ever: int = 0
    max_dpd_last_6m: int = 0
    max_dpd_last_12m: int = 0
    max_dpd_last_24m: int = 0
    months_with_dpd: int = 0
    current_dpd: int = 0


class CreditReportAnalysis(CamelSchema):
    """Comprehensive credit report analysis."""

    pull_id: UUID
    bureau: str
    report_date: date

    # Score analysis
    credit_score: int | None = None
    score_band: str | None = None
    score_percentile: int | None = None

    # Account summary
    total_accounts: int = 0
    active_accounts: int = 0
    closed_accounts: int = 0
    written_off_accounts: int = 0
    accounts_by_type: list[AccountSummaryByType] = []

    # Financial summary
    total_sanctioned: Decimal = Decimal("0")
    total_outstanding: Decimal = Decimal("0")
    total_overdue: Decimal = Decimal("0")
    total_emi: Decimal = Decimal("0")
    utilization_ratio: Decimal | None = None

    # DPD analysis
    dpd_analysis: DPDAnalysis | None = None

    # Enquiry analysis
    total_enquiries: int = 0
    enquiries_last_30d: int = 0
    enquiries_last_90d: int = 0
    enquiries_last_12m: int = 0

    # Risk indicators
    has_written_off: bool = False
    has_settled: bool = False
    has_suit_filed: bool = False
    has_willful_default: bool = False
    high_enquiry_volume: bool = False


# ============================================================================
# Paginated Response
# ============================================================================


class PaginatedCreditPullResponse(CamelSchema):
    """Paginated list of credit pulls (camelCase wire format)."""

    items: list[CreditPullListResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# Statistics Schemas
# ============================================================================


class CreditBureauStats(CamelSchema):
    """Credit bureau usage statistics."""

    total_pulls: int = 0
    successful_pulls: int = 0
    failed_pulls: int = 0
    no_hit_pulls: int = 0
    pulls_by_bureau: dict[str, int] = {}
    pulls_by_status: dict[str, int] = {}
    average_score: float | None = None
    score_distribution: dict[str, int] = {}
