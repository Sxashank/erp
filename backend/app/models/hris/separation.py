"""
Separation and Full & Final Settlement Models.

Handles employee exit process including:
- Resignation, termination, retirement tracking
- Clearance workflow
- Full & Final (FnF) settlement calculation
- Gratuity calculation
"""

import enum
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    String,
    Text,
    Boolean,
    Integer,
    Date,
    DateTime,
    Numeric,
    ForeignKey,
    Enum as SQLEnum,
    UniqueConstraint,
    Index,
    func,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, AuditMixin, VersionedMixin

if TYPE_CHECKING:
    from app.models.hris.employee import Employee
    from app.models.auth.user import User
    from app.models.masters.organization import Organization
    from app.models.masters.department import Department


class SeparationType(str, enum.Enum):
    """Types of employee separation."""
    RESIGNATION = "RESIGNATION"
    TERMINATION = "TERMINATION"
    RETIREMENT = "RETIREMENT"
    ABSCONDING = "ABSCONDING"
    DEATH = "DEATH"
    VRS = "VRS"  # Voluntary Retirement Scheme
    CONTRACT_END = "CONTRACT_END"


class SeparationStatus(str, enum.Enum):
    """Status of separation process."""
    INITIATED = "INITIATED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    NOTICE_PERIOD = "NOTICE_PERIOD"
    CLEARANCE = "CLEARANCE"
    FNF_PENDING = "FNF_PENDING"
    FNF_CALCULATED = "FNF_CALCULATED"
    FNF_APPROVED = "FNF_APPROVED"
    FNF_PAID = "FNF_PAID"
    COMPLETED = "COMPLETED"
    WITHDRAWN = "WITHDRAWN"
    REJECTED = "REJECTED"


class ResignationReason(str, enum.Enum):
    """Categories of resignation reasons."""
    BETTER_OPPORTUNITY = "BETTER_OPPORTUNITY"
    PERSONAL = "PERSONAL"
    HEALTH = "HEALTH"
    RELOCATION = "RELOCATION"
    HIGHER_STUDIES = "HIGHER_STUDIES"
    FAMILY_REASONS = "FAMILY_REASONS"
    CAREER_CHANGE = "CAREER_CHANGE"
    COMPENSATION = "COMPENSATION"
    WORK_ENVIRONMENT = "WORK_ENVIRONMENT"
    OTHER = "OTHER"


class ClearanceStatus(str, enum.Enum):
    """Status of clearance item."""
    PENDING = "PENDING"
    CLEARED = "CLEARED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    RECOVERY_PENDING = "RECOVERY_PENDING"


class FnFStatus(str, enum.Enum):
    """Status of FnF settlement."""
    DRAFT = "DRAFT"
    CALCULATED = "CALCULATED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class Separation(Base, AuditMixin, VersionedMixin):
    """
    Employee separation/exit tracking.

    Tracks the entire exit process from resignation to completion.
    """
    __tablename__ = "hris_separation"
    __table_args__ = (
        Index("ix_hris_separation_org_status", "organization_id", "status"),
        Index("ix_hris_separation_employee", "employee_id"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organization_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("mst_organization.id"), nullable=False)
    employee_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("hris_employee.id"), nullable=False)

    # Separation Details
    separation_type: Mapped[str] = mapped_column(SQLEnum(SeparationType, native_enum=False), nullable=False)
    status: Mapped[str] = mapped_column(SQLEnum(SeparationStatus, native_enum=False), default=SeparationStatus.INITIATED)

    # Dates
    initiation_date: Mapped[date] = mapped_column(Date, nullable=False)
    requested_last_working_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    approved_last_working_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    actual_last_working_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Notice Period
    notice_period_days: Mapped[int] = mapped_column(Integer, default=30)
    notice_period_served: Mapped[int] = mapped_column(Integer, default=0)
    notice_period_shortfall: Mapped[int] = mapped_column(Integer, default=0)
    is_notice_buyout: Mapped[bool] = mapped_column(Boolean, default=False)
    shortfall_recovery_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)

    # Reason
    reason_category: Mapped[Optional[str]] = mapped_column(SQLEnum(ResignationReason, native_enum=False), nullable=True)
    reason_detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Exit Interview
    exit_interview_done: Mapped[bool] = mapped_column(Boolean, default=False)
    exit_interview_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    exit_interview_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    exit_interview_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("mst_user.id"), nullable=True)

    # Approval
    approved_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("mst_user.id"), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Documentation
    resignation_letter_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    relieving_letter_issued: Mapped[bool] = mapped_column(Boolean, default=False)
    relieving_letter_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    relieving_letter_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    experience_letter_issued: Mapped[bool] = mapped_column(Boolean, default=False)
    experience_letter_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Workflow
    workflow_instance_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    # Additional metadata
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    employee: Mapped["Employee"] = relationship("Employee", back_populates="separations", foreign_keys=[employee_id])
    organization: Mapped["Organization"] = relationship("Organization", foreign_keys=[organization_id])
    clearances: Mapped[List["SeparationClearance"]] = relationship("SeparationClearance", back_populates="separation", cascade="all, delete-orphan")
    fnf_settlement: Mapped[Optional["FnFSettlement"]] = relationship("FnFSettlement", back_populates="separation", uselist=False)

    @property
    def days_in_notice_period(self) -> int:
        """Calculate days already served in notice period."""
        if not self.approved_last_working_date or not self.initiation_date:
            return 0
        from datetime import date as date_cls
        today = date_cls.today()
        served = (min(today, self.approved_last_working_date) - self.initiation_date).days
        return max(0, served)

    @property
    def notice_shortfall_days(self) -> int:
        """Calculate notice period shortfall."""
        return max(0, self.notice_period_days - self.notice_period_served)


class ClearanceChecklist(Base, AuditMixin, VersionedMixin):
    """
    Master list of clearance items for employee exit.

    Configured per organization with responsible department.
    """
    __tablename__ = "hris_clearance_checklist"
    __table_args__ = (
        UniqueConstraint("organization_id", "checklist_code", name="uq_clearance_checklist_code"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    organization_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("mst_organization.id"), nullable=False)

    checklist_code: Mapped[str] = mapped_column(String(20), nullable=False)
    checklist_item: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Responsible department
    department_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("mst_department.id"), nullable=True)
    responsible_role: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Configuration
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)
    can_have_recovery: Mapped[bool] = mapped_column(Boolean, default=False)
    default_recovery_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", foreign_keys=[organization_id])
    department: Mapped[Optional["Department"]] = relationship("Department", foreign_keys=[department_id])


class SeparationClearance(Base, AuditMixin, VersionedMixin):
    """
    Individual clearance item status for a separation.

    Tracks clearance from each department.
    """
    __tablename__ = "hris_separation_clearance"
    __table_args__ = (
        UniqueConstraint("separation_id", "checklist_id", name="uq_separation_clearance_item"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    separation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("hris_separation.id"), nullable=False)
    checklist_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("hris_clearance_checklist.id"), nullable=False)

    status: Mapped[str] = mapped_column(SQLEnum(ClearanceStatus, native_enum=False), default=ClearanceStatus.PENDING)

    # Recovery details
    has_recovery: Mapped[bool] = mapped_column(Boolean, default=False)
    recovery_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    recovery_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Clearance details
    cleared_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("mst_user.id"), nullable=True)
    cleared_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    separation: Mapped["Separation"] = relationship("Separation", back_populates="clearances", foreign_keys=[separation_id])
    checklist: Mapped["ClearanceChecklist"] = relationship("ClearanceChecklist", foreign_keys=[checklist_id])


class FnFSettlement(Base, AuditMixin, VersionedMixin):
    """
    Full & Final Settlement for separated employees.

    Calculates all dues and recoveries for final settlement.
    """
    __tablename__ = "hris_fnf_settlement"
    __table_args__ = (
        Index("ix_hris_fnf_settlement_employee", "employee_id"),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    separation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("hris_separation.id"), nullable=False, unique=True)
    employee_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("hris_employee.id"), nullable=False)

    settlement_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    last_working_date: Mapped[date] = mapped_column(Date, nullable=False)

    status: Mapped[str] = mapped_column(SQLEnum(FnFStatus, native_enum=False), default=FnFStatus.DRAFT)

    # Earnings
    pending_salary: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    leave_encashment: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    leave_encashment_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    gratuity_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    gratuity_years: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"))
    bonus_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    pending_reimbursements: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    other_earnings: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    other_earnings_detail: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    total_earnings: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))

    # Deductions
    notice_recovery: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    notice_shortfall_days: Mapped[int] = mapped_column(Integer, default=0)
    advance_recovery: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    loan_recovery: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    asset_recovery: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    clearance_recovery: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    other_deductions: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    other_deductions_detail: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    tds_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    total_deductions: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))

    # Net Payable
    net_payable: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))

    # Calculation Details (for audit)
    calculation_details: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Gratuity Calculation Details
    gratuity_basic_salary: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    gratuity_eligible: Mapped[bool] = mapped_column(Boolean, default=False)
    gratuity_calculation_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # "15/26" or custom

    # Approval
    calculated_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("mst_user.id"), nullable=True)
    calculated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    approved_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("mst_user.id"), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Payment
    payment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    payment_mode: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # BANK_TRANSFER, CHEQUE, CASH
    payment_reference: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    bank_account_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    bank_ifsc: Mapped[Optional[str]] = mapped_column(String(11), nullable=True)

    # GL Posting
    voucher_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), ForeignKey("txn_voucher.id"), nullable=True)
    gl_posted: Mapped[bool] = mapped_column(Boolean, default=False)

    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    separation: Mapped["Separation"] = relationship("Separation", back_populates="fnf_settlement", foreign_keys=[separation_id])
    employee: Mapped["Employee"] = relationship("Employee", foreign_keys=[employee_id])

    def calculate_totals(self) -> None:
        """Calculate total earnings, deductions, and net payable."""
        self.total_earnings = (
            self.pending_salary +
            self.leave_encashment +
            self.gratuity_amount +
            self.bonus_amount +
            self.pending_reimbursements +
            self.other_earnings
        )
        self.total_deductions = (
            self.notice_recovery +
            self.advance_recovery +
            self.loan_recovery +
            self.asset_recovery +
            self.clearance_recovery +
            self.other_deductions +
            self.tds_amount
        )
        self.net_payable = self.total_earnings - self.total_deductions


