"""E-Invoice and E-Way Bill models.

Models for:
- E-Invoice generation via IRP (Invoice Registration Portal)
- E-Way Bill generation via NIC Portal
- IRN (Invoice Reference Number) tracking
- QR code storage
"""

from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Optional, List
from uuid import UUID, uuid4

from sqlalchemy import (
    String, Text, ForeignKey, Enum as SQLEnum, Boolean, Date, DateTime,
    Numeric, Integer, UniqueConstraint, Index, func
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.gst.gst_registration import GSTRegistration
    from app.models.ap_ar.sales_invoice import SalesInvoice


# =============================================================================
# Enums for E-Invoice and E-Way Bill
# =============================================================================

class EInvoiceProvider(str, Enum):
    """E-Invoice service provider (IRP)."""
    NIC = "NIC"              # National Informatics Centre (default)
    CLEARTAX = "CLEARTAX"    # ClearTax GSP
    TALLY = "TALLY"          # Tally GSP
    ZOHO = "ZOHO"            # Zoho GSP


class EInvoiceRequestStatus(str, Enum):
    """Status of E-Invoice generation request."""
    PENDING = "PENDING"          # Request created, not yet sent
    PROCESSING = "PROCESSING"    # Request sent to IRP
    SUCCESS = "SUCCESS"          # IRN generated successfully
    FAILED = "FAILED"            # Generation failed
    CANCELLED = "CANCELLED"      # IRN cancelled


class EWayBillProvider(str, Enum):
    """E-Way Bill service provider."""
    NIC = "NIC"              # National Informatics Centre
    CLEARTAX = "CLEARTAX"    # ClearTax GSP
    MANUAL = "MANUAL"        # Manual entry


class EWayBillStatus(str, Enum):
    """Status of E-Way Bill."""
    DRAFT = "DRAFT"
    GENERATED = "GENERATED"
    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    EXTENDED = "EXTENDED"


class TransportMode(str, Enum):
    """Mode of transportation."""
    ROAD = "1"      # Road
    RAIL = "2"      # Rail
    AIR = "3"       # Air
    SHIP = "4"      # Ship


class VehicleType(str, Enum):
    """Type of vehicle for road transport."""
    REGULAR = "R"       # Regular vehicle
    ODC = "O"           # Over Dimensional Cargo


class TransactionType(str, Enum):
    """Transaction type for E-Way Bill."""
    REGULAR = "1"       # Regular
    BILL_TO_SHIP_TO = "2"    # Bill To - Ship To
    BILL_FROM_DISPATCH = "3"  # Bill From - Dispatch From
    COMBINATION = "4"    # Combination of 2 and 3


class SubSupplyType(str, Enum):
    """Sub-supply type for detailed classification."""
    SUPPLY = "1"
    IMPORT = "2"
    EXPORT = "3"
    JOB_WORK = "4"
    FOR_OWN_USE = "5"
    JOB_WORK_RETURNS = "6"
    SALES_RETURN = "7"
    OTHERS = "8"
    SKD_CKD = "9"
    LINE_SALES = "10"
    RECIPIENT_NOT_KNOWN = "11"
    EXHIBITION = "12"


# =============================================================================
# E-Invoice Request Model
# =============================================================================

class EInvoiceRequest(Base, TimestampMixin):
    """E-Invoice generation request tracking.

    Tracks each attempt to generate E-Invoice for a sales invoice.
    Stores IRN, QR code, and response from IRP.
    """

    __tablename__ = "gst_einvoice_request"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    gst_registration_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_gst_registration.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sales_invoice_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_sales_invoice.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Provider
    provider: Mapped[EInvoiceProvider] = mapped_column(
        SQLEnum(EInvoiceProvider),
        nullable=False,
        default=EInvoiceProvider.NIC,
    )

    # Request details
    request_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    status: Mapped[EInvoiceRequestStatus] = mapped_column(
        SQLEnum(EInvoiceRequestStatus),
        nullable=False,
        default=EInvoiceRequestStatus.PENDING,
        index=True,
    )

    # Generated values
    irn: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        unique=True,
        index=True,
        comment="Invoice Reference Number from IRP",
    )
    ack_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Acknowledgment number from IRP",
    )
    ack_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    signed_invoice: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Digitally signed invoice JSON",
    )
    signed_qr_code: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Signed QR code data",
    )
    qr_code_image: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Base64 encoded QR code image",
    )

    # E-Way Bill auto-generation (if applicable)
    eway_bill_auto_generated: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    eway_bill_number: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="E-Way bill number if auto-generated",
    )
    eway_bill_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    eway_bill_validity: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Request/Response data for debugging
    request_payload: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="JSON payload sent to IRP",
    )
    response_payload: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="JSON response from IRP",
    )

    # Error handling
    error_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    error_details: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )
    retry_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Cancellation
    is_cancelled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    cancel_reason: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )
    cancel_remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    cancelled_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )

    # User tracking
    initiated_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    gst_registration: Mapped["GSTRegistration"] = relationship(
        "GSTRegistration",
        lazy="selectin",
    )
    sales_invoice: Mapped["SalesInvoice"] = relationship(
        "SalesInvoice",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_einvoice_request_org_status", "organization_id", "status"),
        Index("ix_einvoice_request_invoice", "sales_invoice_id"),
        Index("ix_einvoice_request_irn", "irn"),
    )

    def __repr__(self) -> str:
        return f"<EInvoiceRequest(invoice={self.sales_invoice_id}, irn={self.irn}, status={self.status})>"


# =============================================================================
# E-Way Bill Model
# =============================================================================

class EWayBill(Base, TimestampMixin):
    """E-Way Bill tracking model.

    Tracks E-Way bills generated for goods movement.
    Can be linked to sales invoice or created standalone.
    """

    __tablename__ = "gst_eway_bill"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    gst_registration_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_gst_registration.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Linked documents (optional)
    sales_invoice_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_sales_invoice.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    einvoice_request_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("gst_einvoice_request.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Provider
    provider: Mapped[EWayBillProvider] = mapped_column(
        SQLEnum(EWayBillProvider),
        nullable=False,
        default=EWayBillProvider.NIC,
    )

    # E-Way Bill details
    eway_bill_number: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        unique=True,
        index=True,
    )
    eway_bill_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    valid_from: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    valid_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[EWayBillStatus] = mapped_column(
        SQLEnum(EWayBillStatus),
        nullable=False,
        default=EWayBillStatus.DRAFT,
        index=True,
    )

    # Document reference
    document_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="INV",
        comment="INV/BOE/CHL/BIL/CNT/OTH",
    )
    document_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    document_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    # Transaction details
    transaction_type: Mapped[TransactionType] = mapped_column(
        SQLEnum(TransactionType),
        nullable=False,
        default=TransactionType.REGULAR,
    )
    sub_supply_type: Mapped[SubSupplyType] = mapped_column(
        SQLEnum(SubSupplyType),
        nullable=False,
        default=SubSupplyType.SUPPLY,
    )

    # Supplier (From)
    supplier_gstin: Mapped[str] = mapped_column(
        String(15),
        nullable=False,
        index=True,
    )
    supplier_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    supplier_address: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    supplier_place: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    supplier_pincode: Mapped[str] = mapped_column(
        String(6),
        nullable=False,
    )
    supplier_state_code: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
    )

    # Recipient (To)
    recipient_gstin: Mapped[Optional[str]] = mapped_column(
        String(15),
        nullable=True,
        index=True,
    )
    recipient_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    recipient_address: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    recipient_place: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    recipient_pincode: Mapped[str] = mapped_column(
        String(6),
        nullable=False,
    )
    recipient_state_code: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
    )

    # Dispatch details (if different from supplier)
    dispatch_from_gstin: Mapped[Optional[str]] = mapped_column(
        String(15),
        nullable=True,
    )
    dispatch_from_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )
    dispatch_from_address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    dispatch_from_place: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    dispatch_from_pincode: Mapped[Optional[str]] = mapped_column(
        String(6),
        nullable=True,
    )
    dispatch_from_state_code: Mapped[Optional[str]] = mapped_column(
        String(2),
        nullable=True,
    )

    # Ship to details (if different from recipient)
    ship_to_gstin: Mapped[Optional[str]] = mapped_column(
        String(15),
        nullable=True,
    )
    ship_to_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )
    ship_to_address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    ship_to_place: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    ship_to_pincode: Mapped[Optional[str]] = mapped_column(
        String(6),
        nullable=True,
    )
    ship_to_state_code: Mapped[Optional[str]] = mapped_column(
        String(2),
        nullable=True,
    )

    # Item details (summary)
    total_quantity: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
    )
    hsn_code: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
        comment="Primary HSN code",
    )
    product_description: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    # Value details
    taxable_value: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )
    cgst_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
    )
    sgst_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
    )
    igst_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
    )
    cess_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
    )
    total_value: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )

    # Transport details
    transport_mode: Mapped[TransportMode] = mapped_column(
        SQLEnum(TransportMode),
        nullable=False,
        default=TransportMode.ROAD,
    )
    transporter_id: Mapped[Optional[str]] = mapped_column(
        String(15),
        nullable=True,
        comment="Transporter GSTIN",
    )
    transporter_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )
    transport_doc_number: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="LR/RR/Consignment/AWB number",
    )
    transport_doc_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    # Vehicle details (for road transport)
    vehicle_number: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    vehicle_type: Mapped[Optional[VehicleType]] = mapped_column(
        SQLEnum(VehicleType),
        nullable=True,
    )

    # Distance
    approximate_distance: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Distance in KM",
    )

    # Extension tracking
    extension_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    last_extended_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Cancellation
    is_cancelled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    cancel_reason_code: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
    )
    cancel_remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    cancelled_by: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Request/Response tracking
    request_payload: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )
    response_payload: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )
    error_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # User tracking
    created_by_user: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    gst_registration: Mapped["GSTRegistration"] = relationship(
        "GSTRegistration",
        lazy="selectin",
    )
    sales_invoice: Mapped[Optional["SalesInvoice"]] = relationship(
        "SalesInvoice",
        lazy="selectin",
    )
    einvoice_request: Mapped[Optional["EInvoiceRequest"]] = relationship(
        "EInvoiceRequest",
        lazy="selectin",
    )
    items: Mapped[List["EWayBillItem"]] = relationship(
        "EWayBillItem",
        back_populates="eway_bill",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    vehicle_updates: Mapped[List["EWayBillVehicleUpdate"]] = relationship(
        "EWayBillVehicleUpdate",
        back_populates="eway_bill",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_eway_bill_org_status", "organization_id", "status"),
        Index("ix_eway_bill_number", "eway_bill_number"),
        Index("ix_eway_bill_supplier", "supplier_gstin"),
        Index("ix_eway_bill_validity", "valid_until"),
    )

    def __repr__(self) -> str:
        return f"<EWayBill(number={self.eway_bill_number}, status={self.status})>"

    @property
    def is_valid(self) -> bool:
        """Check if E-Way bill is still valid."""
        if self.status not in [EWayBillStatus.GENERATED, EWayBillStatus.ACTIVE, EWayBillStatus.EXTENDED]:
            return False
        if not self.valid_until:
            return False
        return datetime.utcnow() < self.valid_until.replace(tzinfo=None)


class EWayBillItem(Base, TimestampMixin):
    """E-Way Bill line items.

    Stores individual items in an E-Way Bill for HSN-wise details.
    """

    __tablename__ = "gst_eway_bill_item"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    eway_bill_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("gst_eway_bill.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Item details
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    product_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    product_description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    hsn_code: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
    )
    unit: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="NOS",
    )

    # Values
    taxable_value: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
    )
    cgst_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0"),
    )
    sgst_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0"),
    )
    igst_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0"),
    )
    cess_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0"),
    )

    # Relationship
    eway_bill: Mapped["EWayBill"] = relationship(
        "EWayBill",
        back_populates="items",
    )

    __table_args__ = (
        UniqueConstraint("eway_bill_id", "line_number", name="uq_eway_bill_item_line"),
    )

    def __repr__(self) -> str:
        return f"<EWayBillItem(hsn={self.hsn_code}, qty={self.quantity})>"


class EWayBillVehicleUpdate(Base, TimestampMixin):
    """E-Way Bill vehicle update/transit history.

    Tracks vehicle changes during transit (Part B updates).
    """

    __tablename__ = "gst_eway_bill_vehicle_update"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    eway_bill_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("gst_eway_bill.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Update details
    update_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="VEHICLE_CHANGE/TRANSPORTER_CHANGE/EXTENSION",
    )
    update_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Previous values
    previous_vehicle_number: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    previous_transporter_id: Mapped[Optional[str]] = mapped_column(
        String(15),
        nullable=True,
    )
    previous_valid_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # New values
    new_vehicle_number: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    new_transporter_id: Mapped[Optional[str]] = mapped_column(
        String(15),
        nullable=True,
    )
    new_valid_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # From place (for vehicle update)
    from_place: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    from_state_code: Mapped[Optional[str]] = mapped_column(
        String(2),
        nullable=True,
    )

    # Reason
    reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Response
    response_payload: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
    )

    # User tracking
    updated_by_user: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationship
    eway_bill: Mapped["EWayBill"] = relationship(
        "EWayBill",
        back_populates="vehicle_updates",
    )

    __table_args__ = (
        Index("ix_eway_bill_vehicle_update_time", "eway_bill_id", "update_time"),
    )

    def __repr__(self) -> str:
        return f"<EWayBillVehicleUpdate(type={self.update_type}, time={self.update_time})>"
