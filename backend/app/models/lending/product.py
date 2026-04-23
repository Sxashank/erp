"""Loan product models for the lending module."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, List
from uuid import UUID

from sqlalchemy import (
    Boolean, Date, Enum, ForeignKey, Integer,
    Numeric, String, Text, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.lending.enums import (
    ProductCategory, InterestType, RateResetFrequency,
    RepaymentFrequency, RepaymentMode, DayCountConvention,
    FeeType, FeeCalculationType, FeeCollectionStage,
    DocumentCategory, DocumentStage
)


if TYPE_CHECKING:
    from app.models.masters.organization import Organization


class LoanProduct(BaseModel):
    """Loan product configuration."""

    __tablename__ = "los_loan_product"

    # Organization scope
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Organization this product belongs to",
    )

    # Product identification
    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Product code e.g., 'TL_SECURED', 'WC_CC'",
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Product name",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Product description",
    )
    category: Mapped[ProductCategory] = mapped_column(
        Enum(ProductCategory),
        nullable=False,
        index=True,
        comment="Product category - TERM_LOAN, WORKING_CAPITAL, etc.",
    )
    sub_category: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Product sub-category for further classification",
    )

    # Loan amount limits
    min_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("100000"),
        comment="Minimum loan amount",
    )
    max_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        default=Decimal("100000000"),
        comment="Maximum loan amount",
    )
    default_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Default loan amount (for pre-filling)",
    )

    # Tenure limits (in months)
    min_tenure_months: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=12,
        comment="Minimum tenure in months",
    )
    max_tenure_months: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=120,
        comment="Maximum tenure in months",
    )
    default_tenure_months: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Default tenure (for pre-filling)",
    )

    # Moratorium
    allows_moratorium: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Is moratorium allowed?",
    )
    max_moratorium_months: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=12,
        comment="Maximum moratorium period in months",
    )
    moratorium_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="INTEREST_ONLY",
        comment="FULL (no EMI), PRINCIPAL_ONLY, INTEREST_ONLY",
    )

    # Interest configuration
    interest_type: Mapped[InterestType] = mapped_column(
        Enum(InterestType),
        nullable=False,
        default=InterestType.FLOATING,
        comment="FIXED or FLOATING",
    )
    base_rate_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_interest_rate.id", ondelete="SET NULL"),
        nullable=True,
        comment="Default base rate for floating loans",
    )
    min_spread_bps: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Minimum spread over base rate (basis points)",
    )
    max_spread_bps: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=500,
        comment="Maximum spread over base rate (basis points)",
    )
    default_spread_bps: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=200,
        comment="Default spread (for pre-filling)",
    )
    min_effective_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("8.00"),
        comment="Minimum effective interest rate %",
    )
    max_effective_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("24.00"),
        comment="Maximum effective interest rate %",
    )
    rate_reset_frequency: Mapped[Optional[RateResetFrequency]] = mapped_column(
        Enum(RateResetFrequency),
        nullable=True,
        comment="Rate reset frequency for floating loans",
    )

    # Calculation conventions
    day_count_convention: Mapped[DayCountConvention] = mapped_column(
        Enum(DayCountConvention),
        nullable=False,
        default=DayCountConvention.ACT_365,
        comment="Day count convention - ACT_365, ACT_360, 30_360",
    )
    interest_calculation_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="REDUCING_BALANCE",
        comment="REDUCING_BALANCE, FLAT_RATE",
    )
    interest_compounding: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="MONTHLY",
        comment="Interest compounding frequency",
    )

    # Repayment configuration
    allowed_repayment_frequencies: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=["MONTHLY", "QUARTERLY"],
        comment="Allowed repayment frequencies",
    )
    default_repayment_frequency: Mapped[RepaymentFrequency] = mapped_column(
        Enum(RepaymentFrequency),
        nullable=False,
        default=RepaymentFrequency.MONTHLY,
        comment="Default repayment frequency",
    )
    allowed_repayment_modes: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=["EMI", "STRUCTURED"],
        comment="Allowed repayment modes",
    )
    default_repayment_mode: Mapped[RepaymentMode] = mapped_column(
        Enum(RepaymentMode),
        nullable=False,
        default=RepaymentMode.EMI,
        comment="Default repayment mode",
    )

    # Prepayment/Foreclosure
    allows_prepayment: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Is prepayment allowed?",
    )
    prepayment_lock_in_months: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=12,
        comment="Lock-in period before prepayment allowed",
    )
    allows_foreclosure: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Is foreclosure allowed?",
    )
    foreclosure_lock_in_months: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=12,
        comment="Lock-in period before foreclosure allowed",
    )

    # Security requirements
    requires_collateral: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Is collateral mandatory?",
    )
    min_collateral_coverage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("100"),
        comment="Minimum collateral coverage %",
    )
    allowed_security_types: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Allowed security types",
    )
    requires_guarantee: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Is guarantee mandatory?",
    )

    # Eligibility criteria
    eligible_entity_types: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=["CORPORATE", "LLP", "PARTNERSHIP"],
        comment="Eligible entity types",
    )
    min_vintage_months: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=24,
        comment="Minimum business vintage in months",
    )
    min_turnover: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Minimum annual turnover",
    )
    min_rating_grade: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="Minimum internal rating required",
    )
    min_cibil_score: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Minimum CIBIL score for promoters",
    )

    # Financial ratios required
    max_debt_equity_ratio: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Maximum debt to equity ratio",
    )
    min_current_ratio: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Minimum current ratio",
    )
    min_dscr: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Minimum DSCR",
    )

    # Disbursement
    disbursement_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="SINGLE",
        comment="SINGLE, MULTIPLE, TRANCHE_BASED",
    )
    max_tranches: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Maximum number of tranches",
    )
    allows_partial_disbursement: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Allow partial disbursement?",
    )
    disbursement_validity_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=180,
        comment="Sanction validity for disbursement in days",
    )

    # Workflow
    approval_workflow_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="Default approval workflow",
    )

    # GL mapping
    gl_mapping: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="GL account mapping for this product",
    )

    # Status
    is_active_for_new_loans: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Accept new loan applications?",
    )
    effective_from: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Product effective from date",
    )
    effective_until: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Product effective until date",
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )
    base_rate: Mapped[Optional["InterestRate"]] = relationship(
        "InterestRate",
        lazy="selectin",
    )
    fee_configurations: Mapped[List["ProductFee"]] = relationship(
        "ProductFee",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    document_checklist: Mapped[List["DocumentChecklist"]] = relationship(
        "DocumentChecklist",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="noload",
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_loan_product_org_code"),
        Index("ix_los_loan_product_org_cat", "organization_id", "category"),
        Index("ix_los_loan_product_org_active", "organization_id", "is_active_for_new_loans"),
    )

    def __repr__(self) -> str:
        return f"<LoanProduct(code={self.code}, category={self.category})>"


class InterestRate(BaseModel):
    """Base interest rate master (MCLR, SMFC_BR, etc.)."""

    __tablename__ = "los_interest_rate"

    # Organization scope
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Organization",
    )

    # Rate identification
    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Rate code e.g., 'SMFC_BR', 'MCLR_1Y'",
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Rate name",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Rate description",
    )

    # Rate type
    rate_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="BASE_RATE",
        comment="BASE_RATE, MCLR, PLR, EXTERNAL_BENCHMARK",
    )
    benchmark_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="External benchmark name if applicable",
    )

    # Current rate
    current_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Current interest rate %",
    )
    effective_from: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Rate effective from date",
    )

    # Rate history
    previous_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Previous rate %",
    )
    previous_effective_from: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Previous rate effective date",
    )

    # Reset frequency
    reset_frequency: Mapped[Optional[RateResetFrequency]] = mapped_column(
        Enum(RateResetFrequency),
        nullable=True,
        comment="How often this rate is reviewed",
    )
    next_review_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Next rate review date",
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )
    rate_history: Mapped[List["InterestRateHistory"]] = relationship(
        "InterestRateHistory",
        back_populates="interest_rate",
        cascade="all, delete-orphan",
        lazy="noload",
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_interest_rate_org_code"),
        Index("ix_los_interest_rate_org_date", "organization_id", "effective_from"),
    )

    def __repr__(self) -> str:
        return f"<InterestRate(code={self.code}, rate={self.current_rate}%)>"


class InterestRateHistory(BaseModel):
    """Historical interest rate changes."""

    __tablename__ = "los_interest_rate_history"

    # Parent rate
    interest_rate_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_interest_rate.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent interest rate",
    )

    # Rate and period
    rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Interest rate %",
    )
    effective_from: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Rate effective from",
    )
    effective_until: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Rate effective until",
    )

    # Change details
    change_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Reason for rate change",
    )
    approved_by: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Approved by",
    )
    approval_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Approval reference number",
    )

    # Relationships
    interest_rate: Mapped["InterestRate"] = relationship(
        "InterestRate",
        back_populates="rate_history",
    )

    __table_args__ = (
        Index("ix_los_rate_history_rate_date", "interest_rate_id", "effective_from"),
    )

    def __repr__(self) -> str:
        return f"<InterestRateHistory(rate={self.rate}%, from={self.effective_from})>"


class FeeMaster(BaseModel):
    """Fee type master configuration."""

    __tablename__ = "los_fee_master"

    # Organization scope
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Organization",
    )

    # Fee identification
    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Fee code e.g., 'PROCESSING', 'PREPAYMENT'",
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Fee name",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Fee description",
    )
    fee_type: Mapped[FeeType] = mapped_column(
        Enum(FeeType),
        nullable=False,
        index=True,
        comment="Fee type - PROCESSING, PREPAYMENT, etc.",
    )

    # Default configuration
    calculation_type: Mapped[FeeCalculationType] = mapped_column(
        Enum(FeeCalculationType),
        nullable=False,
        default=FeeCalculationType.PERCENTAGE,
        comment="PERCENTAGE, FLAT, SLAB",
    )
    default_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Default rate/percentage",
    )
    default_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
        comment="Default flat amount",
    )
    min_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
        comment="Minimum fee amount",
    )
    max_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
        comment="Maximum fee amount (cap)",
    )

    # Slab configuration (for SLAB type)
    slabs: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Slab configuration for slab-based fees",
    )

    # Collection
    collection_stage: Mapped[FeeCollectionStage] = mapped_column(
        Enum(FeeCollectionStage),
        nullable=False,
        default=FeeCollectionStage.DISBURSEMENT,
        comment="When is this fee collected?",
    )
    is_refundable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Is fee refundable?",
    )
    deduct_from_disbursement: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Deduct from disbursement amount?",
    )

    # Tax
    is_taxable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Is GST applicable?",
    )
    gst_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("18.00"),
        comment="GST rate %",
    )
    hsn_sac_code: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="HSN/SAC code for GST",
    )

    # GL mapping
    income_gl_account: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Income GL account code",
    )
    receivable_gl_account: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Receivable GL account code",
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_fee_master_org_code"),
        Index("ix_los_fee_master_org_type", "organization_id", "fee_type"),
    )

    def __repr__(self) -> str:
        return f"<FeeMaster(code={self.code}, type={self.fee_type})>"


class ProductFee(BaseModel):
    """Fee configuration for a specific product."""

    __tablename__ = "los_product_fee"

    # Parent product
    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_loan_product.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent product",
    )

    # Fee master reference
    fee_master_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_fee_master.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Fee master",
    )

    # Product-specific overrides
    is_mandatory: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Is this fee mandatory for this product?",
    )
    is_waivable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Can this fee be waived?",
    )
    max_waiver_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("100"),
        comment="Maximum waiver percentage allowed",
    )

    # Override calculation
    override_calculation_type: Mapped[Optional[FeeCalculationType]] = mapped_column(
        Enum(FeeCalculationType),
        nullable=True,
        comment="Override calculation type for this product",
    )
    override_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Override rate for this product",
    )
    override_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
        comment="Override flat amount for this product",
    )
    override_min_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
        comment="Override minimum for this product",
    )
    override_max_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
        comment="Override maximum for this product",
    )

    # Display
    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Display order",
    )

    # Relationships
    product: Mapped["LoanProduct"] = relationship(
        "LoanProduct",
        back_populates="fee_configurations",
    )
    fee_master: Mapped["FeeMaster"] = relationship(
        "FeeMaster",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("product_id", "fee_master_id", name="uq_product_fee"),
        Index("ix_los_product_fee_product", "product_id"),
    )

    def __repr__(self) -> str:
        return f"<ProductFee(product={self.product_id}, fee={self.fee_master_id})>"


class DocumentChecklist(BaseModel):
    """Document checklist for a product."""

    __tablename__ = "los_document_checklist"

    # Parent product
    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_loan_product.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent product",
    )

    # Document identification
    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Document code",
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Document name",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Document description/purpose",
    )

    # Category and stage
    category: Mapped[DocumentCategory] = mapped_column(
        Enum(DocumentCategory),
        nullable=False,
        index=True,
        comment="Document category - KYC, FINANCIAL, LEGAL, etc.",
    )
    required_at_stage: Mapped[DocumentStage] = mapped_column(
        Enum(DocumentStage),
        nullable=False,
        index=True,
        comment="Stage at which document is required",
    )

    # Requirements
    is_mandatory: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Is document mandatory?",
    )
    is_mandatory_for_disbursement: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Must be present before disbursement?",
    )

    # Applicability
    applicable_entity_types: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Applicable entity types (null = all)",
    )
    applicable_conditions: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Conditions when this document is required",
    )

    # Validity
    has_expiry: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Does document have expiry?",
    )
    validity_months: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Validity period in months",
    )
    renewal_alert_days: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Days before expiry to alert",
    )

    # File requirements
    allowed_file_types: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=["pdf", "jpg", "jpeg", "png"],
        comment="Allowed file extensions",
    )
    max_file_size_mb: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=10,
        comment="Maximum file size in MB",
    )
    min_file_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Minimum number of files",
    )
    max_file_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=10,
        comment="Maximum number of files",
    )

    # Verification
    requires_verification: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Requires manual verification?",
    )
    verification_instructions: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Instructions for verification",
    )

    # Display
    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Display order",
    )
    help_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Help text for user",
    )
    sample_document_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Path to sample document",
    )

    # Relationships
    product: Mapped["LoanProduct"] = relationship(
        "LoanProduct",
        back_populates="document_checklist",
    )

    __table_args__ = (
        UniqueConstraint("product_id", "code", name="uq_doc_checklist_product_code"),
        Index("ix_los_doc_checklist_product_stage", "product_id", "required_at_stage"),
        Index("ix_los_doc_checklist_product_cat", "product_id", "category"),
    )

    def __repr__(self) -> str:
        return f"<DocumentChecklist(code={self.code}, stage={self.required_at_stage})>"
