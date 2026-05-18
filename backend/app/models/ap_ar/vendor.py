"""Vendor/Supplier master model."""

from datetime import date
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
from uuid import UUID
import enum

from sqlalchemy import ForeignKey, Numeric, String, Integer, Boolean, Text, Enum, Date
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import BalanceType
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.ap_ar.payment_terms import PaymentTerms
    from app.models.tds.tds_section import TDSSection
    from app.models.finance.account import Account
    from app.models.ap_ar.payment import Payment


class VendorType(str, enum.Enum):
    """Vendor type enumeration."""
    SUPPLIER = "SUPPLIER"
    CONTRACTOR = "CONTRACTOR"
    SERVICE_PROVIDER = "SERVICE_PROVIDER"
    OTHERS = "OTHERS"


class MSMEType(str, enum.Enum):
    """MSME classification as per MSMED Act."""
    MICRO = "MICRO"
    SMALL = "SMALL"
    MEDIUM = "MEDIUM"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class GSTRegistrationType(str, enum.Enum):
    """GST registration type enumeration."""
    REGULAR = "REGULAR"
    COMPOSITION = "COMPOSITION"
    UNREGISTERED = "UNREGISTERED"
    SEZ = "SEZ"
    DEEMED_EXPORT = "DEEMED_EXPORT"


class PaymentModePreference(str, enum.Enum):
    """Payment mode preference enumeration."""
    CHEQUE = "CHEQUE"
    NEFT = "NEFT"
    RTGS = "RTGS"
    UPI = "UPI"
    CASH = "CASH"


class Vendor(BaseModel):
    """Vendor/Supplier master for accounts payable."""

    __tablename__ = "mst_vendor"

    # Basic Info
    code: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="Vendor code e.g., V001",
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Legal name of vendor",
    )
    display_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Trade/Display name",
    )
    vendor_type: Mapped[VendorType] = mapped_column(
        Enum(VendorType),
        nullable=False,
        default=VendorType.SUPPLIER,
        comment="Type of vendor",
    )
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Organization this vendor belongs to",
    )

    # Tax & Compliance
    pan: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="PAN number",
    )
    gstin: Mapped[Optional[str]] = mapped_column(
        String(15),
        nullable=True,
        comment="GST registration number",
    )
    gst_registration_type: Mapped[Optional[GSTRegistrationType]] = mapped_column(
        Enum(GSTRegistrationType),
        nullable=True,
        default=GSTRegistrationType.REGULAR,
        comment="GST registration type",
    )
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
    # Lower Deduction Certificate (LDC) fields for TDS
    ldc_certificate_no: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Lower Deduction Certificate number",
    )
    ldc_rate: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Lower TDS rate as per certificate (e.g., 0.5%)",
    )
    ldc_limit: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(18, 2),
        nullable=True,
        comment="Maximum amount covered under LDC",
    )
    ldc_valid_from: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="LDC validity start date",
    )
    ldc_valid_until: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="LDC validity end date",
    )
    ldc_utilized: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Amount utilized against LDC limit",
    )
    tds_applicable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Is TDS applicable",
    )
    tds_section_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_tds_section.id", ondelete="SET NULL"),
        nullable=True,
        comment="Default TDS section",
    )
    tds_rate_override: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        comment="Override TDS rate (null = use section default)",
    )

    # Contact & Address
    contact_person: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Primary contact person name",
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Email address",
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Phone number",
    )
    mobile: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Mobile number",
    )
    address_line1: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Address line 1",
    )
    address_line2: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
        comment="Address line 2",
    )
    city: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="City",
    )
    state_code: Mapped[Optional[str]] = mapped_column(
        String(2),
        nullable=True,
        comment="State code for GST place of supply",
    )
    pincode: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="PIN code",
    )
    country: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="India",
        comment="Country",
    )

    # Banking Details
    bank_name: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Bank name",
    )
    bank_account_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Bank account number",
    )
    bank_ifsc_code: Mapped[Optional[str]] = mapped_column(
        String(11),
        nullable=True,
        comment="Bank IFSC code",
    )
    bank_branch: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Bank branch",
    )
    payment_mode_preference: Mapped[Optional[PaymentModePreference]] = mapped_column(
        Enum(PaymentModePreference),
        nullable=True,
        default=PaymentModePreference.NEFT,
        comment="Preferred payment mode",
    )

    # Financial Settings
    control_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account.id", ondelete="SET NULL"),
        nullable=True,
        comment="Default payable (control) account",
    )
    expense_account_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_account.id", ondelete="SET NULL"),
        nullable=True,
        comment="Default expense account",
    )
    payment_terms_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_payment_terms.id", ondelete="SET NULL"),
        nullable=True,
        comment="Default payment terms",
    )
    credit_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=30,
        comment="Credit period in days",
    )
    credit_limit: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Credit limit amount",
    )
    currency_code: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="INR",
        comment="Default currency",
    )

    # Balances
    opening_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Opening balance amount",
    )
    opening_balance_type: Mapped[Optional[BalanceType]] = mapped_column(
        Enum(BalanceType),
        nullable=True,
        comment="Opening balance type (DR/CR)",
    )
    current_balance: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Current balance amount",
    )
    current_balance_type: Mapped[Optional[BalanceType]] = mapped_column(
        Enum(BalanceType),
        nullable=True,
        comment="Current balance type (DR/CR)",
    )

    # Remarks
    remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Additional remarks/notes",
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="vendors",
    )
    payment_terms: Mapped[Optional["PaymentTerms"]] = relationship(
        "PaymentTerms",
        foreign_keys=[payment_terms_id],
    )
    tds_section: Mapped[Optional["TDSSection"]] = relationship(
        "TDSSection",
        foreign_keys=[tds_section_id],
    )
    control_account: Mapped[Optional["Account"]] = relationship(
        "Account",
        foreign_keys=[control_account_id],
    )
    expense_account: Mapped[Optional["Account"]] = relationship(
        "Account",
        foreign_keys=[expense_account_id],
    )
    payments: Mapped[list["Payment"]] = relationship(
        "Payment",
        back_populates="vendor",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Vendor(code={self.code}, name={self.name})>"
