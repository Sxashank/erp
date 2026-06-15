"""Reimbursement Claims models for ESS Portal."""

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
from app.models.ess.enums import ClaimType, ClaimStatus

if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.hris.employee import Employee
    from app.models.ess.ess_user import ESSUser
    from app.models.finance.gl import GLAccount


class ReimbursementCategory(BaseModel):
    """Master for reimbursement categories with limits."""

    __tablename__ = "mst_reimbursement_category"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "code", name="uq_reimbursement_category_org_code"
        ),
    )

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Category Details
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    claim_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    # Limits
    max_amount_per_claim: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    max_claims_per_month: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_amount_per_month: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    max_amount_per_year: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )

    # Policy
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=True)
    approval_limit: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )  # Auto-approve if below this
    requires_bills: Mapped[bool] = mapped_column(Boolean, default=True)
    min_bill_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )

    # Accounting
    gl_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Tax
    is_taxable: Mapped[bool] = mapped_column(Boolean, default=False)
    tax_section: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    claims: Mapped[List["ReimbursementClaim"]] = relationship(
        "ReimbursementClaim", back_populates="category", lazy="selectin"
    )


class ReimbursementClaim(BaseModel):
    """Employee reimbursement claims."""

    __tablename__ = "ess_reimbursement_claim"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "claim_number", name="uq_reimbursement_claim_org_number"
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

    # Claim Details
    claim_number: Mapped[str] = mapped_column(String(30), nullable=False)
    claim_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Category
    category_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_reimbursement_category.id", ondelete="SET NULL"),
        nullable=True,
    )
    claim_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    # Expense Period
    expense_from: Mapped[date] = mapped_column(Date, nullable=False)
    expense_to: Mapped[date] = mapped_column(Date, nullable=False)

    # Amount
    claimed_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    approved_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )

    # Description
    description: Mapped[str] = mapped_column(Text, nullable=False)
    purpose: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # For Travel Claims
    travel_from: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    travel_to: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    travel_mode: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    kilometers: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)

    # Bills
    bills_attached: Mapped[int] = mapped_column(Integer, default=0)
    attachments: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Approval
    approved_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Payment
    payment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    payment_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    payment_mode: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Payroll Integration
    payroll_month: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # YYYY-MM
    included_in_payslip: Mapped[bool] = mapped_column(Boolean, default=False)

    # Status
    status: Mapped[str] = mapped_column(
        String(30),
        default=ClaimStatus.DRAFT.value,
        nullable=False,
    )

    # Workflow
    workflow_instance_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )

    # Relationships
    ess_user: Mapped["ESSUser"] = relationship(
        "ESSUser", back_populates="reimbursement_claims", lazy="selectin"
    )
    employee: Mapped["Employee"] = relationship(
        "Employee", lazy="selectin"
    )
    category: Mapped[Optional["ReimbursementCategory"]] = relationship(
        "ReimbursementCategory", back_populates="claims", lazy="selectin"
    )
    line_items: Mapped[List["ReimbursementLineItem"]] = relationship(
        "ReimbursementLineItem", back_populates="claim", lazy="selectin", cascade="all, delete-orphan"
    )
    approval_history: Mapped[List["ReimbursementApproval"]] = relationship(
        "ReimbursementApproval", back_populates="claim", lazy="selectin", cascade="all, delete-orphan"
    )


class ReimbursementLineItem(BaseModel):
    """Individual expense items in a reimbursement claim."""

    __tablename__ = "ess_reimbursement_line_item"

    # Claim Reference
    claim_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ess_reimbursement_claim.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Line Item Details
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)
    expense_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)

    # Amount
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    approved_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )

    # Bill Details
    bill_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bill_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    vendor_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    vendor_gstin: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)

    # GST (if applicable)
    gst_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    gst_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)

    # Attachment
    attachment_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    attachment_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Verification
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_remarks: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    claim: Mapped["ReimbursementClaim"] = relationship(
        "ReimbursementClaim", back_populates="line_items", lazy="selectin"
    )


class ReimbursementApproval(BaseModel):
    """Approval history for reimbursement claims."""

    __tablename__ = "ess_reimbursement_approval"

    # Claim Reference
    claim_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("ess_reimbursement_claim.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Approval Details
    approval_level: Mapped[int] = mapped_column(Integer, nullable=False)
    approver_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Action
    action: Mapped[str] = mapped_column(String(20), nullable=False)  # APPROVED, REJECTED, FORWARD
    action_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Amount
    approved_amount: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )

    # Forwarded To (if forwarded)
    forwarded_to: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    claim: Mapped["ReimbursementClaim"] = relationship(
        "ReimbursementClaim", back_populates="approval_history", lazy="selectin"
    )
