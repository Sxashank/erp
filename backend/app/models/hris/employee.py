"""Employee and related models for HRIS module."""

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
    Time,
    Enum as SQLEnum,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.core.constants import (
    Gender,
    MaritalStatus,
    Salutation,
    EmploymentType,
    EmploymentStatus,
    DocumentType,
    FamilyRelation,
    EducationLevel,
    LifecycleEventType,
)

if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.masters.unit import Unit
    from app.models.masters.department import Department
    from app.models.masters.designation import Designation
    from app.models.hris.shift import Shift
    from app.models.hris.leave import LeaveBalance, LeaveApplication
    from app.models.hris.attendance import Attendance
    from app.models.hris.separation import Separation
    from app.models.payroll.salary_component import EmployeeSalary
    from app.models.payroll.payroll import Payslip


class Employee(BaseModel):
    """Employee master model."""

    __tablename__ = "hris_employee"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "employee_code", name="uq_employee_org_code"
        ),
    )

    # Organization
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Employee Code
    employee_code: Mapped[str] = mapped_column(String(20), nullable=False)

    # Personal Information
    salutation: Mapped[Optional[str]] = mapped_column(
        SQLEnum(Salutation, name="salutation_enum", create_type=False),
        nullable=True,
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    middle_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    gender: Mapped[str] = mapped_column(
        SQLEnum(Gender, name="gender_enum", create_type=False),
        nullable=False,
    )
    date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
    blood_group: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    marital_status: Mapped[Optional[str]] = mapped_column(
        SQLEnum(MaritalStatus, name="marital_status_enum", create_type=False),
        nullable=True,
    )
    nationality: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="Indian")

    # Contact Information
    personal_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    personal_mobile: Mapped[str] = mapped_column(String(20), nullable=False)
    official_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    official_mobile: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Emergency Contact
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    emergency_contact_relation: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Address (JSONB for flexibility)
    current_address: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    permanent_address: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    is_address_same: Mapped[bool] = mapped_column(Boolean, default=False)

    # Photo
    photo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Organization Structure
    department_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_department.id", ondelete="SET NULL"),
        nullable=True,
    )
    designation_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_designation.id", ondelete="SET NULL"),
        nullable=True,
    )
    reporting_manager_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_employee.id", ondelete="SET NULL"),
        nullable=True,
    )
    unit_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_unit.id", ondelete="SET NULL"),
        nullable=True,
    )
    cost_center_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_cost_center.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Employment Dates
    date_of_joining: Mapped[date] = mapped_column(Date, nullable=False)
    confirmation_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    probation_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    date_of_leaving: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Employment Type and Status
    employment_type: Mapped[str] = mapped_column(
        SQLEnum(EmploymentType, name="employment_type_enum", create_type=False),
        nullable=False,
        default=EmploymentType.PERMANENT,
    )
    employment_status: Mapped[str] = mapped_column(
        SQLEnum(EmploymentStatus, name="employment_status_enum", create_type=False),
        nullable=False,
        default=EmploymentStatus.ACTIVE,
    )
    notice_period_days: Mapped[int] = mapped_column(Integer, default=30)

    # Shift
    shift_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_shift.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Week Off (JSONB for flexibility - e.g., ["SATURDAY", "SUNDAY"])
    week_off_days: Mapped[Optional[list]] = mapped_column(JSONB, nullable=True, default=["SUNDAY"])

    # Linked User Account
    user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )

    # PAN and Aadhaar (for quick access)
    pan_number: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    aadhaar_number: Mapped[Optional[str]] = mapped_column(String(12), nullable=True)
    uan_number: Mapped[Optional[str]] = mapped_column(String(12), nullable=True)  # Universal Account Number for PF
    esic_number: Mapped[Optional[str]] = mapped_column(String(17), nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="employees")
    department: Mapped[Optional["Department"]] = relationship()
    designation: Mapped[Optional["Designation"]] = relationship()
    reporting_manager: Mapped[Optional["Employee"]] = relationship(
        remote_side="Employee.id",
        foreign_keys=[reporting_manager_id],
    )
    unit: Mapped[Optional["Unit"]] = relationship()
    shift: Mapped[Optional["Shift"]] = relationship()

    # Child relationships
    documents: Mapped[List["EmployeeDocument"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan"
    )
    family_members: Mapped[List["EmployeeFamily"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan"
    )
    bank_accounts: Mapped[List["EmployeeBankAccount"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan"
    )
    education: Mapped[List["EmployeeEducation"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan"
    )
    experience: Mapped[List["EmployeeExperience"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan"
    )
    statutory_info: Mapped[Optional["EmployeeStatutory"]] = relationship(
        back_populates="employee", uselist=False, cascade="all, delete-orphan"
    )
    lifecycle_events: Mapped[List["EmployeeLifecycleEvent"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan"
    )
    # Payroll relationships
    salaries: Mapped[List["EmployeeSalary"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan"
    )
    payslips: Mapped[List["Payslip"]] = relationship(
        back_populates="employee", cascade="all, delete-orphan"
    )
    # Separation relationships
    separations: Mapped[List["Separation"]] = relationship(
        back_populates="employee", foreign_keys="[Separation.employee_id]", cascade="all, delete-orphan"
    )

    @property
    def full_name(self) -> str:
        """Get full name of employee."""
        parts = [self.first_name]
        if self.middle_name:
            parts.append(self.middle_name)
        parts.append(self.last_name)
        return " ".join(parts)

    @property
    def age(self) -> int:
        """Calculate age from date of birth."""
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )


class EmployeeDocument(BaseModel):
    """Employee document storage model."""

    __tablename__ = "hris_employee_document"

    employee_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_employee.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_type: Mapped[str] = mapped_column(
        SQLEnum(DocumentType, name="document_type_enum", create_type=False),
        nullable=False,
    )
    document_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    document_name: Mapped[str] = mapped_column(String(200), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    issue_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    verified_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    employee: Mapped["Employee"] = relationship(back_populates="documents")


class EmployeeFamily(BaseModel):
    """Employee family member details."""

    __tablename__ = "hris_employee_family"

    employee_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_employee.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relation: Mapped[str] = mapped_column(
        SQLEnum(FamilyRelation, name="family_relation_enum", create_type=False),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(
        SQLEnum(Gender, name="gender_enum", create_type=False),
        nullable=True,
    )
    occupation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_dependent: Mapped[bool] = mapped_column(Boolean, default=False)
    is_nominee: Mapped[bool] = mapped_column(Boolean, default=False)
    nominee_percentage: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    is_emergency_contact: Mapped[bool] = mapped_column(Boolean, default=False)
    aadhaar_number: Mapped[Optional[str]] = mapped_column(String(12), nullable=True)

    # Relationships
    employee: Mapped["Employee"] = relationship(back_populates="family_members")


class EmployeeBankAccount(BaseModel):
    """Employee bank account details."""

    __tablename__ = "hris_employee_bank_account"
    __table_args__ = (
        UniqueConstraint(
            "employee_id", "account_number", name="uq_emp_bank_account"
        ),
    )

    employee_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_employee.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    bank_name: Mapped[str] = mapped_column(String(200), nullable=False)
    branch_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    account_number: Mapped[str] = mapped_column(String(30), nullable=False)
    ifsc_code: Mapped[str] = mapped_column(String(11), nullable=False)
    account_holder_name: Mapped[str] = mapped_column(String(200), nullable=False)
    account_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, default="SAVINGS")
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    is_salary_account: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Relationships
    employee: Mapped["Employee"] = relationship(back_populates="bank_accounts")


class EmployeeEducation(BaseModel):
    """Employee education/qualification details."""

    __tablename__ = "hris_employee_education"

    employee_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_employee.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    level: Mapped[str] = mapped_column(
        SQLEnum(EducationLevel, name="education_level_enum", create_type=False),
        nullable=False,
    )
    degree_name: Mapped[str] = mapped_column(String(200), nullable=False)
    specialization: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    institution_name: Mapped[str] = mapped_column(String(300), nullable=False)
    university_board: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    start_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    end_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    percentage_cgpa: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    grade: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_highest_qualification: Mapped[bool] = mapped_column(Boolean, default=False)
    document_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    employee: Mapped["Employee"] = relationship(back_populates="education")


class EmployeeExperience(BaseModel):
    """Employee previous work experience."""

    __tablename__ = "hris_employee_experience"

    employee_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_employee.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    company_name: Mapped[str] = mapped_column(String(300), nullable=False)
    designation: Mapped[str] = mapped_column(String(200), nullable=False)
    department: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    last_ctc: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    reason_for_leaving: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reference_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    reference_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    reference_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    experience_letter_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    relieving_letter_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Relationships
    employee: Mapped["Employee"] = relationship(back_populates="experience")

    @property
    def duration_months(self) -> int:
        """Calculate experience duration in months."""
        end = self.end_date or date.today()
        return (end.year - self.start_date.year) * 12 + (end.month - self.start_date.month)


class EmployeeStatutory(BaseModel):
    """Employee statutory compliance details (PF, ESI, PT, etc.)."""

    __tablename__ = "hris_employee_statutory"

    employee_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_employee.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # PF Details
    pf_applicable: Mapped[bool] = mapped_column(Boolean, default=True)
    pf_account_number: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    pf_join_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    pf_exit_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    is_pf_capped: Mapped[bool] = mapped_column(Boolean, default=True)  # Contribution capped at 15000
    voluntary_pf_rate: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)  # VPF %

    # ESI Details
    esi_applicable: Mapped[bool] = mapped_column(Boolean, default=False)
    esi_number: Mapped[Optional[str]] = mapped_column(String(17), nullable=True)
    esi_dispensary: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Professional Tax
    pt_applicable: Mapped[bool] = mapped_column(Boolean, default=True)
    pt_state: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    pt_location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Labour Welfare Fund
    lwf_applicable: Mapped[bool] = mapped_column(Boolean, default=False)

    # TDS / Income Tax
    tax_regime: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, default="NEW")  # OLD or NEW
    it_section_declarations: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)  # 80C, 80D, etc.

    # Gratuity
    gratuity_applicable: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    employee: Mapped["Employee"] = relationship(back_populates="statutory_info")


class EmployeeLifecycleEvent(BaseModel):
    """Track employee lifecycle events like joining, promotion, transfer, etc."""

    __tablename__ = "hris_employee_lifecycle_event"

    employee_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hris_employee.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(
        SQLEnum(LifecycleEventType, name="lifecycle_event_type_enum", create_type=False),
        nullable=False,
    )
    event_date: Mapped[date] = mapped_column(Date, nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Old values (JSONB for flexibility)
    old_values: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    # New values
    new_values: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # For transfers
    from_department_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    to_department_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    from_designation_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    to_designation_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    from_unit_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )
    to_unit_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True), nullable=True
    )

    # Approval
    approved_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Reference document
    document_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    document_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    employee: Mapped["Employee"] = relationship(back_populates="lifecycle_events")
