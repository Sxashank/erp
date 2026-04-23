"""Credit Bureau Pydantic Schemas.

Schemas for credit bureau pull requests, responses, and report data.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, validator


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

class CreditPullRequest(BaseModel):
    """Request to initiate a credit bureau pull."""

    bureau: str = Field(..., description="Credit bureau: CIBIL, EXPERIAN, EQUIFAX, CRIF")
    pull_type: str = Field(default="SOFT", description="Type of inquiry: SOFT or HARD")

    # Customer identification
    customer_name: str = Field(..., min_length=2, max_length=200)
    pan_number: Optional[str] = Field(None, min_length=10, max_length=10)
    aadhaar_last4: Optional[str] = Field(None, min_length=4, max_length=4)
    mobile_number: Optional[str] = Field(None, max_length=15)
    email: Optional[str] = Field(None, max_length=255)
    date_of_birth: Optional[date] = None

    # Address
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, max_length=10)

    # Optional links
    entity_id: Optional[UUID] = None
    loan_application_id: Optional[UUID] = None
    purpose: Optional[str] = Field(None, max_length=100)

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


class CreditPullBulkRequest(BaseModel):
    """Request to pull credit from multiple bureaus."""

    bureaus: List[str] = Field(..., description="List of bureaus to pull from")
    pull_type: str = Field(default="SOFT")
    customer_name: str
    pan_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    mobile_number: Optional[str] = None
    entity_id: Optional[UUID] = None
    loan_application_id: Optional[UUID] = None


# ============================================================================
# Response Schemas
# ============================================================================

class CreditAccountResponse(BaseModel):
    """Credit account from bureau report."""

    id: UUID
    account_number_masked: Optional[str] = None
    institution_name: Optional[str] = None
    institution_type: Optional[str] = None
    account_type: str
    account_status: str
    ownership: str

    # Financial details
    sanctioned_amount: Optional[Decimal] = None
    current_balance: Optional[Decimal] = None
    overdue_amount: Optional[Decimal] = None
    emi_amount: Optional[Decimal] = None
    credit_limit: Optional[Decimal] = None
    high_credit: Optional[Decimal] = None
    write_off_amount: Optional[Decimal] = None

    # Dates
    opened_date: Optional[date] = None
    closed_date: Optional[date] = None
    last_payment_date: Optional[date] = None
    reported_date: Optional[date] = None

    # Payment behavior
    tenure_months: Optional[int] = None
    remaining_tenure: Optional[int] = None
    max_dpd: Optional[int] = None
    dpd_history: Optional[Dict[str, int]] = None

    # Flags
    is_secured: bool = False
    has_dispute: bool = False

    class Config:
        from_attributes = True


class CreditEnquiryResponse(BaseModel):
    """Credit enquiry from bureau report."""

    id: UUID
    enquiry_date: Optional[date] = None
    institution_name: Optional[str] = None
    enquiry_purpose: Optional[str] = None
    enquiry_amount: Optional[Decimal] = None

    class Config:
        from_attributes = True


class CreditPullResponse(BaseModel):
    """Credit pull response with full report data."""

    id: UUID
    organization_id: UUID
    entity_id: Optional[UUID] = None
    loan_application_id: Optional[UUID] = None

    # Bureau details
    bureau: str
    pull_type: str
    status: str

    # Customer info
    customer_name: str
    pan_number: Optional[str] = None

    # Reference numbers
    request_reference: Optional[str] = None
    bureau_reference: Optional[str] = None

    # Credit Score
    credit_score: Optional[int] = None
    score_version: Optional[str] = None
    score_date: Optional[date] = None
    score_band: Optional[str] = None

    # Summary
    total_accounts: Optional[int] = None
    active_accounts: Optional[int] = None
    total_sanctioned: Optional[Decimal] = None
    total_outstanding: Optional[Decimal] = None
    total_overdue: Optional[Decimal] = None
    max_dpd_last_12m: Optional[int] = None
    max_dpd_last_24m: Optional[int] = None
    enquiries_last_30d: Optional[int] = None
    enquiries_last_12m: Optional[int] = None

    # Error info
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    # Timestamps
    pulled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime

    # Related data
    accounts: List[CreditAccountResponse] = []
    enquiries: List[CreditEnquiryResponse] = []

    # Computed fields
    is_valid: bool = False

    class Config:
        from_attributes = True


class CreditPullListResponse(BaseModel):
    """Credit pull list item (without full report data)."""

    id: UUID
    organization_id: UUID
    entity_id: Optional[UUID] = None
    loan_application_id: Optional[UUID] = None
    bureau: str
    pull_type: str
    status: str
    customer_name: str
    pan_number: Optional[str] = None
    credit_score: Optional[int] = None
    score_band: Optional[str] = None
    pulled_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_valid: bool = False
    created_at: datetime

    class Config:
        from_attributes = True


class CreditPullSummaryResponse(BaseModel):
    """Summary of credit pulls for an entity/application."""

    entity_id: Optional[UUID] = None
    loan_application_id: Optional[UUID] = None
    total_pulls: int = 0
    latest_score: Optional[int] = None
    latest_score_date: Optional[date] = None
    latest_bureau: Optional[str] = None
    score_band: Optional[str] = None
    pulls_by_bureau: Dict[str, int] = {}
    has_valid_report: bool = False


# ============================================================================
# Report Analysis Schemas
# ============================================================================

class CreditScoreHistory(BaseModel):
    """Historical credit scores."""

    date: date
    bureau: str
    score: int
    score_band: str


class AccountSummaryByType(BaseModel):
    """Summary of accounts by type."""

    account_type: str
    count: int
    total_sanctioned: Decimal = Decimal("0")
    total_outstanding: Decimal = Decimal("0")
    total_overdue: Decimal = Decimal("0")
    active_count: int = 0
    closed_count: int = 0


class DPDAnalysis(BaseModel):
    """DPD (Days Past Due) analysis."""

    max_dpd_ever: int = 0
    max_dpd_last_6m: int = 0
    max_dpd_last_12m: int = 0
    max_dpd_last_24m: int = 0
    months_with_dpd: int = 0
    current_dpd: int = 0


class CreditReportAnalysis(BaseModel):
    """Comprehensive credit report analysis."""

    pull_id: UUID
    bureau: str
    report_date: date

    # Score analysis
    credit_score: Optional[int] = None
    score_band: Optional[str] = None
    score_percentile: Optional[int] = None

    # Account summary
    total_accounts: int = 0
    active_accounts: int = 0
    closed_accounts: int = 0
    written_off_accounts: int = 0
    accounts_by_type: List[AccountSummaryByType] = []

    # Financial summary
    total_sanctioned: Decimal = Decimal("0")
    total_outstanding: Decimal = Decimal("0")
    total_overdue: Decimal = Decimal("0")
    total_emi: Decimal = Decimal("0")
    utilization_ratio: Optional[Decimal] = None

    # DPD analysis
    dpd_analysis: Optional[DPDAnalysis] = None

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

class PaginatedCreditPullResponse(BaseModel):
    """Paginated list of credit pulls."""

    items: List[CreditPullListResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ============================================================================
# Statistics Schemas
# ============================================================================

class CreditBureauStats(BaseModel):
    """Credit bureau usage statistics."""

    total_pulls: int = 0
    successful_pulls: int = 0
    failed_pulls: int = 0
    no_hit_pulls: int = 0
    pulls_by_bureau: Dict[str, int] = {}
    pulls_by_status: Dict[str, int] = {}
    average_score: Optional[float] = None
    score_distribution: Dict[str, int] = {}
