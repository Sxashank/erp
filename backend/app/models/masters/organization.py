"""Organization master model."""

from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.core.constants import EntityStatus

if TYPE_CHECKING:
    from app.models.auth.user import User
    from app.models.masters.unit import Unit
    from app.models.masters.department import Department
    from app.models.masters.organization_bank_account import OrganizationBankAccount
    from app.models.masters.organization_address import OrganizationAddress
    from app.models.finance.financial_year import FinancialYear
    from app.models.finance.account_group import AccountGroup
    from app.models.finance.account import Account
    from app.models.finance.voucher_type import VoucherType
    from app.models.finance.voucher import Voucher
    from app.models.ap_ar.payment_terms import PaymentTerms
    from app.models.ap_ar.vendor import Vendor
    from app.models.ap_ar.customer import Customer
    from app.models.core.integration_config import IntegrationConfig
    from app.models.fixed_assets.lease import Lease
    from app.models.hris.employee import Employee
    from app.models.payroll.payroll import StatutorySetup, PayrollBatch
    from app.models.payroll.salary_component import SalaryComponent, SalaryStructure


class Organization(BaseModel):
    """Organization master - top level entity."""

    __tablename__ = "mst_organization"

    # Basic info
    code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    legal_name: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
    )
    short_name: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Registration details
    cin: Mapped[Optional[str]] = mapped_column(
        String(25),
        unique=True,
        nullable=True,
    )
    pan: Mapped[str] = mapped_column(
        String(10),
        unique=True,
        nullable=False,
    )
    tan: Mapped[Optional[str]] = mapped_column(
        String(10),
        unique=True,
        nullable=True,
    )
    gstin: Mapped[Optional[str]] = mapped_column(
        String(15),
        nullable=True,
    )
    rbi_registration: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    # Address - Registered
    reg_address_line1: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    reg_address_line2: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    reg_city: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    reg_district: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    reg_state_code: Mapped[Optional[str]] = mapped_column(
        String(2),
        nullable=True,
    )
    reg_pincode: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
    )
    reg_country: Mapped[str] = mapped_column(
        String(50),
        default="India",
        nullable=False,
    )

    # Contact
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    website: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )

    # Financial
    base_currency: Mapped[str] = mapped_column(
        String(3),
        default="INR",
        nullable=False,
    )
    financial_year_start_month: Mapped[int] = mapped_column(
        default=4,  # April
        nullable=False,
    )

    # Branding
    logo_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    primary_color: Mapped[Optional[str]] = mapped_column(
        String(7),  # Hex color
        nullable=True,
    )

    # Status
    status: Mapped[str] = mapped_column(
        String(20),
        default=EntityStatus.ACTIVE.value,
        nullable=False,
        index=True,
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Relationships
    units: Mapped[List["Unit"]] = relationship(
        "Unit",
        back_populates="organization",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    departments: Mapped[List["Department"]] = relationship(
        "Department",
        back_populates="organization",
        lazy="selectin",
        cascade="all, delete-orphan",
    )
    bank_accounts: Mapped[List["OrganizationBankAccount"]] = relationship(
        "OrganizationBankAccount",
        back_populates="organization",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    addresses: Mapped[List["OrganizationAddress"]] = relationship(
        "OrganizationAddress",
        back_populates="organization",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    users: Mapped[List["User"]] = relationship(
        "User",
        back_populates="organization",
        foreign_keys="[User.organization_id]",
        lazy="selectin",
    )
    # Finance relationships
    financial_years: Mapped[List["FinancialYear"]] = relationship(
        "FinancialYear",
        back_populates="organization",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    account_groups: Mapped[List["AccountGroup"]] = relationship(
        "AccountGroup",
        back_populates="organization",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    accounts: Mapped[List["Account"]] = relationship(
        "Account",
        back_populates="organization",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    voucher_types: Mapped[List["VoucherType"]] = relationship(
        "VoucherType",
        back_populates="organization",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    vouchers: Mapped[List["Voucher"]] = relationship(
        "Voucher",
        back_populates="organization",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    # AP/AR relationships
    payment_terms: Mapped[List["PaymentTerms"]] = relationship(
        "PaymentTerms",
        back_populates="organization",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    vendors: Mapped[List["Vendor"]] = relationship(
        "Vendor",
        back_populates="organization",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    customers: Mapped[List["Customer"]] = relationship(
        "Customer",
        back_populates="organization",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    # Integration settings
    integration_configs: Mapped[List["IntegrationConfig"]] = relationship(
        "IntegrationConfig",
        back_populates="organization",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    # Fixed Assets - Leases
    leases: Mapped[List["Lease"]] = relationship(
        "Lease",
        back_populates="organization",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    # HRIS
    employees: Mapped[List["Employee"]] = relationship(
        "Employee",
        back_populates="organization",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    # Payroll
    statutory_setups: Mapped[List["StatutorySetup"]] = relationship(
        "StatutorySetup",
        back_populates="organization",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    payroll_batches: Mapped[List["PayrollBatch"]] = relationship(
        "PayrollBatch",
        back_populates="organization",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    salary_components: Mapped[List["SalaryComponent"]] = relationship(
        "SalaryComponent",
        back_populates="organization",
        lazy="noload",
        cascade="all, delete-orphan",
    )
    salary_structures: Mapped[List["SalaryStructure"]] = relationship(
        "SalaryStructure",
        back_populates="organization",
        lazy="noload",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Organization(code={self.code}, name={self.name})>"
