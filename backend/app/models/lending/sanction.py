"""Loan sanction models for the lending module."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, List
from uuid import UUID

from sqlalchemy import (
    Boolean, Date, DateTime, Enum, ForeignKey, Integer,
    Numeric, String, Text, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.lending.enums import (
    SanctionStatus, ConditionType, ConditionCategory,
    ConditionComplianceStatus, SecurityCategory, SecurityType,
    ChargeType, SecurityStatus, InterestType, RateResetFrequency,
    RepaymentFrequency, RepaymentMode, DayCountConvention
)


if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.lending.entity import Entity
    from app.models.lending.product import LoanProduct, InterestRate
    from app.models.lending.application import LoanApplication
    from app.models.workflow import WorkflowInstance


class LoanSanction(BaseModel):
    """Loan sanction terms and conditions."""

    __tablename__ = "los_loan_sanction"

    # Organization scope
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Organization",
    )

    # References
    application_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_loan_application.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Parent application",
    )
    entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_entity.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Borrower entity",
    )
    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_loan_product.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Loan product",
    )

    # Sanction identification
    sanction_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Sanction number e.g., 'SMFC/SL/2025/00001'",
    )
    sanction_letter_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Sanction letter reference number",
    )

    # Sanction dates
    sanction_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Date of sanction",
    )
    validity_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Sanction validity expiry date",
    )
    first_disbursement_deadline: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Deadline for first disbursement",
    )

    # Sanction amounts
    sanctioned_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        comment="Sanctioned loan amount",
    )
    requested_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        comment="Originally requested amount",
    )
    approved_project_cost: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Approved project cost (for project finance)",
    )

    # Tenure
    tenure_months: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Sanctioned tenure in months",
    )
    moratorium_months: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Moratorium period in months",
    )
    moratorium_type: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="FULL, PRINCIPAL_ONLY, INTEREST_ONLY",
    )

    # Interest terms
    interest_type: Mapped[InterestType] = mapped_column(
        Enum(InterestType),
        nullable=False,
        comment="FIXED or FLOATING",
    )
    base_rate_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_interest_rate.id", ondelete="RESTRICT"),
        nullable=True,
        comment="Base rate for floating loans",
    )
    base_rate_at_sanction: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Base rate at time of sanction",
    )
    spread_bps: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Spread over base rate in basis points",
    )
    effective_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Effective interest rate at sanction",
    )
    rate_reset_frequency: Mapped[Optional[RateResetFrequency]] = mapped_column(
        Enum(RateResetFrequency),
        nullable=True,
        comment="Rate reset frequency for floating",
    )
    first_rate_reset_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="First rate reset date",
    )

    # Penal interest
    penal_interest_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("2.00"),
        comment="Penal interest rate % over regular rate",
    )

    # Repayment terms
    repayment_frequency: Mapped[RepaymentFrequency] = mapped_column(
        Enum(RepaymentFrequency),
        nullable=False,
        comment="Repayment frequency",
    )
    repayment_mode: Mapped[RepaymentMode] = mapped_column(
        Enum(RepaymentMode),
        nullable=False,
        comment="Repayment mode - EMI, STRUCTURED, BULLET, etc.",
    )
    repayment_start_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Expected repayment start date",
    )
    day_count_convention: Mapped[DayCountConvention] = mapped_column(
        Enum(DayCountConvention),
        nullable=False,
        default=DayCountConvention.ACT_365,
        comment="Day count convention",
    )

    # Structured repayment (if not EMI)
    principal_schedule: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Custom principal repayment schedule",
    )

    # Prepayment/Foreclosure terms
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
        comment="Lock-in period before prepayment",
    )
    prepayment_penalty_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Prepayment penalty % on prepaid amount",
    )
    allows_foreclosure: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Is foreclosure allowed?",
    )
    foreclosure_penalty_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Foreclosure penalty %",
    )

    # Disbursement terms
    disbursement_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="SINGLE",
        comment="SINGLE, MULTIPLE, TRANCHE_BASED, MILESTONE_BASED",
    )
    max_tranches: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Maximum number of tranches",
    )

    # Status and workflow
    status: Mapped[SanctionStatus] = mapped_column(
        Enum(SanctionStatus),
        nullable=False,
        default=SanctionStatus.DRAFT,
        index=True,
        comment="Sanction status",
    )
    workflow_instance_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("wf_workflow_instance.id", ondelete="SET NULL"),
        nullable=True,
        comment="Approval workflow instance",
    )

    # Approval details
    approved_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="Final approver",
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Approval timestamp",
    )
    approval_authority: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Approval authority (committee, designation)",
    )
    approval_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Committee meeting/note reference",
    )

    # Borrower acceptance
    acceptance_required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Is borrower acceptance required?",
    )
    acceptance_deadline: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Deadline for borrower acceptance",
    )
    accepted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Acceptance timestamp",
    )
    acceptance_document_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Path to signed acceptance letter",
    )

    # Amendment tracking
    is_amendment: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Is this an amendment to original sanction?",
    )
    original_sanction_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_loan_sanction.id", ondelete="SET NULL"),
        nullable=True,
        comment="Original sanction if this is amendment",
    )
    amendment_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Reason for amendment",
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Sanction version number",
    )

    # Internal rating at sanction
    entity_rating: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="Entity rating at sanction",
    )

    # Special terms
    special_terms: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Special terms and conditions",
    )

    # Documents
    sanction_letter_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Path to generated sanction letter",
    )
    agreement_draft_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Path to loan agreement draft",
    )

    # Remarks
    remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Internal remarks",
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )
    application: Mapped["LoanApplication"] = relationship(
        "LoanApplication",
        back_populates="sanctions",
        lazy="selectin",
    )
    entity: Mapped["Entity"] = relationship(
        "Entity",
        lazy="selectin",
    )
    product: Mapped["LoanProduct"] = relationship(
        "LoanProduct",
        lazy="selectin",
    )
    base_rate: Mapped[Optional["InterestRate"]] = relationship(
        "InterestRate",
        lazy="selectin",
    )
    workflow_instance: Mapped[Optional["WorkflowInstance"]] = relationship(
        "WorkflowInstance",
        lazy="selectin",
    )
    original_sanction: Mapped[Optional["LoanSanction"]] = relationship(
        "LoanSanction",
        remote_side="LoanSanction.id",
        lazy="selectin",
    )
    conditions: Mapped[List["SanctionCondition"]] = relationship(
        "SanctionCondition",
        back_populates="sanction",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    securities: Mapped[List["LoanSecurity"]] = relationship(
        "LoanSecurity",
        back_populates="sanction",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "sanction_number", name="uq_sanction_org_number"),
        Index("ix_los_sanction_org_status", "organization_id", "status"),
        Index("ix_los_sanction_app", "application_id"),
        Index("ix_los_sanction_entity", "entity_id"),
        Index("ix_los_sanction_date", "sanction_date"),
    )

    def __repr__(self) -> str:
        return f"<LoanSanction(number={self.sanction_number}, amount={self.sanctioned_amount}, status={self.status})>"


class SanctionCondition(BaseModel):
    """Conditions attached to a sanction."""

    __tablename__ = "los_sanction_condition"

    # Parent sanction
    sanction_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_loan_sanction.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent sanction",
    )

    # Condition identification
    condition_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Condition sequence number",
    )
    condition_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Standard condition code if from master",
    )

    # Condition type and category
    condition_type: Mapped[ConditionType] = mapped_column(
        Enum(ConditionType),
        nullable=False,
        index=True,
        comment="PRE_DISBURSEMENT, POST_DISBURSEMENT, ONGOING, EVENT_BASED",
    )
    category: Mapped[ConditionCategory] = mapped_column(
        Enum(ConditionCategory),
        nullable=False,
        index=True,
        comment="LEGAL, FINANCIAL, SECURITY, REGULATORY, OPERATIONAL, PROJECT",
    )

    # Condition details
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Condition description",
    )
    detailed_requirement: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed requirement/instructions",
    )

    # Timeline
    due_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Due date for compliance",
    )
    is_time_bound: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Is this time-bound?",
    )
    days_from_disbursement: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Days from disbursement if relative",
    )

    # Frequency (for ongoing conditions)
    frequency: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Frequency for ongoing conditions - MONTHLY, QUARTERLY, ANNUAL",
    )
    next_compliance_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Next compliance date for ongoing",
    )

    # Criticality
    is_mandatory: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Is condition mandatory?",
    )
    blocks_disbursement: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Does non-compliance block disbursement?",
    )
    is_waivable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Can condition be waived?",
    )
    waiver_authority: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Authority who can waive",
    )

    # Compliance status
    compliance_status: Mapped[ConditionComplianceStatus] = mapped_column(
        Enum(ConditionComplianceStatus),
        nullable=False,
        default=ConditionComplianceStatus.PENDING,
        index=True,
        comment="PENDING, COMPLIED, WAIVED, DEFERRED, NOT_APPLICABLE",
    )
    compliance_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date of compliance",
    )
    compliance_remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Compliance remarks",
    )
    compliance_verified_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="Compliance verified by",
    )

    # Waiver details
    waiver_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Waiver date if waived",
    )
    waiver_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Reason for waiver",
    )
    waiver_approved_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="Waiver approved by",
    )

    # Deferral details
    deferral_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Deferred to date",
    )
    deferral_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Reason for deferral",
    )
    deferral_approved_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="Deferral approved by",
    )

    # Supporting documents
    required_documents: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="List of required documents for compliance",
    )
    uploaded_documents: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="List of uploaded compliance documents",
    )

    # Display
    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Display order",
    )

    # Relationships
    sanction: Mapped["LoanSanction"] = relationship(
        "LoanSanction",
        back_populates="conditions",
    )

    __table_args__ = (
        UniqueConstraint("sanction_id", "condition_number", name="uq_sanction_condition_num"),
        Index("ix_los_sanction_cond_type", "sanction_id", "condition_type"),
        Index("ix_los_sanction_cond_status", "sanction_id", "compliance_status"),
    )

    def __repr__(self) -> str:
        return f"<SanctionCondition(sanction={self.sanction_id}, num={self.condition_number}, status={self.compliance_status})>"


class LoanSecurity(BaseModel):
    """Security/Collateral for a loan sanction."""

    __tablename__ = "los_loan_security"

    # Parent sanction
    sanction_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_loan_sanction.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent sanction",
    )

    # Security identification
    security_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Security sequence number",
    )
    security_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="Security reference code",
    )

    # Classification
    security_category: Mapped[SecurityCategory] = mapped_column(
        Enum(SecurityCategory),
        nullable=False,
        index=True,
        comment="PRIMARY, COLLATERAL, GUARANTEE",
    )
    security_type: Mapped[SecurityType] = mapped_column(
        Enum(SecurityType),
        nullable=False,
        index=True,
        comment="Type of security - IMMOVABLE_PROPERTY, SHARES, etc.",
    )
    charge_type: Mapped[ChargeType] = mapped_column(
        Enum(ChargeType),
        nullable=False,
        default=ChargeType.FIRST,
        comment="FIRST, SECOND, PARI_PASSU, SUBSERVIENT",
    )

    # Security description
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Security description",
    )
    detailed_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed description",
    )

    # Property details (for immovable property)
    property_address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Property address",
    )
    property_area_sqft: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        comment="Property area in square feet",
    )
    survey_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Survey/Plot number",
    )
    property_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Land, Building, Factory, etc.",
    )

    # Ownership
    owner_name: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Owner name(s)",
    )
    owner_relationship: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Relationship with borrower",
    )
    is_third_party: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Is third party security?",
    )
    third_party_entity_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_entity.id", ondelete="SET NULL"),
        nullable=True,
        comment="Third party entity if registered",
    )

    # Valuation
    declared_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Value declared by borrower",
    )
    market_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Current market value",
    )
    forced_sale_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Forced/distress sale value",
    )
    acceptable_value: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        comment="Value acceptable for security coverage",
    )
    margin_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("25"),
        comment="Margin/haircut percentage",
    )
    net_value: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        comment="Net value after margin",
    )

    # Valuation details
    valuation_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date of valuation",
    )
    valuer_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Valuer name",
    )
    valuer_firm: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Valuation firm",
    )
    valuation_report_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Path to valuation report",
    )
    next_valuation_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Next valuation due date",
    )

    # Existing encumbrances
    has_existing_charge: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Has existing charge/encumbrance?",
    )
    existing_charge_holder: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Existing charge holder",
    )
    existing_charge_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Existing charge amount",
    )
    noc_obtained: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="NOC obtained from existing charge holder?",
    )

    # Insurance
    requires_insurance: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Requires insurance?",
    )
    insured_value: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Insured value",
    )
    insurance_policy_number: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Insurance policy number",
    )
    insurance_company: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Insurance company",
    )
    insurance_expiry: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Insurance expiry date",
    )

    # Status
    status: Mapped[SecurityStatus] = mapped_column(
        Enum(SecurityStatus),
        nullable=False,
        default=SecurityStatus.PROPOSED,
        index=True,
        comment="PROPOSED, CREATED, REGISTERED, RELEASED, SUBSTITUTED",
    )

    # Charge creation
    charge_created_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date charge was created",
    )
    charge_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="ROC charge ID",
    )

    # CERSAI registration
    cersai_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="CERSAI registration ID",
    )
    cersai_registration_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="CERSAI registration date",
    )

    # Legal vetting
    legal_vetted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Legal vetting completed?",
    )
    legal_vetting_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Legal vetting date",
    )
    legal_opinion_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Path to legal opinion/title report",
    )
    legal_remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Legal remarks/observations",
    )

    # Documents
    original_documents_received: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Original documents received?",
    )
    document_list: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="List of documents held",
    )
    document_location: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Physical location of documents",
    )

    # Guarantee-specific fields
    guarantor_entity_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_entity.id", ondelete="SET NULL"),
        nullable=True,
        comment="Guarantor entity if corporate guarantee",
    )
    guarantor_contact_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_entity_contact.id", ondelete="SET NULL"),
        nullable=True,
        comment="Guarantor contact if personal guarantee",
    )
    guarantee_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Guarantee amount (if limited)",
    )
    is_unlimited_guarantee: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Is unlimited guarantee?",
    )

    # Remarks
    remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Internal remarks",
    )

    # Relationships
    sanction: Mapped["LoanSanction"] = relationship(
        "LoanSanction",
        back_populates="securities",
    )
    third_party_entity: Mapped[Optional["Entity"]] = relationship(
        "Entity",
        foreign_keys=[third_party_entity_id],
        lazy="selectin",
    )
    guarantor_entity: Mapped[Optional["Entity"]] = relationship(
        "Entity",
        foreign_keys=[guarantor_entity_id],
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("sanction_id", "security_number", name="uq_loan_security_num"),
        Index("ix_los_loan_security_type", "sanction_id", "security_type"),
        Index("ix_los_loan_security_category", "sanction_id", "security_category"),
        Index("ix_los_loan_security_status", "sanction_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<LoanSecurity(sanction={self.sanction_id}, type={self.security_type}, value={self.acceptable_value})>"
