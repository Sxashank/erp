"""
Salary Component Models

Defines:
- SalaryComponent: Master of earnings and deductions
- SalaryStructure: Template for employee salary composition
- SalaryStructureComponent: Components within a structure
- EmployeeSalary: Employee's salary assignment
- EmployeeSalaryComponent: Individual employee component overrides
"""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import Boolean, Date, ForeignKey, String, Text, Enum as SQLEnum, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.hris.employee import Employee


class ComponentType:
    """Salary component types"""
    EARNING = "EARNING"
    DEDUCTION = "DEDUCTION"


class CalculationType:
    """How the component amount is calculated"""
    FIXED = "FIXED"  # Fixed amount
    PERCENTAGE_OF_BASIC = "PERCENTAGE_OF_BASIC"  # % of Basic
    PERCENTAGE_OF_GROSS = "PERCENTAGE_OF_GROSS"  # % of Gross
    PERCENTAGE_OF_CTC = "PERCENTAGE_OF_CTC"  # % of CTC
    FORMULA = "FORMULA"  # Custom formula


class ComponentCategory:
    """Category for grouping/reporting"""
    BASIC = "BASIC"
    ALLOWANCE = "ALLOWANCE"
    REIMBURSEMENT = "REIMBURSEMENT"
    STATUTORY = "STATUTORY"  # PF, ESI, PT, etc.
    BONUS = "BONUS"
    VARIABLE = "VARIABLE"
    OTHER = "OTHER"


class SalaryComponent(BaseModel):
    """
    Master table for salary components (earnings and deductions).
    Each organization can have its own set of components.
    """
    __tablename__ = "payroll_salary_component"
    __table_args__ = (
        UniqueConstraint("organization_id", "component_code", name="uq_salary_component_org_code"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False
    )

    component_code: Mapped[str] = mapped_column(String(20), nullable=False)
    component_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    component_type: Mapped[str] = mapped_column(String(20), nullable=False)  # EARNING, DEDUCTION
    category: Mapped[str] = mapped_column(String(20), nullable=False, default=ComponentCategory.OTHER)

    calculation_type: Mapped[str] = mapped_column(String(30), nullable=False, default=CalculationType.FIXED)
    default_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)  # Fixed amount or percentage
    formula: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # For FORMULA type

    # Tax treatment
    is_taxable: Mapped[bool] = mapped_column(Boolean, default=True)
    tax_exemption_limit: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)
    exemption_section: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # e.g., 10(14), 80C

    # Statutory flags
    is_part_of_basic: Mapped[bool] = mapped_column(Boolean, default=False)
    is_part_of_gross: Mapped[bool] = mapped_column(Boolean, default=True)
    is_part_of_ctc: Mapped[bool] = mapped_column(Boolean, default=True)
    affects_pf: Mapped[bool] = mapped_column(Boolean, default=False)  # Part of PF wage
    affects_esi: Mapped[bool] = mapped_column(Boolean, default=False)  # Part of ESI wage
    affects_pt: Mapped[bool] = mapped_column(Boolean, default=False)  # Part of PT wage
    affects_gratuity: Mapped[bool] = mapped_column(Boolean, default=False)

    # Display order
    display_order: Mapped[int] = mapped_column(default=0)
    show_on_payslip: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="salary_components")
    structure_components: Mapped[List["SalaryStructureComponent"]] = relationship(
        back_populates="component",
        cascade="all, delete-orphan"
    )


class SalaryStructure(BaseModel):
    """
    Salary structure template that can be assigned to employees.
    Defines the composition of salary using components.
    """
    __tablename__ = "payroll_salary_structure"
    __table_args__ = (
        UniqueConstraint("organization_id", "structure_code", name="uq_salary_structure_org_code"),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False
    )

    structure_code: Mapped[str] = mapped_column(String(20), nullable=False)
    structure_name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Payroll settings
    payment_mode: Mapped[str] = mapped_column(String(20), default="BANK")  # BANK, CASH, CHEQUE
    pay_frequency: Mapped[str] = mapped_column(String(20), default="MONTHLY")  # MONTHLY, WEEKLY, BIWEEKLY

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="salary_structures")
    components: Mapped[List["SalaryStructureComponent"]] = relationship(
        back_populates="structure",
        cascade="all, delete-orphan"
    )
    employee_salaries: Mapped[List["EmployeeSalary"]] = relationship(
        back_populates="structure"
    )


class SalaryStructureComponent(BaseModel):
    """
    Components within a salary structure with their configuration.
    """
    __tablename__ = "payroll_salary_structure_component"
    __table_args__ = (
        UniqueConstraint("structure_id", "component_id", name="uq_structure_component"),
    )

    structure_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("payroll_salary_structure.id", ondelete="CASCADE"),
        nullable=False
    )
    component_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("payroll_salary_component.id"),
        nullable=False
    )

    calculation_type: Mapped[str] = mapped_column(String(30), nullable=False)  # Override from component
    value: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)  # Fixed or percentage
    formula: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    structure: Mapped["SalaryStructure"] = relationship(back_populates="components")
    component: Mapped["SalaryComponent"] = relationship(back_populates="structure_components")


class EmployeeSalary(BaseModel):
    """
    Employee's salary assignment linking to a structure.
    Tracks salary revisions over time.
    """
    __tablename__ = "payroll_employee_salary"

    employee_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_employee.id"),
        nullable=False
    )
    structure_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("payroll_salary_structure.id"),
        nullable=False
    )

    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Annual figures
    annual_ctc: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    annual_gross: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    annual_net: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)

    # Monthly figures
    monthly_ctc: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    monthly_gross: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    monthly_basic: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    monthly_net: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2), nullable=True)

    # Revision tracking
    revision_number: Mapped[int] = mapped_column(default=1)
    revision_reason: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    previous_salary_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("payroll_employee_salary.id"),
        nullable=True
    )

    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")  # ACTIVE, SUPERSEDED

    # Relationships
    employee: Mapped["Employee"] = relationship(back_populates="salaries")
    structure: Mapped["SalaryStructure"] = relationship(back_populates="employee_salaries")
    components: Mapped[List["EmployeeSalaryComponent"]] = relationship(
        back_populates="employee_salary",
        cascade="all, delete-orphan"
    )


class EmployeeSalaryComponent(BaseModel):
    """
    Individual component values for an employee's salary.
    Allows overriding structure defaults.
    """
    __tablename__ = "payroll_employee_salary_component"
    __table_args__ = (
        UniqueConstraint("employee_salary_id", "component_id", name="uq_employee_salary_component"),
    )

    employee_salary_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("payroll_employee_salary.id", ondelete="CASCADE"),
        nullable=False
    )
    component_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("payroll_salary_component.id"),
        nullable=False
    )

    monthly_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    annual_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # Override flags
    is_overridden: Mapped[bool] = mapped_column(Boolean, default=False)  # Manual override

    # Relationships
    employee_salary: Mapped["EmployeeSalary"] = relationship(back_populates="components")
    component: Mapped["SalaryComponent"] = relationship()
