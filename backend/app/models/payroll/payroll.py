"""
Payroll Processing Models

Defines:
- PayrollBatch: Monthly payroll processing batch
- Payslip: Individual employee payslip
- PayslipComponent: Earning/deduction lines on payslip
- StatutorySetup: PF, ESI, PT configuration
- PayrollStatutory: Calculated statutory for each payslip
"""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text, Numeric, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.hris.employee import Employee
    from app.models.payroll.salary_component import SalaryComponent


class PayrollBatchStatus:
    """Payroll batch status values"""
    DRAFT = "DRAFT"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    APPROVED = "APPROVED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class PayslipStatus:
    """Payslip status values"""
    DRAFT = "DRAFT"
    GENERATED = "GENERATED"
    APPROVED = "APPROVED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class StatutorySetup(BaseModel):
    """
    Statutory compliance configuration per organization.
    Stores PF, ESI, PT rates and settings.
    """
    __tablename__ = "payroll_statutory_setup"
    __table_args__ = (
        UniqueConstraint("organization_id", "statutory_type", name="uq_statutory_setup_org_type"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False
    )

    statutory_type: Mapped[str] = mapped_column(String(20), nullable=False)  # PF, ESI, PT, LWF

    # PF Settings
    pf_employer_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)  # 12%
    pf_employee_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)  # 12%
    pf_admin_charge_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)  # 0.5%
    pf_edli_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)  # 0.5%
    pf_wage_ceiling: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)  # 15000
    eps_employer_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)  # 8.33%
    eps_wage_ceiling: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)  # 15000

    # ESI Settings
    esi_employer_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)  # 3.25%
    esi_employee_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)  # 0.75%
    esi_wage_ceiling: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)  # 21000

    # PT Settings (state-wise slabs stored as JSON)
    pt_state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    pt_slabs: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # LWF Settings
    lwf_employer_contribution: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    lwf_employee_contribution: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    lwf_frequency: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # MONTHLY, HALF_YEARLY

    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="statutory_setups")


class PayrollBatch(BaseModel):
    """
    Monthly payroll processing batch.
    Groups all payslips for a pay period.
    """
    __tablename__ = "payroll_batch"
    __table_args__ = (
        UniqueConstraint("organization_id", "payroll_month", "payroll_year", name="uq_payroll_batch_period"),
        Index("ix_payroll_batch_org_status", "organization_id", "status"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False
    )

    batch_number: Mapped[str] = mapped_column(String(30), nullable=False)  # e.g., PAY/2026/01/001
    payroll_month: Mapped[int] = mapped_column(nullable=False)  # 1-12
    payroll_year: Mapped[int] = mapped_column(nullable=False)

    pay_period_from: Mapped[date] = mapped_column(Date, nullable=False)
    pay_period_to: Mapped[date] = mapped_column(Date, nullable=False)
    payment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Totals
    total_employees: Mapped[int] = mapped_column(default=0)
    total_gross: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    total_deductions: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    total_net: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    total_employer_statutory: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)

    # Statutory totals
    total_pf_employee: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    total_pf_employer: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    total_esi_employee: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    total_esi_employer: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    total_pt: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    total_tds: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)

    status: Mapped[str] = mapped_column(String(20), default=PayrollBatchStatus.DRAFT)

    # Processing timestamps
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    approved_by: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="payroll_batches")
    payslips: Mapped[List["Payslip"]] = relationship(
        back_populates="batch",
        cascade="all, delete-orphan"
    )


class Payslip(BaseModel):
    """
    Individual employee payslip for a pay period.
    """
    __tablename__ = "payroll_payslip"
    __table_args__ = (
        UniqueConstraint("batch_id", "employee_id", name="uq_payslip_batch_employee"),
        Index("ix_payslip_employee", "employee_id"),
    )

    batch_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("payroll_batch.id", ondelete="CASCADE"),
        nullable=False
    )
    employee_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_employee.id"),
        nullable=False
    )

    payslip_number: Mapped[str] = mapped_column(String(30), nullable=False)

    # Employee snapshot (at time of payroll)
    employee_code: Mapped[str] = mapped_column(String(20), nullable=False)
    employee_name: Mapped[str] = mapped_column(String(200), nullable=False)
    department_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    designation_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pan_number: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    uan_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    esi_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    bank_account_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    bank_ifsc: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)

    # Attendance data
    working_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    days_present: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    days_absent: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    leave_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    lop_days: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)  # Loss of Pay
    overtime_hours: Mapped[Decimal] = mapped_column(Numeric(7, 2), default=0)

    # Salary figures
    gross_salary: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    total_earnings: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    total_deductions: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    net_salary: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # Statutory details
    pf_wage: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    esi_wage: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    pt_wage: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    taxable_income: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)

    # Employer contributions (not in net, but tracked)
    employer_pf: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    employer_esi: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)

    # Arrears
    arrears_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    arrears_remarks: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    status: Mapped[str] = mapped_column(String(20), default=PayslipStatus.DRAFT)

    # Payment details
    payment_mode: Mapped[str] = mapped_column(String(20), default="BANK")
    payment_reference: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    batch: Mapped["PayrollBatch"] = relationship(back_populates="payslips")
    employee: Mapped["Employee"] = relationship(back_populates="payslips")
    components: Mapped[List["PayslipComponent"]] = relationship(
        back_populates="payslip",
        cascade="all, delete-orphan"
    )
    statutory: Mapped[List["PayrollStatutory"]] = relationship(
        back_populates="payslip",
        cascade="all, delete-orphan"
    )


class PayslipComponent(BaseModel):
    """
    Individual earning/deduction line items on a payslip.
    """
    __tablename__ = "payroll_payslip_component"
    __table_args__ = (
        UniqueConstraint("payslip_id", "component_id", name="uq_payslip_component"),
    )

    payslip_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("payroll_payslip.id", ondelete="CASCADE"),
        nullable=False
    )
    component_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("payroll_salary_component.id"),
        nullable=False
    )

    component_code: Mapped[str] = mapped_column(String(20), nullable=False)
    component_name: Mapped[str] = mapped_column(String(100), nullable=False)
    component_type: Mapped[str] = mapped_column(String(20), nullable=False)  # EARNING, DEDUCTION

    # Amounts
    standard_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)  # Full month
    actual_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)  # After LOP etc.
    arrears_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)

    # Tax treatment
    is_taxable: Mapped[bool] = mapped_column(Boolean, default=True)
    taxable_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)

    display_order: Mapped[int] = mapped_column(default=0)

    # Relationships
    payslip: Mapped["Payslip"] = relationship(back_populates="components")
    component: Mapped["SalaryComponent"] = relationship()


class PayrollStatutory(BaseModel):
    """
    Statutory calculation details for each payslip.
    Stores PF, ESI, PT, TDS breakup.
    """
    __tablename__ = "payroll_statutory"
    __table_args__ = (
        UniqueConstraint("payslip_id", "statutory_type", name="uq_payroll_statutory_type"),
    )

    payslip_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("payroll_payslip.id", ondelete="CASCADE"),
        nullable=False
    )

    statutory_type: Mapped[str] = mapped_column(String(20), nullable=False)  # PF, ESI, PT, TDS, LWF

    # Common fields
    wage_base: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)

    # Employee contribution
    employee_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    employee_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)

    # Employer contribution
    employer_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    employer_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)

    # PF specific
    eps_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)  # Employer's EPS
    edli_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)  # Employer's EDLI
    admin_charges: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)

    # TDS specific
    projected_annual_income: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    total_deductions_declared: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    taxable_income: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)
    tax_regime: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # OLD, NEW

    total_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0)  # Total statutory

    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    payslip: Mapped["Payslip"] = relationship(back_populates="statutory")
