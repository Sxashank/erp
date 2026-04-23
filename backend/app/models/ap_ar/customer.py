"""Customer master model."""

import enum
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import Boolean, Date, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.ap_ar.vendor import GSTRegistrationType, PaymentModePreference, BalanceType, MSMEType


class CustomerType(str, enum.Enum):
    """Customer type enum."""
    INDIVIDUAL = "INDIVIDUAL"
    COMPANY = "COMPANY"
    GOVERNMENT = "GOVERNMENT"
    OTHERS = "OTHERS"


if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.tds.tds_section import TDSSection
    from app.models.finance.account import Account
    from app.models.ap_ar.payment_terms import PaymentTerms
    from app.models.ap_ar.sales_invoice import SalesInvoice
    from app.models.ap_ar.payment import Payment


class Customer(BaseModel):
    """Customer master - sub-ledger for AR."""

    __tablename__ = "mst_customer"

    # Basic Info
    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    display_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )
    customer_type: Mapped[CustomerType] = mapped_column(
        Enum(CustomerType),
        nullable=False,
        default=CustomerType.COMPANY,
    )
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Tax & Compliance
    pan: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
    )
    gstin: Mapped[Optional[str]] = mapped_column(
        String(15),
        nullable=True,
        index=True,
    )
    gst_registration_type: Mapped[Optional[GSTRegistrationType]] = mapped_column(
        Enum(GSTRegistrationType),
        nullable=True,
    )
    place_of_supply_state: Mapped[Optional[str]] = mapped_column(
        String(2),
        nullable=True,
    )
    tcs_applicable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    tcs_section_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_tds_section.id", ondelete="SET NULL"),
        nullable=True,
    )

    # MSME fields (mirroring vendor)
    msme_registered: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Is MSME registered",
    )
    msme_number: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="MSME registration number (UAM/Udyam)",
    )
    msme_type: Mapped[MSMEType] = mapped_column(
        Enum(MSMEType),
        nullable=False,
        default=MSMEType.NOT_APPLICABLE,
        comment="MSME classification: MICRO, SMALL, MEDIUM",
    )
    msme_valid_until: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="MSME certificate validity date",
    )

    # E-Invoice fields
    e_invoice_applicable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Is E-Invoice applicable for this customer",
    )
    e_invoice_exemption_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Reason for E-Invoice exemption if not applicable",
    )

    # Contact & Address - Billing
    contact_person: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    mobile: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    billing_address_line1: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )
    billing_address_line2: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )
    billing_city: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    billing_state_code: Mapped[Optional[str]] = mapped_column(
        String(2),
        nullable=True,
    )
    billing_pincode: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
    )
    billing_country: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="India",
    )

    # Shipping Address
    shipping_address_line1: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )
    shipping_address_line2: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )
    shipping_city: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    shipping_state_code: Mapped[Optional[str]] = mapped_column(
        String(2),
        nullable=True,
    )
    shipping_pincode: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
    )
    shipping_country: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="India",
    )

    # Banking Details (for refunds)
    bank_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    bank_account_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    bank_ifsc_code: Mapped[Optional[str]] = mapped_column(
        String(11),
        nullable=True,
    )
    bank_branch: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    payment_mode_preference: Mapped[Optional[PaymentModePreference]] = mapped_column(
        Enum(PaymentModePreference),
        nullable=True,
    )

    # Financial Settings
    control_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account.id", ondelete="SET NULL"),
        nullable=True,
    )
    revenue_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account.id", ondelete="SET NULL"),
        nullable=True,
    )
    payment_terms_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_payment_terms.id", ondelete="SET NULL"),
        nullable=True,
    )
    credit_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=30,
    )
    credit_limit: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
    )
    credit_limit_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="INR",
    )

    # Balances
    opening_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
    )
    opening_balance_type: Mapped[Optional[BalanceType]] = mapped_column(
        Enum(BalanceType),
        nullable=True,
    )
    current_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
    )
    current_balance_type: Mapped[Optional[BalanceType]] = mapped_column(
        Enum(BalanceType),
        nullable=True,
    )

    # Notes
    remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="customers",
        lazy="selectin",
    )
    tcs_section: Mapped[Optional["TDSSection"]] = relationship(
        "TDSSection",
        foreign_keys=[tcs_section_id],
        lazy="selectin",
    )
    control_account: Mapped[Optional["Account"]] = relationship(
        "Account",
        foreign_keys=[control_account_id],
        lazy="selectin",
    )
    revenue_account: Mapped[Optional["Account"]] = relationship(
        "Account",
        foreign_keys=[revenue_account_id],
        lazy="selectin",
    )
    payment_terms: Mapped[Optional["PaymentTerms"]] = relationship(
        "PaymentTerms",
        foreign_keys=[payment_terms_id],
        lazy="selectin",
    )
    sales_invoices: Mapped[list["SalesInvoice"]] = relationship(
        "SalesInvoice",
        back_populates="customer",
        lazy="selectin",
    )
    payments: Mapped[list["Payment"]] = relationship(
        "Payment",
        back_populates="customer",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Customer(code={self.code}, name={self.name})>"
