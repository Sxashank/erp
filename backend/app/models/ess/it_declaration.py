"""IT Declaration models for ESS Portal (Indian Income Tax)."""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Enum as SQLEnum,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.ess.enums import (
    ITDeclarationStatus,
    ITDeclarationSection,
)

if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.hris.employee import Employee
    from app.models.ess.ess_user import ESSUser


class ITDeclarationMaster(BaseModel):
    """Master for IT Declaration sections with limits."""

    __tablename__ = "mst_it_declaration_section"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "section_code", name="uq_it_declaration_section_org_code"
        ),
    )

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Section Details
    section_code: Mapped[str] = mapped_column(String(20), nullable=False)
    section_name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Category
    category: Mapped[str] = mapped_column(String(50), nullable=False)  # DEDUCTION, EXEMPTION, REBATE

    # Limits
    max_limit: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    is_combined_limit: Mapped[bool] = mapped_column(Boolean, default=False)
    combined_with_sections: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)

    # Applicable Financial Year
    applicable_from_fy: Mapped[str] = mapped_column(String(10), nullable=False)  # 2024-25
    applicable_to_fy: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Proof Requirements
    requires_proof: Mapped[bool] = mapped_column(Boolean, default=True)
    proof_types: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)  # ["RECEIPT", "CERTIFICATE", etc.]
    proof_mandatory_for_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )

    # Display
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    help_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Regime
    applicable_in_old_regime: Mapped[bool] = mapped_column(Boolean, default=True)
    applicable_in_new_regime: Mapped[bool] = mapped_column(Boolean, default=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    declarations: Mapped[List["ITDeclarationItem"]] = relationship(
        "ITDeclarationItem", back_populates="section_master", lazy="selectin"
    )


class ITDeclaration(BaseModel):
    """Employee IT Declaration for a financial year."""

    __tablename__ = "ess_it_declaration"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "employee_id", "financial_year",
            name="uq_it_declaration_org_emp_fy"
        ),
    )

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ESS User
    ess_user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ess_user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Employee
    employee_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_employee.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Financial Year
    financial_year: Mapped[str] = mapped_column(String(10), nullable=False)  # 2024-25

    # Tax Regime
    tax_regime: Mapped[str] = mapped_column(String(10), nullable=False)  # OLD, NEW

    # Declaration Period
    declaration_start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    declaration_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    proof_submission_deadline: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Total Declared
    total_declared_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=0
    )
    total_verified_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=0
    )
    total_approved_amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=0
    )

    # HRA Details
    hra_declared: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    rent_paid_monthly: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    landlord_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    landlord_pan: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    landlord_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metro_city: Mapped[bool] = mapped_column(Boolean, default=False)

    # Home Loan Details (Section 24b)
    home_loan_interest: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    home_loan_principal: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    loan_sanctioned_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    lender_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    lender_pan: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    property_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # SELF_OCCUPIED, LET_OUT

    # Tax Computation (Computed fields - updated by payroll)
    estimated_taxable_income: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(14, 2), nullable=True
    )
    estimated_tax_liability: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    monthly_tds: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )

    # Submission
    submitted_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    proof_submitted_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Verification
    verified_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("auth_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    verified_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    verification_remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        SQLEnum(ITDeclarationStatus, name="it_declaration_status_enum", create_type=False),
        default=ITDeclarationStatus.DRAFT,
        nullable=False,
    )

    # Version (for re-declarations)
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_latest: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    ess_user: Mapped["ESSUser"] = relationship(
        "ESSUser", back_populates="it_declarations", lazy="selectin"
    )
    employee: Mapped["Employee"] = relationship(
        "Employee", lazy="selectin"
    )
    items: Mapped[List["ITDeclarationItem"]] = relationship(
        "ITDeclarationItem", back_populates="declaration", lazy="selectin", cascade="all, delete-orphan"
    )
    hra_receipts: Mapped[List["HRAReceipt"]] = relationship(
        "HRAReceipt", back_populates="declaration", lazy="selectin", cascade="all, delete-orphan"
    )


class ITDeclarationItem(BaseModel):
    """Individual declaration items under each section."""

    __tablename__ = "ess_it_declaration_item"

    # Declaration Reference
    declaration_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ess_it_declaration.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Section
    section_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_it_declaration_section.id", ondelete="SET NULL"),
        nullable=True,
    )
    section_code: Mapped[str] = mapped_column(String(20), nullable=False)

    # Item Details
    particular: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Amount
    declared_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    verified_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    approved_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )

    # Investment Details
    investment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    policy_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    institution_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Proof
    proof_submitted: Mapped[bool] = mapped_column(Boolean, default=False)
    proof_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    proof_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Verification
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_remarks: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    declaration: Mapped["ITDeclaration"] = relationship(
        "ITDeclaration", back_populates="items", lazy="selectin"
    )
    section_master: Mapped[Optional["ITDeclarationMaster"]] = relationship(
        "ITDeclarationMaster", back_populates="declarations", lazy="selectin"
    )


class HRAReceipt(BaseModel):
    """Monthly HRA receipts for rent declaration."""

    __tablename__ = "ess_hra_receipt"

    # Declaration Reference
    declaration_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ess_it_declaration.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Month
    month: Mapped[str] = mapped_column(String(7), nullable=False)  # YYYY-MM
    receipt_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Amount
    rent_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Receipt Upload
    receipt_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    receipt_uploaded: Mapped[bool] = mapped_column(Boolean, default=False)

    # Verification
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    declaration: Mapped["ITDeclaration"] = relationship(
        "ITDeclaration", back_populates="hra_receipts", lazy="selectin"
    )


class AttendanceRegularization(BaseModel):
    """Attendance regularization requests from ESS Portal."""

    __tablename__ = "ess_attendance_regularization"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "request_number", name="uq_attendance_reg_org_number"
        ),
    )

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Employee
    employee_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_employee.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Request Details
    request_number: Mapped[str] = mapped_column(String(30), nullable=False)
    attendance_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Regularization Type
    regularization_type: Mapped[str] = mapped_column(String(30), nullable=False)

    # Time Details
    requested_in_time: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # HH:MM
    requested_out_time: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    actual_in_time: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    actual_out_time: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Reason
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_document: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Approval
    approved_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("auth_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    approver_remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)

    # Relationships
    employee: Mapped["Employee"] = relationship(
        "Employee", lazy="selectin"
    )
