"""Loan application models for the lending module."""

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
    ApplicationStage, ApplicationStatus, AppraisalType,
    TechnicalFeasibility, AppraisalRecommendation, MilestoneStatus,
    InterestType, RepaymentFrequency, RepaymentMode
)


if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.lending.entity import Entity
    from app.models.lending.product import LoanProduct
    from app.models.lending.sanction import LoanSanction
    from app.models.workflow import WorkflowInstance


class LoanApplication(BaseModel):
    """Loan application master."""

    __tablename__ = "los_loan_application"

    # Organization scope
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Organization",
    )

    # Application identification
    application_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Application number e.g., 'SMFC/TL/DEL/2025/A00001'",
    )
    lead_reference: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Lead/enquiry reference if applicable",
    )

    # Entity reference
    entity_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_entity.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Borrower entity",
    )

    # Product reference
    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_loan_product.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Loan product",
    )

    # Loan request details
    requested_amount: Mapped[Decimal] = mapped_column(
        Numeric(20, 2),
        nullable=False,
        comment="Requested loan amount",
    )
    requested_tenure_months: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Requested tenure in months",
    )
    purpose: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Purpose of loan",
    )
    detailed_purpose: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed description of purpose/end use",
    )

    # Project details (for project finance)
    is_project_finance: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Is this project finance?",
    )
    project_name: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Project name",
    )
    project_cost: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Total project cost",
    )
    promoter_contribution: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Promoter contribution",
    )
    promoter_contribution_pct: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Promoter contribution %",
    )
    bank_finance: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Bank/NBFC finance amount",
    )
    other_finance: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Other finance (subsidy, grants, etc.)",
    )
    project_location: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Project location",
    )
    project_start_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Expected project start date",
    )
    project_completion_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Expected project completion date",
    )

    # Interest preference
    preferred_interest_type: Mapped[InterestType] = mapped_column(
        Enum(InterestType),
        nullable=False,
        default=InterestType.FLOATING,
        comment="Preferred interest type",
    )
    preferred_repayment_frequency: Mapped[RepaymentFrequency] = mapped_column(
        Enum(RepaymentFrequency),
        nullable=False,
        default=RepaymentFrequency.MONTHLY,
        comment="Preferred repayment frequency",
    )
    preferred_repayment_mode: Mapped[RepaymentMode] = mapped_column(
        Enum(RepaymentMode),
        nullable=False,
        default=RepaymentMode.EMI,
        comment="Preferred repayment mode",
    )
    requested_moratorium_months: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Requested moratorium period",
    )

    # Application stage and status
    stage: Mapped[ApplicationStage] = mapped_column(
        Enum(ApplicationStage),
        nullable=False,
        default=ApplicationStage.APPLICATION,
        index=True,
        comment="Application stage - APPLICATION, APPRAISAL, SANCTION, etc.",
    )
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus),
        nullable=False,
        default=ApplicationStatus.DRAFT,
        index=True,
        comment="Application status - DRAFT, SUBMITTED, UNDER_REVIEW, etc.",
    )
    sub_status: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Sub-status for detailed tracking",
    )

    # Dates
    application_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Application date",
    )
    submission_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date submitted for processing",
    )
    expected_decision_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Expected decision date",
    )
    decision_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Actual decision date",
    )
    expiry_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Application expiry date",
    )

    # Assignment
    relationship_manager_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="Relationship manager",
    )
    credit_officer_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="Credit officer handling application",
    )
    branch_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Processing branch",
    )

    # Workflow
    workflow_instance_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("wf_workflow_instance.id", ondelete="SET NULL"),
        nullable=True,
        comment="Approval workflow instance",
    )

    # Scoring/Rating at application time
    entity_rating_at_application: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="Entity rating at time of application",
    )
    cibil_score_at_application: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="CIBIL score at time of application",
    )

    # Decision details
    rejection_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Reason for rejection if rejected",
    )
    rejection_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Rejection code",
    )
    withdrawal_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Reason for withdrawal if withdrawn",
    )

    # Source tracking
    source_channel: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="DIRECT",
        comment="Application source - DIRECT, DSA, ONLINE, REFERRAL",
    )
    source_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="DSA code or referral reference",
    )

    # Additional info
    remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Internal remarks",
    )
    extra_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Additional metadata",
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )
    entity: Mapped["Entity"] = relationship(
        "Entity",
        back_populates="applications",
        lazy="selectin",
    )
    product: Mapped["LoanProduct"] = relationship(
        "LoanProduct",
        lazy="selectin",
    )
    workflow_instance: Mapped[Optional["WorkflowInstance"]] = relationship(
        "WorkflowInstance",
        lazy="selectin",
    )
    documents: Mapped[List["ApplicationDocument"]] = relationship(
        "ApplicationDocument",
        back_populates="application",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    fees: Mapped[List["ApplicationFee"]] = relationship(
        "ApplicationFee",
        back_populates="application",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    technical_appraisals: Mapped[List["TechnicalAppraisal"]] = relationship(
        "TechnicalAppraisal",
        back_populates="application",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    financial_analyses: Mapped[List["FinancialAnalysis"]] = relationship(
        "FinancialAnalysis",
        back_populates="application",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    milestones: Mapped[List["ProjectMilestone"]] = relationship(
        "ProjectMilestone",
        back_populates="application",
        cascade="all, delete-orphan",
        lazy="noload",
    )
    sanctions: Mapped[List["LoanSanction"]] = relationship(
        "LoanSanction",
        back_populates="application",
        lazy="noload",
    )

    __table_args__ = (
        UniqueConstraint("organization_id", "application_number", name="uq_loan_app_org_number"),
        Index("ix_los_loan_app_org_stage", "organization_id", "stage"),
        Index("ix_los_loan_app_org_status", "organization_id", "status"),
        Index("ix_los_loan_app_entity", "entity_id"),
        Index("ix_los_loan_app_product", "product_id"),
        Index("ix_los_loan_app_date", "application_date"),
    )

    def __repr__(self) -> str:
        return f"<LoanApplication(number={self.application_number}, stage={self.stage}, status={self.status})>"


class ApplicationDocument(BaseModel):
    """Documents uploaded for a loan application."""

    __tablename__ = "los_application_document"

    # Parent application
    application_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_loan_application.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent application",
    )

    # Document checklist reference
    checklist_item_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_document_checklist.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Checklist item reference",
    )

    # Document identification
    document_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Document code from checklist",
    )
    document_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Document name",
    )
    document_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Document description",
    )

    # File details
    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Original file name",
    )
    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Storage path/key",
    )
    file_size_bytes: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="File size in bytes",
    )
    file_mime_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="MIME type",
    )
    file_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        comment="SHA-256 hash",
    )

    # Document dates
    document_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date on document",
    )
    expiry_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Document expiry date",
    )
    upload_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Upload timestamp",
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="PENDING",
        index=True,
        comment="PENDING, VERIFIED, REJECTED, WAIVED",
    )
    is_mandatory: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Is document mandatory?",
    )
    is_waived: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Document requirement waived?",
    )
    waiver_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Reason for waiver",
    )
    waiver_approved_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="Waiver approved by",
    )

    # Verification
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Verification timestamp",
    )
    verified_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="Verified by user",
    )
    verification_remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Verification remarks",
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Rejection reason if rejected",
    )

    # Version tracking
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        comment="Document version (for re-uploads)",
    )
    previous_version_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="Previous version if re-uploaded",
    )

    # Relationships
    application: Mapped["LoanApplication"] = relationship(
        "LoanApplication",
        back_populates="documents",
    )

    __table_args__ = (
        Index("ix_los_app_doc_app_code", "application_id", "document_code"),
        Index("ix_los_app_doc_status", "application_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<ApplicationDocument(app={self.application_id}, code={self.document_code}, status={self.status})>"


class ApplicationFee(BaseModel):
    """Fee collection tracking for an application."""

    __tablename__ = "los_application_fee"

    # Parent application
    application_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_loan_application.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent application",
    )

    # Fee reference
    fee_master_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_fee_master.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Fee master reference",
    )

    # Fee details
    fee_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Fee code",
    )
    fee_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Fee name",
    )

    # Amounts
    calculated_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment="System calculated amount",
    )
    approved_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment="Approved amount after any waiver",
    )
    waiver_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Waived amount",
    )
    waiver_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0"),
        comment="Waiver percentage",
    )

    # Tax
    cgst_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
        comment="CGST amount",
    )
    sgst_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
        comment="SGST amount",
    )
    igst_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
        comment="IGST amount",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        comment="Total amount including tax",
    )

    # Collection status
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="PENDING",
        index=True,
        comment="PENDING, COLLECTED, WAIVED, DEDUCTED, REFUNDED",
    )
    collection_mode: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Collection mode - CASH, CHEQUE, NEFT, DEDUCTION",
    )
    collection_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Collection date",
    )
    collection_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Payment reference",
    )

    # Waiver approval
    waiver_approved_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="Waiver approved by",
    )
    waiver_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Waiver reason",
    )

    # Deduction from disbursement
    deducted_from_disbursement: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Was deducted from disbursement?",
    )
    disbursement_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=True,
        comment="Disbursement from which deducted",
    )

    # Invoice
    invoice_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Invoice number",
    )
    invoice_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Invoice date",
    )

    # Relationships
    application: Mapped["LoanApplication"] = relationship(
        "LoanApplication",
        back_populates="fees",
    )

    __table_args__ = (
        UniqueConstraint("application_id", "fee_master_id", name="uq_app_fee"),
        Index("ix_los_app_fee_status", "application_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<ApplicationFee(app={self.application_id}, fee={self.fee_code}, amount={self.total_amount})>"


class TechnicalAppraisal(BaseModel):
    """Technical/Site appraisal for an application."""

    __tablename__ = "los_technical_appraisal"

    # Parent application
    application_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_loan_application.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent application",
    )

    # Appraisal identification
    appraisal_reference: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Appraisal reference number",
    )
    appraisal_type: Mapped[AppraisalType] = mapped_column(
        Enum(AppraisalType),
        nullable=False,
        default=AppraisalType.TECHNICAL,
        comment="Type of appraisal - TECHNICAL, LEGAL, MARKET",
    )

    # Appraisal details
    appraisal_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Date of appraisal",
    )
    site_visit_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date of site visit",
    )
    appraiser_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Appraiser",
    )
    external_appraiser: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="External appraiser name if applicable",
    )
    external_appraiser_firm: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="External appraiser firm",
    )

    # Project/Asset details
    project_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Project description",
    )
    location_details: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Location/site details",
    )
    land_area_sqft: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        comment="Land area in square feet",
    )
    built_up_area_sqft: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(15, 2),
        nullable=True,
        comment="Built-up area in square feet",
    )

    # Cost estimates
    estimated_project_cost: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Estimated project cost",
    )
    land_cost: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Land cost",
    )
    construction_cost: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Construction cost",
    )
    machinery_cost: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Plant & machinery cost",
    )
    other_costs: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Other costs",
    )
    contingency: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Contingency provision",
    )

    # Feasibility assessment
    feasibility: Mapped[TechnicalFeasibility] = mapped_column(
        Enum(TechnicalFeasibility),
        nullable=False,
        default=TechnicalFeasibility.FEASIBLE,
        comment="Technical feasibility - FEASIBLE, CONDITIONAL, NOT_FEASIBLE",
    )
    feasibility_remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Feasibility assessment remarks",
    )

    # Timeline assessment
    estimated_completion_months: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Estimated completion in months",
    )
    construction_stage: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Current construction stage if ongoing",
    )
    completion_percentage: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Current completion percentage",
    )

    # Statutory compliance
    statutory_approvals: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="List of statutory approvals and status",
    )
    environmental_clearance: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Environmental clearance status",
    )

    # Recommendation
    recommendation: Mapped[AppraisalRecommendation] = mapped_column(
        Enum(AppraisalRecommendation),
        nullable=False,
        default=AppraisalRecommendation.PROCEED,
        comment="Recommendation - PROCEED, PROCEED_WITH_CONDITIONS, REJECT, HOLD",
    )
    conditions: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Conditions for proceeding",
    )
    concerns: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Concerns/risks identified",
    )

    # Report
    report_summary: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Appraisal report summary",
    )
    report_file_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Path to detailed report file",
    )
    photos: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="List of site photos paths",
    )

    # Relationships
    application: Mapped["LoanApplication"] = relationship(
        "LoanApplication",
        back_populates="technical_appraisals",
    )

    __table_args__ = (
        UniqueConstraint("application_id", "appraisal_reference", name="uq_tech_appraisal_ref"),
        Index("ix_los_tech_appraisal_app_type", "application_id", "appraisal_type"),
    )

    def __repr__(self) -> str:
        return f"<TechnicalAppraisal(ref={self.appraisal_reference}, feasibility={self.feasibility})>"


class FinancialAnalysis(BaseModel):
    """Financial analysis for an application."""

    __tablename__ = "los_financial_analysis"

    # Parent application
    application_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_loan_application.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent application",
    )

    # Analysis identification
    analysis_reference: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Analysis reference number",
    )
    analysis_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Date of analysis",
    )
    analyst_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Analyst",
    )

    # Financial years analyzed
    financial_years_analyzed: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        comment="List of FY analyzed e.g., ['2022-23', '2023-24', '2024-25']",
    )
    base_year: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="Base year for analysis",
    )

    # Historical ratios (from EntityFinancial)
    historical_ratios: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="Year-wise historical ratios",
    )

    # Projected financials
    projection_years: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5,
        comment="Number of projection years",
    )
    projected_revenue: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="Year-wise projected revenue",
    )
    projected_ebitda: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="Year-wise projected EBITDA",
    )
    projected_net_profit: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="Year-wise projected net profit",
    )
    projected_cash_flows: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        comment="Year-wise projected cash flows",
    )

    # Key ratios - Current
    current_ratio: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Current ratio",
    )
    debt_equity_ratio: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Debt to equity ratio",
    )
    interest_coverage_ratio: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Interest coverage ratio",
    )

    # DSCR analysis
    average_dscr: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Average DSCR over projection period",
    )
    minimum_dscr: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="Minimum DSCR in any year",
    )
    dscr_by_year: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Year-wise DSCR",
    )

    # Break-even analysis
    break_even_capacity_pct: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Break-even capacity utilization %",
    )
    break_even_sales: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Break-even sales amount",
    )

    # Sensitivity analysis
    sensitivity_analysis: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Sensitivity analysis results",
    )

    # Recommendation
    recommendation: Mapped[AppraisalRecommendation] = mapped_column(
        Enum(AppraisalRecommendation),
        nullable=False,
        default=AppraisalRecommendation.PROCEED,
        comment="Financial recommendation",
    )
    recommended_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Recommended loan amount",
    )
    recommended_tenure: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Recommended tenure in months",
    )
    recommended_moratorium: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Recommended moratorium in months",
    )

    # Comments
    strengths: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Financial strengths",
    )
    weaknesses: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Financial weaknesses",
    )
    comments: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Overall comments",
    )
    conditions: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Conditions for approval",
    )

    # Report
    report_file_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Path to detailed report file",
    )

    # Relationships
    application: Mapped["LoanApplication"] = relationship(
        "LoanApplication",
        back_populates="financial_analyses",
    )

    __table_args__ = (
        UniqueConstraint("application_id", "analysis_reference", name="uq_fin_analysis_ref"),
        Index("ix_los_fin_analysis_app", "application_id"),
    )

    def __repr__(self) -> str:
        return f"<FinancialAnalysis(ref={self.analysis_reference}, dscr={self.average_dscr})>"


class ProjectMilestone(BaseModel):
    """Project milestones for milestone-linked disbursement."""

    __tablename__ = "los_project_milestone"

    # Parent application
    application_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("los_loan_application.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent application",
    )

    # Milestone identification
    milestone_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Milestone sequence number",
    )
    milestone_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Milestone name",
    )
    milestone_description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Milestone description",
    )

    # Timeline
    expected_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Expected completion date",
    )
    actual_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Actual completion date",
    )
    delay_days: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="Delay in days if any",
    )

    # Linked disbursement
    disbursement_percentage: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="% of loan to disburse at this milestone",
    )
    disbursement_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Disbursement amount at this milestone",
    )
    cumulative_disbursement_pct: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Cumulative disbursement % up to this milestone",
    )

    # Equity contribution requirement
    equity_contribution_required: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(20, 2),
        nullable=True,
        comment="Equity contribution required before this milestone",
    )
    equity_contribution_verified: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Equity contribution verified?",
    )

    # Status
    status: Mapped[MilestoneStatus] = mapped_column(
        Enum(MilestoneStatus),
        nullable=False,
        default=MilestoneStatus.PENDING,
        index=True,
        comment="Status - PENDING, IN_PROGRESS, COMPLETED, DELAYED, WAIVED",
    )

    # Verification
    verification_criteria: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Criteria for milestone verification",
    )
    verification_documents: Mapped[Optional[list]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Required verification documents",
    )
    verified_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
        comment="Verified by",
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Verification timestamp",
    )
    verification_remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Verification remarks",
    )

    # Remarks
    remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="General remarks",
    )

    # Relationships
    application: Mapped["LoanApplication"] = relationship(
        "LoanApplication",
        back_populates="milestones",
    )

    __table_args__ = (
        UniqueConstraint("application_id", "milestone_number", name="uq_milestone_app_num"),
        Index("ix_los_milestone_app_status", "application_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<ProjectMilestone(app={self.application_id}, num={self.milestone_number}, status={self.status})>"
