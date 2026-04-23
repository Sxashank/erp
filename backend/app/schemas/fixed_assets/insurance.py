"""Insurance schemas."""

from datetime import date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import Field, field_validator

from app.schemas.base import BaseSchema, AuditSchema
from app.models.fixed_assets.insurance import (
    InsuranceType,
    InsurancePolicyStatus,
    ClaimStatus,
)


# ============================================
# Insurance Policy Schemas
# ============================================

class InsurancePolicyCreate(BaseSchema):
    """Schema for creating insurance policy."""

    organization_id: UUID
    policy_number: str = Field(..., max_length=50)
    policy_name: str = Field(..., max_length=200)
    insurance_type: InsuranceType

    insurer_name: str = Field(..., max_length=200)
    insurer_id: Optional[UUID] = None
    broker_name: Optional[str] = Field(None, max_length=200)
    broker_id: Optional[UUID] = None

    contact_person: Optional[str] = Field(None, max_length=100)
    contact_phone: Optional[str] = Field(None, max_length=20)
    contact_email: Optional[str] = Field(None, max_length=100)
    claim_helpline: Optional[str] = Field(None, max_length=20)

    start_date: date
    end_date: date

    sum_insured: Decimal = Field(..., ge=0)
    coverage_description: Optional[str] = None
    exclusions: Optional[str] = None
    deductible_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    deductible_percentage: Decimal = Field(default=Decimal("0.00"), ge=0)

    base_premium: Decimal = Field(..., ge=0)
    gst_rate: Decimal = Field(default=Decimal("18.00"), ge=0)
    stamp_duty: Decimal = Field(default=Decimal("0.00"), ge=0)

    payment_mode: str = Field(default="ANNUAL", max_length=20)

    asset_ids: Optional[List[str]] = None
    covers_all_assets: bool = False

    is_renewable: bool = True
    renewal_reminder_days: int = Field(default=30, ge=1)

    policy_document_url: Optional[str] = Field(None, max_length=500)
    terms_conditions: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v, info):
        if "start_date" in info.data and v <= info.data["start_date"]:
            raise ValueError("End date must be after start date")
        return v


class InsurancePolicyUpdate(BaseSchema):
    """Schema for updating insurance policy."""

    policy_name: Optional[str] = Field(None, max_length=200)
    contact_person: Optional[str] = Field(None, max_length=100)
    contact_phone: Optional[str] = Field(None, max_length=20)
    contact_email: Optional[str] = Field(None, max_length=100)
    claim_helpline: Optional[str] = Field(None, max_length=20)

    coverage_description: Optional[str] = None
    exclusions: Optional[str] = None

    asset_ids: Optional[List[str]] = None
    covers_all_assets: Optional[bool] = None

    renewal_reminder_days: Optional[int] = Field(None, ge=1)

    policy_document_url: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None


class InsurancePolicyRenew(BaseSchema):
    """Schema for renewing insurance policy."""

    new_start_date: date
    new_end_date: date
    new_sum_insured: Decimal = Field(..., ge=0)
    new_base_premium: Decimal = Field(..., ge=0)


class InsurancePremiumPayment(BaseSchema):
    """Schema for recording premium payment."""

    payment_date: date
    payment_reference: str = Field(..., max_length=100)
    amount_paid: Decimal = Field(..., ge=0)


class InsurancePolicyResponse(AuditSchema):
    """Schema for insurance policy response."""

    id: UUID
    organization_id: UUID
    policy_number: str
    policy_name: str
    insurance_type: InsuranceType
    status: InsurancePolicyStatus

    insurer_name: str
    insurer_id: Optional[UUID] = None
    broker_name: Optional[str] = None
    broker_id: Optional[UUID] = None

    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    claim_helpline: Optional[str] = None

    start_date: date
    end_date: date
    days_until_expiry: int
    is_expiring_soon: bool

    sum_insured: Decimal
    remaining_coverage: Decimal
    coverage_description: Optional[str] = None
    exclusions: Optional[str] = None
    deductible_amount: Decimal
    deductible_percentage: Decimal

    base_premium: Decimal
    gst_rate: Decimal
    gst_amount: Decimal
    stamp_duty: Decimal
    total_premium: Decimal

    payment_mode: str
    next_premium_due: Optional[date] = None
    premium_paid: bool
    premium_paid_date: Optional[date] = None

    asset_ids: Optional[List[str]] = None
    asset_count: int = 0
    covers_all_assets: bool

    total_claims_count: int
    total_claims_amount: Decimal
    total_settled_amount: Decimal

    is_renewable: bool
    renewal_reminder_days: int


# ============================================
# Insurance Claim Schemas
# ============================================

class InsuranceClaimCreate(BaseSchema):
    """Schema for creating insurance claim."""

    organization_id: UUID
    policy_id: UUID
    asset_id: UUID

    incident_date: date
    incident_description: str
    incident_location: Optional[str] = Field(None, max_length=200)
    cause_of_loss: Optional[str] = Field(None, max_length=100)

    reported_date: date = Field(default_factory=date.today)

    fir_number: Optional[str] = Field(None, max_length=50)
    fir_date: Optional[date] = None

    estimated_loss: Decimal = Field(..., ge=0)
    claim_amount: Decimal = Field(..., ge=0)

    notes: Optional[str] = None


class InsuranceClaimUpdate(BaseSchema):
    """Schema for updating insurance claim."""

    insurer_claim_number: Optional[str] = Field(None, max_length=50)
    status: Optional[ClaimStatus] = None

    fir_number: Optional[str] = Field(None, max_length=50)
    fir_date: Optional[date] = None

    submitted_date: Optional[date] = None
    surveyor_assigned_date: Optional[date] = None
    surveyor_name: Optional[str] = Field(None, max_length=100)
    surveyor_report_date: Optional[date] = None

    deductible_applied: Optional[Decimal] = Field(None, ge=0)
    approved_amount: Optional[Decimal] = Field(None, ge=0)
    rejection_reason: Optional[str] = None

    surveyor_report_url: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None


class InsuranceClaimSettle(BaseSchema):
    """Schema for settling insurance claim."""

    settlement_date: date
    settled_amount: Decimal = Field(..., ge=0)
    payment_received_date: Optional[date] = None
    payment_reference: Optional[str] = Field(None, max_length=100)

    asset_written_off: bool = False
    asset_repaired: bool = False
    repair_cost: Decimal = Field(default=Decimal("0.00"), ge=0)


class InsuranceClaimResponse(AuditSchema):
    """Schema for insurance claim response."""

    id: UUID
    organization_id: UUID
    policy_id: UUID
    policy_number: Optional[str] = None

    claim_number: str
    insurer_claim_number: Optional[str] = None

    asset_id: UUID
    asset_code: Optional[str] = None
    asset_name: Optional[str] = None

    status: ClaimStatus

    incident_date: date
    incident_description: str
    incident_location: Optional[str] = None
    cause_of_loss: Optional[str] = None

    reported_date: date
    reported_by: UUID

    fir_number: Optional[str] = None
    fir_date: Optional[date] = None

    estimated_loss: Decimal
    claim_amount: Decimal
    deductible_applied: Decimal
    approved_amount: Decimal
    settled_amount: Decimal
    rejection_reason: Optional[str] = None

    submitted_date: Optional[date] = None
    surveyor_assigned_date: Optional[date] = None
    surveyor_name: Optional[str] = None
    surveyor_report_date: Optional[date] = None
    approval_date: Optional[date] = None
    settlement_date: Optional[date] = None
    payment_received_date: Optional[date] = None
    payment_reference: Optional[str] = None

    processing_days: int

    asset_written_off: bool
    asset_repaired: bool
    repair_cost: Decimal


# ============================================
# Summary and Analytics Schemas
# ============================================

class InsuranceSummaryResponse(BaseSchema):
    """Insurance portfolio summary."""

    organization_id: UUID
    as_on_date: date

    # Policy counts
    total_policies: int
    active_policies: int
    expiring_within_30_days: int
    expired_policies: int

    # Coverage
    total_sum_insured: Decimal
    total_premium_paid: Decimal
    premium_due: Decimal

    # Claims
    total_claims_ytd: int
    claims_pending: int
    claims_settled_ytd: int
    total_claim_amount_ytd: Decimal
    total_settled_amount_ytd: Decimal

    # By type
    by_insurance_type: List[dict]

    # Claim ratio
    claim_ratio_percentage: Decimal


class InsuranceExpiryAlertResponse(BaseSchema):
    """Insurance expiry alerts."""

    policies_expiring: List[InsurancePolicyResponse]
    total_count: int
    total_sum_insured_at_risk: Decimal


class PendingClaimsResponse(BaseSchema):
    """Pending claims summary."""

    claims: List[InsuranceClaimResponse]
    total_count: int
    total_claim_amount: Decimal
    oldest_claim_days: int
