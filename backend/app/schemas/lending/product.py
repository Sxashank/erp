"""Loan Product schemas for the lending module."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import Field, model_validator

from app.schemas.base import BaseSchema
from app.models.lending.enums import (
    ProductCategory,
    InterestType,
    RateResetFrequency,
    RepaymentFrequency,
    RepaymentMode,
    DayCountConvention,
    FeeType,
    FeeCalculationType,
    FeeCollectionStage,
    DocumentCategory,
    DocumentStage,
    EntityType,
)


# =============================================================================
# Interest Rate Schemas
# =============================================================================


class InterestRateBase(BaseSchema):
    """Base schema for interest rate."""

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    rate_type: str = Field(default="BASE_RATE", max_length=30)
    current_rate: Decimal = Field(..., ge=0, le=100)
    effective_from: date
    effective_till: Optional[date] = None
    benchmark_rate: Optional[str] = Field(None, max_length=50, description="e.g., REPO, MCLR")
    spread_over_benchmark_bps: Optional[int] = Field(None, ge=0)


class InterestRateCreate(InterestRateBase):
    """Schema for creating interest rate."""

    organization_id: UUID


class InterestRateUpdate(BaseSchema):
    """Schema for updating interest rate."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    rate_type: Optional[str] = Field(None, max_length=30)
    current_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    effective_from: Optional[date] = None
    effective_till: Optional[date] = None
    benchmark_rate: Optional[str] = Field(None, max_length=50)
    spread_over_benchmark_bps: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class InterestRateResponse(InterestRateBase):
    """Schema for interest rate response."""

    id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True


# =============================================================================
# Fee Master Schemas
# =============================================================================


class FeeMasterBase(BaseSchema):
    """Base schema for fee master."""

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    fee_type: FeeType
    calculation_type: FeeCalculationType
    default_rate: Optional[Decimal] = Field(None, ge=0, le=100, description="Default percentage")
    default_amount: Optional[Decimal] = Field(None, ge=0, description="Default flat amount")
    min_amount: Optional[Decimal] = Field(None, ge=0)
    max_amount: Optional[Decimal] = Field(None, ge=0)
    slab_config: Optional[Dict[str, Any]] = Field(
        None,
        description="Slab-based fee: [{from: 0, to: 1000000, rate: 1.5}, ...]"
    )
    gl_account_id: Optional[UUID] = None
    tax_applicable: bool = False
    gst_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    hsn_sac_code: Optional[str] = Field(None, max_length=20)


class FeeMasterCreate(FeeMasterBase):
    """Schema for creating fee master."""

    organization_id: UUID


class FeeMasterUpdate(BaseSchema):
    """Schema for updating fee master."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    fee_type: Optional[FeeType] = None
    calculation_type: Optional[FeeCalculationType] = None
    default_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    default_amount: Optional[Decimal] = Field(None, ge=0)
    min_amount: Optional[Decimal] = Field(None, ge=0)
    max_amount: Optional[Decimal] = Field(None, ge=0)
    slab_config: Optional[Dict[str, Any]] = None
    gl_account_id: Optional[UUID] = None
    tax_applicable: Optional[bool] = None
    gst_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    hsn_sac_code: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None


class FeeMasterResponse(FeeMasterBase):
    """Schema for fee master response."""

    id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True


# =============================================================================
# Product Fee Schemas
# =============================================================================


class ProductFeeBase(BaseSchema):
    """Base schema for product fee."""

    fee_master_id: UUID
    is_mandatory: bool = True
    is_waivable: bool = True
    max_waiver_percentage: Decimal = Field(default=Decimal("100"), ge=0, le=100)
    override_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    override_amount: Optional[Decimal] = Field(None, ge=0)
    display_order: int = Field(default=0, ge=0)


class ProductFeeCreate(ProductFeeBase):
    """Schema for creating product fee."""

    product_id: UUID


class ProductFeeUpdate(BaseSchema):
    """Schema for updating product fee."""

    is_mandatory: Optional[bool] = None
    is_waivable: Optional[bool] = None
    max_waiver_percentage: Optional[Decimal] = Field(None, ge=0, le=100)
    override_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    override_amount: Optional[Decimal] = Field(None, ge=0)
    display_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class ProductFeeResponse(ProductFeeBase):
    """Schema for product fee response."""

    id: UUID
    product_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True


# =============================================================================
# Document Checklist Schemas
# =============================================================================


class DocumentChecklistBase(BaseSchema):
    """Base schema for document checklist."""

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: DocumentCategory
    required_at_stage: DocumentStage
    is_mandatory: bool = True
    is_mandatory_for_disbursement: bool = False
    applicable_entity_types: Optional[List[EntityType]] = None
    sample_document_path: Optional[str] = Field(None, max_length=500)
    help_text: Optional[str] = None
    display_order: int = Field(default=0, ge=0)


class DocumentChecklistCreate(DocumentChecklistBase):
    """Schema for creating document checklist."""

    product_id: UUID


class DocumentChecklistUpdate(BaseSchema):
    """Schema for updating document checklist."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[DocumentCategory] = None
    required_at_stage: Optional[DocumentStage] = None
    is_mandatory: Optional[bool] = None
    is_mandatory_for_disbursement: Optional[bool] = None
    applicable_entity_types: Optional[List[EntityType]] = None
    sample_document_path: Optional[str] = Field(None, max_length=500)
    help_text: Optional[str] = None
    display_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class DocumentChecklistResponse(DocumentChecklistBase):
    """Schema for document checklist response."""

    id: UUID
    product_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True


# =============================================================================
# Loan Product Schemas
# =============================================================================


class LoanProductBase(BaseSchema):
    """Base schema for loan product."""

    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: ProductCategory
    sub_category: Optional[str] = Field(None, max_length=100)

    # Amount Limits
    min_amount: Decimal = Field(..., ge=0)
    max_amount: Decimal = Field(..., ge=0)

    # Tenure
    min_tenure_months: int = Field(..., ge=1)
    max_tenure_months: int = Field(..., ge=1)
    default_tenure_months: Optional[int] = Field(None, ge=1)
    allows_moratorium: bool = False
    max_moratorium_months: Optional[int] = Field(None, ge=0)

    # Interest
    interest_type: InterestType
    base_rate_id: Optional[UUID] = None
    min_spread_bps: int = Field(default=0, ge=0)
    max_spread_bps: int = Field(default=500, ge=0)
    default_spread_bps: int = Field(default=200, ge=0)
    min_effective_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    max_effective_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    rate_reset_frequency: Optional[RateResetFrequency] = None
    day_count_convention: DayCountConvention = DayCountConvention.ACT_365

    # Repayment
    default_repayment_frequency: RepaymentFrequency = RepaymentFrequency.MONTHLY
    allowed_repayment_modes: List[RepaymentMode] = [RepaymentMode.EMI]
    default_repayment_mode: RepaymentMode = RepaymentMode.EMI

    # Prepayment
    allows_prepayment: bool = True
    prepayment_lock_in_months: Optional[int] = Field(None, ge=0)
    allows_foreclosure: bool = True
    foreclosure_lock_in_months: Optional[int] = Field(None, ge=0)

    # Eligibility
    eligible_entity_types: List[EntityType] = []
    min_vintage_months: Optional[int] = Field(None, ge=0)
    min_turnover: Optional[Decimal] = Field(None, ge=0)
    min_rating_grade: Optional[str] = Field(None, max_length=10)
    min_cibil_score: Optional[int] = Field(None, ge=300, le=900)

    # Collateral
    requires_collateral: bool = True
    min_collateral_coverage: Optional[Decimal] = Field(None, ge=0)
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

    organization_id: UUID


class LoanProductUpdate(BaseSchema):
    """Schema for updating loan product."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[ProductCategory] = None
    sub_category: Optional[str] = Field(None, max_length=100)

    # Amount Limits
    min_amount: Optional[Decimal] = Field(None, ge=0)
    max_amount: Optional[Decimal] = Field(None, ge=0)

    # Tenure
    min_tenure_months: Optional[int] = Field(None, ge=1)
    max_tenure_months: Optional[int] = Field(None, ge=1)
    default_tenure_months: Optional[int] = Field(None, ge=1)
    allows_moratorium: Optional[bool] = None
    max_moratorium_months: Optional[int] = Field(None, ge=0)

    # Interest
    interest_type: Optional[InterestType] = None
    base_rate_id: Optional[UUID] = None
    min_spread_bps: Optional[int] = Field(None, ge=0)
    max_spread_bps: Optional[int] = Field(None, ge=0)
    default_spread_bps: Optional[int] = Field(None, ge=0)
    min_effective_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    max_effective_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    rate_reset_frequency: Optional[RateResetFrequency] = None
    day_count_convention: Optional[DayCountConvention] = None

    # Repayment
    default_repayment_frequency: Optional[RepaymentFrequency] = None
    allowed_repayment_modes: Optional[List[RepaymentMode]] = None
    default_repayment_mode: Optional[RepaymentMode] = None

    # Prepayment
    allows_prepayment: Optional[bool] = None
    prepayment_lock_in_months: Optional[int] = Field(None, ge=0)
    allows_foreclosure: Optional[bool] = None
    foreclosure_lock_in_months: Optional[int] = Field(None, ge=0)

    # Eligibility
    eligible_entity_types: Optional[List[EntityType]] = None
    min_vintage_months: Optional[int] = Field(None, ge=0)
    min_turnover: Optional[Decimal] = Field(None, ge=0)
    min_rating_grade: Optional[str] = Field(None, max_length=10)
    min_cibil_score: Optional[int] = Field(None, ge=300, le=900)

    # Collateral
    requires_collateral: Optional[bool] = None
    min_collateral_coverage: Optional[Decimal] = Field(None, ge=0)
    requires_guarantee: Optional[bool] = None

    is_active: Optional[bool] = None


class LoanProductResponse(LoanProductBase):
    """Schema for loan product response."""

    id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool = True


class LoanProductListResponse(BaseSchema):
    """Schema for loan product list response (lightweight)."""

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


class LoanProductDetailResponse(LoanProductResponse):
    """Schema for detailed loan product response with related data."""

    fees: List[ProductFeeResponse] = []
    document_checklist: List[DocumentChecklistResponse] = []
    base_rate: Optional[InterestRateResponse] = None
