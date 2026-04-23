"""Loan Sanction schemas for the lending module."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import Field, model_validator

from app.schemas.base import BaseSchema
from app.models.lending.enums import (
    SanctionStatus,
    ConditionType,
    ConditionCategory,
    ConditionComplianceStatus,
    SecurityCategory,
    SecurityType,
    ChargeType,
    SecurityStatus,
    InterestType,
    RepaymentMode,
    RepaymentFrequency,
    RateResetFrequency,
    DayCountConvention,
)


# =============================================================================
# Sanction Condition Schemas
# =============================================================================


class SanctionConditionBase(BaseSchema):
    """Base schema for sanction condition."""

    condition_type: ConditionType
    category: ConditionCategory
    condition_text: str = Field(..., min_length=1)
    sequence: int = Field(default=1, ge=1)
    compliance_due_date: Optional[date] = None
    is_mandatory: bool = True
    compliance_status: ConditionComplianceStatus = ConditionComplianceStatus.PENDING
    complied_on: Optional[date] = None
    compliance_remarks: Optional[str] = None
    compliance_document_path: Optional[str] = Field(None, max_length=500)
    waiver_remarks: Optional[str] = None
    deferred_till: Optional[date] = None


class SanctionConditionCreate(SanctionConditionBase):
    """Schema for creating sanction condition."""

    sanction_id: UUID
    verified_by_id: Optional[UUID] = None
    waived_by_id: Optional[UUID] = None


class SanctionConditionUpdate(BaseSchema):
    """Schema for updating sanction condition."""

    condition_type: Optional[ConditionType] = None
    category: Optional[ConditionCategory] = None
    condition_text: Optional[str] = Field(None, min_length=1)
    sequence: Optional[int] = Field(None, ge=1)
    compliance_due_date: Optional[date] = None
    is_mandatory: Optional[bool] = None
    compliance_status: Optional[ConditionComplianceStatus] = None
    complied_on: Optional[date] = None
    verified_by_id: Optional[UUID] = None
    compliance_remarks: Optional[str] = None
    compliance_document_path: Optional[str] = Field(None, max_length=500)
    waived_by_id: Optional[UUID] = None
    waiver_remarks: Optional[str] = None
    deferred_till: Optional[date] = None
    is_active: Optional[bool] = None


class SanctionConditionResponse(SanctionConditionBase):
    """Schema for sanction condition response."""

    id: UUID
    sanction_id: UUID
    verified_by_id: Optional[UUID] = None
    waived_by_id: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True


# =============================================================================
# Loan Security Schemas
# =============================================================================


class LoanSecurityBase(BaseSchema):
    """Base schema for loan security."""

    security_category: SecurityCategory
    security_type: SecurityType
    charge_type: ChargeType
    security_description: str = Field(..., min_length=1, max_length=500)

    # Asset Details
    asset_id: Optional[str] = Field(None, max_length=100)
    asset_address: Optional[str] = Field(None, max_length=500)
    survey_number: Optional[str] = Field(None, max_length=100)
    area_sqft: Optional[Decimal] = Field(None, ge=0)
    land_type: Optional[str] = Field(None, max_length=50)

    # Ownership
    owner_name: Optional[str] = Field(None, max_length=200)
    owner_relation: Optional[str] = Field(None, max_length=50)
    ownership_document: Optional[str] = Field(None, max_length=200)

    # Valuation
    market_value: Optional[Decimal] = Field(None, ge=0)
    forced_sale_value: Optional[Decimal] = Field(None, ge=0)
    valuation_date: Optional[date] = None
    valuer_name: Optional[str] = Field(None, max_length=200)
    valuation_report_path: Optional[str] = Field(None, max_length=500)

    # Margins & Coverage
    margin_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    drawing_power: Optional[Decimal] = Field(None, ge=0)
    security_cover_percentage: Optional[Decimal] = Field(None, ge=0)

    # Insurance
    insurance_required: bool = False
    insurance_policy_number: Optional[str] = Field(None, max_length=100)
    insurance_company: Optional[str] = Field(None, max_length=200)
    insurance_amount: Optional[Decimal] = Field(None, ge=0)
    insurance_validity: Optional[date] = None

    # Registration
    cersai_registration_id: Optional[str] = Field(None, max_length=100)
    cersai_registration_date: Optional[date] = None
    roc_charge_id: Optional[str] = Field(None, max_length=100)
    roc_registration_date: Optional[date] = None

    # Status
    status: SecurityStatus = SecurityStatus.PROPOSED


class LoanSecurityCreate(LoanSecurityBase):
    """Schema for creating loan security."""

    sanction_id: UUID


class LoanSecurityUpdate(BaseSchema):
    """Schema for updating loan security."""

    security_category: Optional[SecurityCategory] = None
    security_type: Optional[SecurityType] = None
    charge_type: Optional[ChargeType] = None
    security_description: Optional[str] = Field(None, min_length=1, max_length=500)

    asset_id: Optional[str] = Field(None, max_length=100)
    asset_address: Optional[str] = Field(None, max_length=500)
    survey_number: Optional[str] = Field(None, max_length=100)
    area_sqft: Optional[Decimal] = Field(None, ge=0)
    land_type: Optional[str] = Field(None, max_length=50)

    owner_name: Optional[str] = Field(None, max_length=200)
    owner_relation: Optional[str] = Field(None, max_length=50)
    ownership_document: Optional[str] = Field(None, max_length=200)

    market_value: Optional[Decimal] = Field(None, ge=0)
    forced_sale_value: Optional[Decimal] = Field(None, ge=0)
    valuation_date: Optional[date] = None
    valuer_name: Optional[str] = Field(None, max_length=200)
    valuation_report_path: Optional[str] = Field(None, max_length=500)

    margin_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    drawing_power: Optional[Decimal] = Field(None, ge=0)
    security_cover_percentage: Optional[Decimal] = Field(None, ge=0)

    insurance_required: Optional[bool] = None
    insurance_policy_number: Optional[str] = Field(None, max_length=100)
    insurance_company: Optional[str] = Field(None, max_length=200)
    insurance_amount: Optional[Decimal] = Field(None, ge=0)
    insurance_validity: Optional[date] = None

    cersai_registration_id: Optional[str] = Field(None, max_length=100)
    cersai_registration_date: Optional[date] = None
    roc_charge_id: Optional[str] = Field(None, max_length=100)
    roc_registration_date: Optional[date] = None

    status: Optional[SecurityStatus] = None
    is_active: Optional[bool] = None


class LoanSecurityResponse(LoanSecurityBase):
    """Schema for loan security response."""

    id: UUID
    sanction_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True


# =============================================================================
# Loan Sanction Schemas
# =============================================================================


class LoanSanctionBase(BaseSchema):
    """Base schema for loan sanction."""

    application_id: UUID

    # Sanctioned Amount & Terms
    sanctioned_amount: Decimal = Field(..., ge=0)
    tenure_months: int = Field(..., ge=1)
    moratorium_months: int = Field(default=0, ge=0)
    moratorium_type: Optional[str] = Field(None, max_length=20)

    # Interest
    interest_type: InterestType
    base_rate_id: Optional[UUID] = None
    base_rate_at_sanction: Optional[Decimal] = Field(None, ge=0, le=100)
    spread_bps: int = Field(default=0, ge=0)
    effective_rate: Decimal = Field(..., ge=0, le=100)
    rate_reset_frequency: Optional[RateResetFrequency] = None
    first_rate_reset_date: Optional[date] = None
    penal_interest_rate: Decimal = Field(default=Decimal("2.00"), ge=0, le=100)
    day_count_convention: DayCountConvention = DayCountConvention.ACT_365

    # Repayment
    repayment_mode: RepaymentMode
    repayment_frequency: RepaymentFrequency
    repayment_start_date: Optional[date] = None

    # Prepayment Terms
    allows_prepayment: bool = True
    prepayment_lock_in_months: int = Field(default=0, ge=0)
    prepayment_penalty_rate: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    allows_foreclosure: bool = True
    foreclosure_penalty_rate: Decimal = Field(default=Decimal("0"), ge=0, le=100)

    # Disbursement
    disbursement_type: str = Field(default="SINGLE", max_length=20)
    max_tranches: int = Field(default=1, ge=1)

    # Sanction Validity
    sanction_date: date
    validity_date: date
    first_disbursement_deadline: Optional[date] = None
    sanction_letter_path: Optional[str] = Field(None, max_length=500)
    agreement_draft_path: Optional[str] = Field(None, max_length=500)

    # Remarks
    special_terms: Optional[str] = None
    remarks: Optional[str] = None


class LoanSanctionCreate(LoanSanctionBase):
    """Schema for creating loan sanction."""

    organization_id: UUID
    entity_id: UUID
    conditions: List[SanctionConditionCreate] = []
    securities: List[LoanSecurityCreate] = []


class LoanSanctionUpdate(BaseSchema):
    """Schema for updating loan sanction."""

    sanctioned_amount: Optional[Decimal] = Field(None, ge=0)
    tenure_months: Optional[int] = Field(None, ge=1)
    moratorium_months: Optional[int] = Field(None, ge=0)
    moratorium_type: Optional[str] = Field(None, max_length=20)

    interest_type: Optional[InterestType] = None
    base_rate_id: Optional[UUID] = None
    base_rate_at_sanction: Optional[Decimal] = Field(None, ge=0, le=100)
    spread_bps: Optional[int] = Field(None, ge=0)
    effective_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    rate_reset_frequency: Optional[RateResetFrequency] = None
    first_rate_reset_date: Optional[date] = None
    penal_interest_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    day_count_convention: Optional[DayCountConvention] = None

    repayment_mode: Optional[RepaymentMode] = None
    repayment_frequency: Optional[RepaymentFrequency] = None
    repayment_start_date: Optional[date] = None

    allows_prepayment: Optional[bool] = None
    prepayment_lock_in_months: Optional[int] = Field(None, ge=0)
    prepayment_penalty_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    allows_foreclosure: Optional[bool] = None
    foreclosure_penalty_rate: Optional[Decimal] = Field(None, ge=0, le=100)

    disbursement_type: Optional[str] = Field(None, max_length=20)
    max_tranches: Optional[int] = Field(None, ge=1)

    validity_date: Optional[date] = None
    first_disbursement_deadline: Optional[date] = None
    sanction_letter_path: Optional[str] = Field(None, max_length=500)
    agreement_draft_path: Optional[str] = Field(None, max_length=500)

    status: Optional[SanctionStatus] = None
    special_terms: Optional[str] = None
    remarks: Optional[str] = None
    is_active: Optional[bool] = None


class LoanSanctionResponse(LoanSanctionBase):
    """Schema for loan sanction response."""

    id: UUID
    sanction_number: str
    organization_id: UUID
    entity_id: UUID
    product_id: UUID
    requested_amount: Decimal
    status: SanctionStatus
    workflow_instance_id: Optional[UUID] = None
    approved_by_id: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True


class LoanSanctionListResponse(LoanSanctionResponse):
    """Schema for loan sanction list response (lighter version for lists)."""

    entity_name: Optional[str] = None
    product_name: Optional[str] = None


class LoanSanctionDetailResponse(LoanSanctionResponse):
    """Schema for detailed loan sanction response with conditions and securities."""

    conditions: List[SanctionConditionResponse] = []
    securities: List[LoanSecurityResponse] = []
