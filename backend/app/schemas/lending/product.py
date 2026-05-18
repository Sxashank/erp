"""Loan Product schemas for the lending module."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field, model_validator

from app.models.lending.enums import (
    DayCountConvention,
    DocumentCategory,
    DocumentStage,
    EntityType,
    FeeCalculationType,
    FeeType,
    InterestType,
    ProductCategory,
    RateResetFrequency,
    RepaymentFrequency,
    RepaymentMode,
)
from app.schemas.base import CamelSchema

# =============================================================================
# Interest Rate Schemas
# =============================================================================


class InterestRateBase(CamelSchema):
    """Base schema for interest rate."""

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    rate_type: str = Field(default="BASE_RATE", max_length=30)
    current_rate: Decimal = Field(..., ge=0, le=100)
    effective_from: date
    effective_till: date | None = None
    benchmark_rate: str | None = Field(None, max_length=50, description="e.g., REPO, MCLR")
    spread_over_benchmark_bps: int | None = Field(None, ge=0)


class InterestRateCreate(InterestRateBase):
    """Schema for creating interest rate."""

    organization_id: UUID | None = None


class InterestRateUpdate(CamelSchema):
    """Schema for updating interest rate."""

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    rate_type: str | None = Field(None, max_length=30)
    current_rate: Decimal | None = Field(None, ge=0, le=100)
    effective_from: date | None = None
    effective_till: date | None = None
    benchmark_rate: str | None = Field(None, max_length=50)
    spread_over_benchmark_bps: int | None = Field(None, ge=0)
    is_active: bool | None = None


class InterestRateResponse(InterestRateBase):
    """Schema for interest rate response."""

    id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    is_active: bool = True


# =============================================================================
# Fee Master Schemas
# =============================================================================


class FeeMasterBase(CamelSchema):
    """Base schema for fee master."""

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    fee_type: FeeType
    calculation_type: FeeCalculationType
    default_rate: Decimal | None = Field(None, ge=0, le=100, description="Default percentage")
    default_amount: Decimal | None = Field(None, ge=0, description="Default flat amount")
    min_amount: Decimal | None = Field(None, ge=0)
    max_amount: Decimal | None = Field(None, ge=0)
    slab_config: dict[str, Any] | None = Field(
        None, description="Slab-based fee: [{from: 0, to: 1000000, rate: 1.5}, ...]"
    )
    gl_account_id: UUID | None = None
    tax_applicable: bool = False
    gst_rate: Decimal | None = Field(None, ge=0, le=100)
    hsn_sac_code: str | None = Field(None, max_length=20)


class FeeMasterCreate(FeeMasterBase):
    """Schema for creating fee master."""

    organization_id: UUID | None = None


class FeeMasterUpdate(CamelSchema):
    """Schema for updating fee master."""

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    fee_type: FeeType | None = None
    calculation_type: FeeCalculationType | None = None
    default_rate: Decimal | None = Field(None, ge=0, le=100)
    default_amount: Decimal | None = Field(None, ge=0)
    min_amount: Decimal | None = Field(None, ge=0)
    max_amount: Decimal | None = Field(None, ge=0)
    slab_config: dict[str, Any] | None = None
    gl_account_id: UUID | None = None
    tax_applicable: bool | None = None
    gst_rate: Decimal | None = Field(None, ge=0, le=100)
    hsn_sac_code: str | None = Field(None, max_length=20)
    is_active: bool | None = None


class FeeMasterResponse(FeeMasterBase):
    """Schema for fee master response."""

    id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    is_active: bool = True


# =============================================================================
# Product Fee Schemas
# =============================================================================


class ProductFeeBase(CamelSchema):
    """Base schema for product fee."""

    fee_master_id: UUID
    is_mandatory: bool = True
    is_waivable: bool = True
    max_waiver_percentage: Decimal = Field(default=Decimal("100"), ge=0, le=100)
    override_calculation_type: FeeCalculationType | None = None
    override_rate: Decimal | None = Field(None, ge=0, le=100)
    override_amount: Decimal | None = Field(None, ge=0)
    override_min_amount: Decimal | None = Field(None, ge=0)
    override_max_amount: Decimal | None = Field(None, ge=0)
    display_order: int = Field(default=0, ge=0)


class ProductFeeCreate(ProductFeeBase):
    """Schema for creating product fee."""

    product_id: UUID


class ProductFeeUpdate(CamelSchema):
    """Schema for updating product fee."""

    is_mandatory: bool | None = None
    is_waivable: bool | None = None
    max_waiver_percentage: Decimal | None = Field(None, ge=0, le=100)
    override_calculation_type: FeeCalculationType | None = None
    override_rate: Decimal | None = Field(None, ge=0, le=100)
    override_amount: Decimal | None = Field(None, ge=0)
    override_min_amount: Decimal | None = Field(None, ge=0)
    override_max_amount: Decimal | None = Field(None, ge=0)
    display_order: int | None = Field(None, ge=0)
    is_active: bool | None = None


class ProductFeeResponse(ProductFeeBase):
    """Schema for product fee response."""

    id: UUID
    product_id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    is_active: bool = True


# =============================================================================
# Document Checklist Schemas
# =============================================================================


class DocumentChecklistBase(CamelSchema):
    """Base schema for document checklist."""

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    category: DocumentCategory
    required_at_stage: DocumentStage
    is_mandatory: bool = True
    is_mandatory_for_disbursement: bool = False
    applicable_entity_types: list[EntityType] | None = None
    applicable_conditions: dict[str, Any] | None = None
    has_expiry: bool = False
    validity_months: int | None = Field(None, ge=0)
    renewal_alert_days: int | None = Field(None, ge=0)
    allowed_file_types: list[str] = ["pdf", "jpg", "jpeg", "png"]
    max_file_size_mb: int = Field(default=10, ge=1)
    min_file_count: int = Field(default=1, ge=1)
    max_file_count: int = Field(default=10, ge=1)
    requires_verification: bool = False
    verification_instructions: str | None = None
    sample_document_path: str | None = Field(None, max_length=500)
    help_text: str | None = None
    display_order: int = Field(default=0, ge=0)


class DocumentChecklistCreate(DocumentChecklistBase):
    """Schema for creating document checklist."""

    product_id: UUID


class DocumentChecklistUpdate(CamelSchema):
    """Schema for updating document checklist."""

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    category: DocumentCategory | None = None
    required_at_stage: DocumentStage | None = None
    is_mandatory: bool | None = None
    is_mandatory_for_disbursement: bool | None = None
    applicable_entity_types: list[EntityType] | None = None
    applicable_conditions: dict[str, Any] | None = None
    has_expiry: bool | None = None
    validity_months: int | None = Field(None, ge=0)
    renewal_alert_days: int | None = Field(None, ge=0)
    allowed_file_types: list[str] | None = None
    max_file_size_mb: int | None = Field(None, ge=1)
    min_file_count: int | None = Field(None, ge=1)
    max_file_count: int | None = Field(None, ge=1)
    requires_verification: bool | None = None
    verification_instructions: str | None = None
    sample_document_path: str | None = Field(None, max_length=500)
    help_text: str | None = None
    display_order: int | None = Field(None, ge=0)
    is_active: bool | None = None


class DocumentChecklistResponse(DocumentChecklistBase):
    """Schema for document checklist response."""

    id: UUID
    product_id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    is_active: bool = True


# =============================================================================
# Loan Product Schemas
# =============================================================================


class LoanProductBase(CamelSchema):
    """Base schema for loan product."""

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    category: ProductCategory
    sub_category: str | None = Field(None, max_length=100)

    # Amount Limits
    min_amount: Decimal = Field(..., ge=0)
    max_amount: Decimal = Field(..., ge=0)

    # Tenure
    min_tenure_months: int = Field(..., ge=1)
    max_tenure_months: int = Field(..., ge=1)
    default_tenure_months: int | None = Field(None, ge=1)
    allows_moratorium: bool = False
    max_moratorium_months: int | None = Field(None, ge=0)

    # Interest
    interest_type: InterestType
    base_rate_id: UUID | None = None
    min_spread_bps: int = Field(default=0, ge=0)
    max_spread_bps: int = Field(default=500, ge=0)
    default_spread_bps: int = Field(default=200, ge=0)
    min_effective_rate: Decimal | None = Field(None, ge=0, le=100)
    max_effective_rate: Decimal | None = Field(None, ge=0, le=100)
    rate_reset_frequency: RateResetFrequency | None = None
    day_count_convention: DayCountConvention = DayCountConvention.ACT_365

    # Repayment
    default_repayment_frequency: RepaymentFrequency = RepaymentFrequency.MONTHLY
    allowed_repayment_modes: list[RepaymentMode] = [RepaymentMode.EMI]
    default_repayment_mode: RepaymentMode = RepaymentMode.EMI

    # Prepayment
    allows_prepayment: bool = True
    prepayment_lock_in_months: int | None = Field(None, ge=0)
    allows_foreclosure: bool = True
    foreclosure_lock_in_months: int | None = Field(None, ge=0)

    # Eligibility
    eligible_entity_types: list[EntityType] = []
    min_vintage_months: int | None = Field(None, ge=0)
    min_turnover: Decimal | None = Field(None, ge=0)
    min_rating_grade: str | None = Field(None, max_length=10)
    min_cibil_score: int | None = Field(None, ge=300, le=900)

    # Collateral
    requires_collateral: bool = True
    min_collateral_coverage: Decimal | None = Field(None, ge=0)
    requires_guarantee: bool = False

    # Effective Date (required)
    effective_from: date

    @model_validator(mode="after")
    def validate_amounts_and_tenure(self):
        if self.max_amount < self.min_amount:
            raise ValueError("max_amount must be >= min_amount")
        if self.max_tenure_months < self.min_tenure_months:
            raise ValueError("max_tenure_months must be >= min_tenure_months")
        return self


class LoanProductCreate(LoanProductBase):
    """Schema for creating loan product."""

    organization_id: UUID | None = None


class LoanProductUpdate(CamelSchema):
    """Schema for updating loan product."""

    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    category: ProductCategory | None = None
    sub_category: str | None = Field(None, max_length=100)

    # Amount Limits
    min_amount: Decimal | None = Field(None, ge=0)
    max_amount: Decimal | None = Field(None, ge=0)

    # Tenure
    min_tenure_months: int | None = Field(None, ge=1)
    max_tenure_months: int | None = Field(None, ge=1)
    default_tenure_months: int | None = Field(None, ge=1)
    allows_moratorium: bool | None = None
    max_moratorium_months: int | None = Field(None, ge=0)

    # Interest
    interest_type: InterestType | None = None
    base_rate_id: UUID | None = None
    min_spread_bps: int | None = Field(None, ge=0)
    max_spread_bps: int | None = Field(None, ge=0)
    default_spread_bps: int | None = Field(None, ge=0)
    min_effective_rate: Decimal | None = Field(None, ge=0, le=100)
    max_effective_rate: Decimal | None = Field(None, ge=0, le=100)
    rate_reset_frequency: RateResetFrequency | None = None
    day_count_convention: DayCountConvention | None = None

    # Repayment
    default_repayment_frequency: RepaymentFrequency | None = None
    allowed_repayment_modes: list[RepaymentMode] | None = None
    default_repayment_mode: RepaymentMode | None = None

    # Prepayment
    allows_prepayment: bool | None = None
    prepayment_lock_in_months: int | None = Field(None, ge=0)
    allows_foreclosure: bool | None = None
    foreclosure_lock_in_months: int | None = Field(None, ge=0)

    # Eligibility
    eligible_entity_types: list[EntityType] | None = None
    min_vintage_months: int | None = Field(None, ge=0)
    min_turnover: Decimal | None = Field(None, ge=0)
    min_rating_grade: str | None = Field(None, max_length=10)
    min_cibil_score: int | None = Field(None, ge=300, le=900)

    # Collateral
    requires_collateral: bool | None = None
    min_collateral_coverage: Decimal | None = Field(None, ge=0)
    requires_guarantee: bool | None = None

    is_active: bool | None = None


class LoanProductResponse(LoanProductBase):
    """Schema for loan product response."""

    id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: datetime | None = None
    is_active: bool = True


class LoanProductListResponse(CamelSchema):
    """Slim list response for loan products (camelCase wire format).

    Monetary + rate fields stay Decimal per CLAUDE.md §6.2.
    """

    id: UUID
    code: str
    name: str
    category: ProductCategory
    interest_type: InterestType
    min_amount: Decimal
    max_amount: Decimal
    min_tenure_months: int
    max_tenure_months: int
    is_active: bool = True
    base_rate_value: Decimal | None = None
    spread_bps: int = 0
    processing_fee_percent: Decimal | None = None
    status: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _flatten(cls, obj):
        if isinstance(obj, dict):
            return obj
        # `obj` is a LoanProduct ORM instance — flatten the base_rate join.
        base_rate = getattr(obj, "base_rate", None)
        base_rate_value = getattr(base_rate, "current_rate", None) if base_rate else None
        return {
            "id": obj.id,
            "code": obj.code,
            "name": obj.name,
            "category": obj.category,
            "interest_type": obj.interest_type,
            "min_amount": obj.min_amount,
            "max_amount": obj.max_amount,
            "min_tenure_months": obj.min_tenure_months,
            "max_tenure_months": obj.max_tenure_months,
            "is_active": bool(obj.is_active and obj.is_active_for_new_loans),
            "base_rate_value": base_rate_value,
            "spread_bps": getattr(obj, "default_spread_bps", 0) or 0,
            "processing_fee_percent": None,
            "status": "ACTIVE" if obj.is_active and obj.is_active_for_new_loans else "INACTIVE",
        }


class LoanProductDetailResponse(LoanProductResponse):
    """Schema for detailed loan product response with related data."""

    fees: list[ProductFeeResponse] = []
    document_checklist: list[DocumentChecklistResponse] = []
    base_rate: InterestRateResponse | None = None
