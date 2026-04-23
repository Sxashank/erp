"""Sales Invoice model."""

import enum
from datetime import date
from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.ap_ar.customer import Customer
    from app.models.masters.organization import Organization
    from app.models.masters.unit import Unit
    from app.models.finance.voucher import Voucher
    from app.models.gst.gst_rate import GSTRate
    from app.models.finance.account import Account
    from app.models.workflow import WorkflowInstance


class InvoiceStatus(str, enum.Enum):
    """Invoice status enum."""
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED"
    RECEIVED = "RECEIVED"
    CANCELLED = "CANCELLED"


class ReceiptStatus(str, enum.Enum):
    """Receipt status enum."""
    UNRECEIVED = "UNRECEIVED"
    PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED"
    RECEIVED = "RECEIVED"


class InvoiceSupplyType(str, enum.Enum):
    """Supply type for GST."""
    INTRA_STATE = "INTRA_STATE"
    INTER_STATE = "INTER_STATE"
    EXPORT = "EXPORT"
    SEZ = "SEZ"


class EInvoiceStatus(str, enum.Enum):
    """E-Invoice status enum."""
    NOT_APPLICABLE = "NOT_APPLICABLE"
    PENDING = "PENDING"
    GENERATED = "GENERATED"
    CANCELLED = "CANCELLED"


class SalesInvoice(BaseModel):
    """Sales Invoice model for customer invoices."""

    __tablename__ = "txn_sales_invoice"

    # Invoice identification
    invoice_number: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Customer reference
    customer_id: Mapped[UUID] = mapped_column(
        ForeignKey("mst_customer.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Organization & Unit
    organization_id: Mapped[UUID] = mapped_column(
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    unit_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("mst_unit.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Amounts
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0")
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0")
    )
    taxable_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0")
    )
    cgst_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0")
    )
    sgst_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0")
    )
    igst_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0")
    )
    cess_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0")
    )
    tcs_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0")
    )
    round_off: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0")
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0")
    )
    balance_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0")
    )

    # GST Details
    is_reverse_charge: Mapped[bool] = mapped_column(Boolean, default=False)
    supply_type: Mapped[Optional[InvoiceSupplyType]] = mapped_column(
        Enum(InvoiceSupplyType), nullable=True
    )
    customer_gstin: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    place_of_supply: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)

    # E-Invoice Details
    e_invoice_required: Mapped[bool] = mapped_column(Boolean, default=False)
    irn: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    irn_date: Mapped[Optional[date]] = mapped_column(DateTime(timezone=True), nullable=True)
    qr_code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    e_invoice_status: Mapped[EInvoiceStatus] = mapped_column(
        Enum(EInvoiceStatus), nullable=False, default=EInvoiceStatus.NOT_APPLICABLE
    )
    ack_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ack_date: Mapped[Optional[date]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Status & Workflow
    status: Mapped[InvoiceStatus] = mapped_column(
        Enum(InvoiceStatus), nullable=False, default=InvoiceStatus.DRAFT, index=True
    )
    receipt_status: Mapped[ReceiptStatus] = mapped_column(
        Enum(ReceiptStatus), nullable=False, default=ReceiptStatus.UNRECEIVED, index=True
    )

    # GL Integration
    voucher_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("txn_voucher.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_posted: Mapped[bool] = mapped_column(Boolean, default=False)

    # Workflow Integration
    workflow_instance_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("wf_workflow_instance.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Narration & Reference
    narration: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reference_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    po_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    po_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Shipping Details
    shipping_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    transporter_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    vehicle_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    eway_bill_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    eway_bill_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Relationships
    customer: Mapped["Customer"] = relationship(back_populates="sales_invoices")
    organization: Mapped["Organization"] = relationship()
    unit: Mapped[Optional["Unit"]] = relationship()
    voucher: Mapped[Optional["Voucher"]] = relationship()
    workflow_instance: Mapped[Optional["WorkflowInstance"]] = relationship()
    lines: Mapped[List["SalesInvoiceLine"]] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan",
        order_by="SalesInvoiceLine.line_number",
    )

    def __repr__(self) -> str:
        return f"<SalesInvoice {self.invoice_number}>"


class SalesInvoiceLine(BaseModel):
    """Sales Invoice Line model."""

    __tablename__ = "txn_sales_invoice_line"

    # Parent reference
    invoice_id: Mapped[UUID] = mapped_column(
        ForeignKey("txn_sales_invoice.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # Item details
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    hsn_sac_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Quantity & Pricing
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), nullable=False, default=Decimal("1")
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), nullable=False, default=Decimal("0")
    )
    discount_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0")
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0")
    )
    taxable_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0")
    )

    # GST Details
    gst_rate_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("mst_gst_rate.id", ondelete="SET NULL"),
        nullable=True,
    )
    cgst_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0")
    )
    cgst_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0")
    )
    sgst_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0")
    )
    sgst_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0")
    )
    igst_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0")
    )
    igst_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0")
    )
    cess_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=Decimal("0")
    )
    cess_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0")
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0")
    )

    # Account mapping
    revenue_account_id: Mapped[Optional[UUID]] = mapped_column(
        ForeignKey("mst_account.id", ondelete="SET NULL"),
        nullable=True,
    )
    cost_center_id: Mapped[Optional[UUID]] = mapped_column(nullable=True)

    # Relationships
    invoice: Mapped["SalesInvoice"] = relationship(back_populates="lines")
    gst_rate: Mapped[Optional["GSTRate"]] = relationship()
    revenue_account: Mapped[Optional["Account"]] = relationship()

    def __repr__(self) -> str:
        return f"<SalesInvoiceLine {self.invoice_id}:{self.line_number}>"
