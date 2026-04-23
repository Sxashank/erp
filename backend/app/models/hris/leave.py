"""Leave management models for HRIS module."""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
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
from app.core.constants import (
    LeaveCategory,
    LeaveApplicationStatus,
    Gender,
)

if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.hris.employee import Employee


class LeaveType(BaseModel):
    """Leave type master model."""

    __tablename__ = "hris_leave_type"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "leave_code", name="uq_leave_type_org_code"
        ),
    )

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Leave Details
    leave_code: Mapped[str] = mapped_column(String(20), nullable=False)
    leave_name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(
        SQLEnum(LeaveCategory, name="leave_category_enum", create_type=False),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Annual Quota
    annual_quota: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    max_accumulation: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)  # Max balance allowed

    # Accrual Settings
    accrual_type: Mapped[str] = mapped_column(String(20), default="YEARLY")  # YEARLY, MONTHLY, PRORATE
    accrual_on_joining: Mapped[bool] = mapped_column(Boolean, default=True)  # Accrue from joining
    prorate_on_joining: Mapped[bool] = mapped_column(Boolean, default=True)  # Prorate for partial year

    # Carry Forward
    carry_forward_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    max_carry_forward: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    carry_forward_expiry_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # e.g., 3 months

    # Encashment
    encashment_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    max_encashment_days: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    encashment_on_separation: Mapped[bool] = mapped_column(Boolean, default=False)

    # Application Rules
    min_days_per_application: Mapped[Decimal] = mapped_column(Numeric(3, 1), default=0.5)  # Half day allowed
    max_days_per_application: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    max_consecutive_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Advance Notice
    min_advance_days: Mapped[int] = mapped_column(Integer, default=0)  # Days in advance required
    max_advance_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Club with Other Leaves
    can_club_with_holidays: Mapped[bool] = mapped_column(Boolean, default=True)
    can_club_with_weekoff: Mapped[bool] = mapped_column(Boolean, default=True)
    excluded_holidays_counted: Mapped[bool] = mapped_column(Boolean, default=False)  # Holidays in between counted

    # Negative Balance
    negative_balance_allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    max_negative_balance: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)

    # Document Required
    document_required: Mapped[bool] = mapped_column(Boolean, default=False)
    document_required_after_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # e.g., > 2 days

    # Gender Specific
    gender_specific: Mapped[Optional[str]] = mapped_column(
        SQLEnum(Gender, name="gender_enum", create_type=False),
        nullable=True,
    )

    # Employment Type Specific (JSONB array)
    applicable_employment_types: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    # Probation
    applicable_in_probation: Mapped[bool] = mapped_column(Boolean, default=True)
    probation_quota: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)

    # Notice Period
    applicable_in_notice: Mapped[bool] = mapped_column(Boolean, default=False)

    # Compensatory Off Settings (for COMP_OFF type)
    comp_off_validity_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Half Day Settings
    half_day_allowed: Mapped[bool] = mapped_column(Boolean, default=True)

    # Paid/Unpaid
    is_paid: Mapped[bool] = mapped_column(Boolean, default=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Display Order
    display_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    organization: Mapped["Organization"] = relationship()
    leave_balances: Mapped[List["LeaveBalance"]] = relationship(back_populates="leave_type")


class LeaveBalance(BaseModel):
    """Employee leave balance per leave type per year."""

    __tablename__ = "hris_leave_balance"
    __table_args__ = (
        UniqueConstraint(
            "employee_id", "leave_type_id", "year", name="uq_leave_balance_emp_type_year"
        ),
    )

    employee_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_employee.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    leave_type_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_leave_type.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)

    # Balance Components
    opening_balance: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    accrued: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    carry_forward: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    adjustment: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)  # Manual adjustments
    used: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    encashed: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)
    lapsed: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=0)  # Expired balance

    # Calculated balance = opening + accrued + carry_forward + adjustment - used - encashed - lapsed

    # Relationships
    employee: Mapped["Employee"] = relationship()
    leave_type: Mapped["LeaveType"] = relationship(back_populates="leave_balances")

    @property
    def available_balance(self) -> Decimal:
        """Calculate current available balance."""
        return (
            self.opening_balance
            + self.accrued
            + self.carry_forward
            + self.adjustment
            - self.used
            - self.encashed
            - self.lapsed
        )


class LeaveApplication(BaseModel):
    """Leave application model."""

    __tablename__ = "hris_leave_application"

    # Employee
    employee_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_employee.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    leave_type_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_leave_type.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Application Number
    application_number: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)

    # Leave Period
    from_date: Mapped[date] = mapped_column(Date, nullable=False)
    to_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_half_day: Mapped[bool] = mapped_column(Boolean, default=False)
    half_day_type: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # FIRST_HALF, SECOND_HALF

    # Duration
    total_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    working_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)  # Excluding holidays/weekends

    # Reason
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    # Contact During Leave
    contact_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    contact_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Attachments (JSONB array of URLs)
    attachments: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        SQLEnum(LeaveApplicationStatus, name="leave_application_status_enum", create_type=False),
        nullable=False,
        default=LeaveApplicationStatus.PENDING,
    )

    # Approval
    approved_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    approver_remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Rejection
    rejected_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    rejected_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Cancellation
    cancelled_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # For compensatory off - reference to worked date
    comp_off_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Relationships
    employee: Mapped["Employee"] = relationship()
    leave_type: Mapped["LeaveType"] = relationship()


class LeaveEncashment(BaseModel):
    """Leave encashment record."""

    __tablename__ = "hris_leave_encashment"

    employee_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_employee.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    leave_type_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_leave_type.id", ondelete="CASCADE"),
        nullable=False,
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)

    # Encashment Details
    encashment_date: Mapped[date] = mapped_column(Date, nullable=False)
    days_encashed: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    per_day_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    gross_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    tds_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    net_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    # Encashment Type
    encashment_type: Mapped[str] = mapped_column(String(20), default="ANNUAL")  # ANNUAL, SEPARATION, RETIREMENT

    # Payment Reference
    payroll_run_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    voucher_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)

    # Approval
    approved_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="PENDING")  # PENDING, APPROVED, PAID

    # Relationships
    employee: Mapped["Employee"] = relationship()
    leave_type: Mapped["LeaveType"] = relationship()
