"""Loan Sanction schemas for the lending module."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field, model_validator

from app.models.lending.enums import (
    ChargeType,
    ConditionCategory,
    ConditionComplianceStatus,
    ConditionType,
    DayCountConvention,
    InterestType,
    RateResetFrequency,
    RepaymentFrequency,
    RepaymentMode,
    SanctionStatus,
    SecurityCategory,
    SecurityStatus,
    SecurityType,
)
from app.schemas.base import CamelSchema

# =============================================================================
# Sanction Condition Schemas
# =============================================================================


class SanctionConditionBase(CamelSchema):
    """Base schema for sanction condition."""

    condition_number: int | None = Field(None, ge=1)
    condition_code: str | None = Field(None, max_length=50)
    condition_type: ConditionType
    category: ConditionCategory
    description: str = Field(..., min_length=1)
    detailed_requirement: str | None = None
    due_date: date | None = None
    is_time_bound: bool = False
    days_from_disbursement: int | None = Field(None, ge=0)
    frequency: str | None = Field(None, max_length=50)
    next_compliance_date: date | None = None
    is_mandatory: bool = True
    blocks_disbursement: bool = False
    is_waivable: bool = True
    waiver_authority: str | None = Field(None, max_length=100)
    compliance_status: ConditionComplianceStatus = ConditionComplianceStatus.PENDING
    compliance_date: date | None = None
    compliance_remarks: str | None = None
    compliance_verified_by: UUID | None = None
    waiver_date: date | None = None
    waiver_reason: str | None = None
    waiver_approved_by: UUID | None = None
    deferral_date: date | None = None
    deferral_reason: str | None = None
    deferral_approved_by: UUID | None = None
    required_documents: list[dict[str, Any]] | None = None
    uploaded_documents: list[dict[str, Any]] | None = None
    display_order: int = Field(default=0, ge=0)


class SanctionConditionCreate(SanctionConditionBase):
    """Schema for creating sanction condition."""

    sanction_id: UUID | None = None


class SanctionConditionUpdate(CamelSchema):
    """Schema for updating sanction condition."""

    condition_number: int | None = Field(None, ge=1)
    condition_code: str | None = Field(None, max_length=50)
    condition_type: ConditionType | None = None
    category: ConditionCategory | None = None
    description: str | None = Field(None, min_length=1)
    detailed_requirement: str | None = None
    due_date: date | None = None
    is_time_bound: bool | None = None
    days_from_disbursement: int | None = Field(None, ge=0)
    frequency: str | None = Field(None, max_length=50)
    next_compliance_date: date | None = None
    is_mandatory: bool | None = None
    blocks_disbursement: bool | None = None
    is_waivable: bool | None = None
    waiver_authority: str | None = Field(None, max_length=100)
    compliance_status: ConditionComplianceStatus | None = None
    compliance_date: date | None = None
    compliance_remarks: str | None = None
    compliance_verified_by: UUID | None = None
    waiver_date: date | None = None
    waiver_reason: str | None = None
    waiver_approved_by: UUID | None = None
    deferral_date: date | None = None
    deferral_reason: str | None = None
    deferral_approved_by: UUID | None = None
    required_documents: list[dict[str, Any]] | None = None
    uploaded_documents: list[dict[str, Any]] | None = None
    display_order: int | None = Field(None, ge=0)
    is_active: bool | None = None


class SanctionConditionResponse(SanctionConditionBase):
    """Schema for sanction condition response."""

    id: UUID
    sanction_id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    is_active: bool = True


# =============================================================================
# Loan Security Schemas
# =============================================================================


class LoanSecurityBase(CamelSchema):
    """Base schema for loan security."""

    security_number: int | None = Field(None, ge=1)
    security_code: str | None = Field(None, max_length=50)
    security_category: SecurityCategory
    security_type: SecurityType
    charge_type: ChargeType = ChargeType.FIRST
    description: str = Field(..., min_length=1)
    detailed_description: str | None = None

    # Property details
    property_address: str | None = None
    property_area_sqft: Decimal | None = Field(None, ge=0)
    survey_number: str | None = Field(None, max_length=100)
    property_type: str | None = Field(None, max_length=100)

    # Ownership
    owner_name: str | None = Field(None, max_length=500)
    owner_relationship: str | None = Field(None, max_length=100)
    is_third_party: bool = False
    third_party_entity_id: UUID | None = None

    # Valuation
    declared_value: Decimal | None = Field(None, ge=0)
    market_value: Decimal | None = Field(None, ge=0)
    forced_sale_value: Decimal | None = Field(None, ge=0)
    acceptable_value: Decimal = Field(..., ge=0)
    margin_percentage: Decimal = Field(default=Decimal("25"), ge=0, le=100)
    net_value: Decimal | None = Field(None, ge=0)
    valuation_date: date | None = None
    valuer_name: str | None = Field(None, max_length=200)
    valuer_firm: str | None = Field(None, max_length=200)
    valuation_report_path: str | None = Field(None, max_length=500)
    next_valuation_date: date | None = None

    # Existing encumbrances
    has_existing_charge: bool = False
    existing_charge_holder: str | None = Field(None, max_length=200)
    existing_charge_amount: Decimal | None = Field(None, ge=0)
    noc_obtained: bool = False

    # Insurance
    requires_insurance: bool = True
    insured_value: Decimal | None = Field(None, ge=0)
    insurance_policy_number: str | None = Field(None, max_length=100)
    insurance_company: str | None = Field(None, max_length=200)
    insurance_expiry: date | None = None

    # Status and registrations
    status: SecurityStatus = SecurityStatus.PROPOSED
    release_date: date | None = None
    charge_created_date: date | None = None
    charge_id: str | None = Field(None, max_length=50)
    cersai_id: str | None = Field(None, max_length=50)
    cersai_registration_date: date | None = None

    # Legal and documents
    legal_vetted: bool = False
    legal_vetting_date: date | None = None
    legal_opinion_path: str | None = Field(None, max_length=500)
    legal_remarks: str | None = None
    original_documents_received: bool = False
    document_list: list[dict[str, Any]] | None = None
    document_location: str | None = Field(None, max_length=200)

    # Guarantee
    guarantor_entity_id: UUID | None = None
    guarantor_contact_id: UUID | None = None
    guarantee_amount: Decimal | None = Field(None, ge=0)
    is_unlimited_guarantee: bool = False
    remarks: str | None = None


class LoanSecurityCreate(LoanSecurityBase):
    """Schema for creating loan security."""

    sanction_id: UUID | None = None


class LoanSecurityUpdate(CamelSchema):
    """Schema for updating loan security."""

    security_number: int | None = Field(None, ge=1)
    security_code: str | None = Field(None, max_length=50)
    security_category: SecurityCategory | None = None
    security_type: SecurityType | None = None
    charge_type: ChargeType | None = None
    description: str | None = Field(None, min_length=1)
    detailed_description: str | None = None

    property_address: str | None = None
    property_area_sqft: Decimal | None = Field(None, ge=0)
    survey_number: str | None = Field(None, max_length=100)
    property_type: str | None = Field(None, max_length=100)

    owner_name: str | None = Field(None, max_length=500)
    owner_relationship: str | None = Field(None, max_length=100)
    is_third_party: bool | None = None
    third_party_entity_id: UUID | None = None

    declared_value: Decimal | None = Field(None, ge=0)
    market_value: Decimal | None = Field(None, ge=0)
    forced_sale_value: Decimal | None = Field(None, ge=0)
    acceptable_value: Decimal | None = Field(None, ge=0)
    margin_percentage: Decimal | None = Field(None, ge=0, le=100)
    net_value: Decimal | None = Field(None, ge=0)
    valuation_date: date | None = None
    valuer_name: str | None = Field(None, max_length=200)
    valuer_firm: str | None = Field(None, max_length=200)
    valuation_report_path: str | None = Field(None, max_length=500)
    next_valuation_date: date | None = None

    has_existing_charge: bool | None = None
    existing_charge_holder: str | None = Field(None, max_length=200)
    existing_charge_amount: Decimal | None = Field(None, ge=0)
    noc_obtained: bool | None = None

    requires_insurance: bool | None = None
    insured_value: Decimal | None = Field(None, ge=0)
    insurance_policy_number: str | None = Field(None, max_length=100)
    insurance_company: str | None = Field(None, max_length=200)
    insurance_expiry: date | None = None

    status: SecurityStatus | None = None
    release_date: date | None = None
    charge_created_date: date | None = None
    charge_id: str | None = Field(None, max_length=50)
    cersai_id: str | None = Field(None, max_length=50)
    cersai_registration_date: date | None = None
    legal_vetted: bool | None = None
    legal_vetting_date: date | None = None
    legal_opinion_path: str | None = Field(None, max_length=500)
    legal_remarks: str | None = None
    original_documents_received: bool | None = None
    document_list: list[dict[str, Any]] | None = None
    document_location: str | None = Field(None, max_length=200)
    guarantor_entity_id: UUID | None = None
    guarantor_contact_id: UUID | None = None
    guarantee_amount: Decimal | None = Field(None, ge=0)
    is_unlimited_guarantee: bool | None = None
    remarks: str | None = None
    is_active: bool | None = None


class LoanSecurityResponse(LoanSecurityBase):
    """Schema for loan security response."""

    id: UUID
    sanction_id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    is_active: bool = True


# =============================================================================
# Loan Sanction Schemas
# =============================================================================


class LoanSanctionBase(CamelSchema):
    """Base schema for loan sanction."""

    application_id: UUID

    # Sanctioned Amount & Terms
    sanctioned_amount: Decimal = Field(..., ge=0)
    tenure_months: int = Field(..., ge=1)
    moratorium_months: int = Field(default=0, ge=0)
    moratorium_type: str | None = Field(None, max_length=20)

    # Interest
    interest_type: InterestType
    base_rate_id: UUID | None = None
    base_rate_at_sanction: Decimal | None = Field(None, ge=0, le=100)
    spread_bps: int = Field(default=0, ge=0)
    effective_rate: Decimal = Field(..., ge=0, le=100)
    rate_reset_frequency: RateResetFrequency | None = None
    first_rate_reset_date: date | None = None
    penal_interest_rate: Decimal = Field(default=Decimal("2.00"), ge=0, le=100)
    day_count_convention: DayCountConvention = DayCountConvention.ACT_365

    # Repayment
    repayment_mode: RepaymentMode
    repayment_frequency: RepaymentFrequency
    repayment_start_date: date | None = None

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
    first_disbursement_deadline: date | None = None
    sanction_letter_path: str | None = Field(None, max_length=500)
    agreement_draft_path: str | None = Field(None, max_length=500)

    # Remarks
    special_terms: str | None = None
    remarks: str | None = None


class LoanSanctionCreate(LoanSanctionBase):
    """Schema for creating loan sanction."""

    organization_id: UUID | None = None
    entity_id: UUID | None = None
    conditions: list[SanctionConditionCreate] = Field(default_factory=list)
    securities: list[LoanSecurityCreate] = Field(default_factory=list)


class LoanSanctionUpdate(CamelSchema):
    """Schema for updating loan sanction."""

    sanctioned_amount: Decimal | None = Field(None, ge=0)
    tenure_months: int | None = Field(None, ge=1)
    moratorium_months: int | None = Field(None, ge=0)
    moratorium_type: str | None = Field(None, max_length=20)

    interest_type: InterestType | None = None
    base_rate_id: UUID | None = None
    base_rate_at_sanction: Decimal | None = Field(None, ge=0, le=100)
    spread_bps: int | None = Field(None, ge=0)
    effective_rate: Decimal | None = Field(None, ge=0, le=100)
    rate_reset_frequency: RateResetFrequency | None = None
    first_rate_reset_date: date | None = None
    penal_interest_rate: Decimal | None = Field(None, ge=0, le=100)
    day_count_convention: DayCountConvention | None = None

    repayment_mode: RepaymentMode | None = None
    repayment_frequency: RepaymentFrequency | None = None
    repayment_start_date: date | None = None

    allows_prepayment: bool | None = None
    prepayment_lock_in_months: int | None = Field(None, ge=0)
    prepayment_penalty_rate: Decimal | None = Field(None, ge=0, le=100)
    allows_foreclosure: bool | None = None
    foreclosure_penalty_rate: Decimal | None = Field(None, ge=0, le=100)

    disbursement_type: str | None = Field(None, max_length=20)
    max_tranches: int | None = Field(None, ge=1)

    validity_date: date | None = None
    first_disbursement_deadline: date | None = None
    sanction_letter_path: str | None = Field(None, max_length=500)
    agreement_draft_path: str | None = Field(None, max_length=500)

    status: SanctionStatus | None = None
    special_terms: str | None = None
    remarks: str | None = None
    is_active: bool | None = None


class LoanSanctionResponse(LoanSanctionBase):
    """Schema for loan sanction response."""

    id: UUID
    sanction_number: str
    organization_id: UUID
    entity_id: UUID
    product_id: UUID
    requested_amount: Decimal
    status: SanctionStatus
    workflow_instance_id: UUID | None = None
    approved_by_id: UUID | None = None
    approved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None
    is_active: bool = True


class LoanSanctionListResponse(CamelSchema):
    """Slim list response for sanctions.

    Wire format is camelCase via CamelSchema. Monetary + rate fields stay
    Decimal per CLAUDE.md §6.2 ("Float is banned for money"). Pydantic v2
    serializes Decimal to JSON as a string, preserving precision; the FE
    types those fields as `string` and only parses at display time.
    """

    id: UUID
    sanction_number: str
    application_id: UUID
    application_number: str | None = None
    entity_id: UUID
    entity_name: str | None = None
    product_id: UUID
    product_name: str | None = None
    sanctioned_amount: Decimal
    effective_rate: Decimal
    tenure_months: int
    sanction_date: date
    validity_date: date
    status: SanctionStatus

    @model_validator(mode="before")
    @classmethod
    def _derive_join_names(cls, obj):
        if isinstance(obj, dict):
            return obj
        entity = getattr(obj, "entity", None)
        product = getattr(obj, "product", None)
        application = getattr(obj, "application", None)
        return {
            "id": obj.id,
            "sanction_number": obj.sanction_number,
            "application_id": obj.application_id,
            "application_number": getattr(application, "application_number", None),
            "entity_id": obj.entity_id,
            "entity_name": (
                getattr(entity, "trade_name", None) or getattr(entity, "legal_name", None)
            ),
            "product_id": obj.product_id,
            "product_name": getattr(product, "name", None),
            "sanctioned_amount": obj.sanctioned_amount,
            "effective_rate": obj.effective_rate,
            "tenure_months": obj.tenure_months,
            "sanction_date": obj.sanction_date,
            "validity_date": obj.validity_date,
            "status": obj.status,
        }


class LoanSanctionDetailResponse(LoanSanctionResponse):
    """Schema for detailed loan sanction response with conditions and securities."""

    conditions: list[SanctionConditionResponse] = []
    securities: list[LoanSecurityResponse] = []
