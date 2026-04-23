"""Purchase Order model."""

import enum
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class POStatus(str, enum.Enum):
    """Purchase Order status enum."""
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    SENT_TO_VENDOR = "SENT_TO_VENDOR"
    PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED"
    RECEIVED = "RECEIVED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class POAckStatus(str, enum.Enum):
    """PO Acknowledgement status enum."""
    PENDING = "PENDING"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    REJECTED = "REJECTED"
    CHANGE_REQUESTED = "CHANGE_REQUESTED"


class SupplyType(str, enum.Enum):
    """GST supply type enum."""
    INTRA_STATE = "INTRA_STATE"
    INTER_STATE = "INTER_STATE"


if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.masters.unit import Unit
    from app.models.ap_ar.vendor import Vendor
    from app.models.gst.gst_rate import GSTRate
    from app.models.workflow import WorkflowInstance


class PurchaseOrder(BaseModel):
    """Purchase Order header."""

    __tablename__ = "txn_purchase_order"

    # PO Info
    po_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
    )
    po_date: Mapped["Date"] = mapped_column(
        Date,
        nullable=False,
    )
    expected_delivery_date: Mapped[Optional["Date"]] = mapped_column(
        Date,
        nullable=True,
    )
    delivery_address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # References
    vendor_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_vendor.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    unit_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_unit.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Amounts
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
    )
    taxable_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
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
    round_off: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
    )

    # GST Details
    supply_type: Mapped[Optional[SupplyType]] = mapped_column(
        Enum(SupplyType),
        nullable=True,
    )
    vendor_gstin: Mapped[Optional[str]] = mapped_column(
        String(15),
        nullable=True,
    )
    place_of_supply: Mapped[Optional[str]] = mapped_column(
        String(2),
        nullable=True,
    )

    # Status
    status: Mapped[POStatus] = mapped_column(
        Enum(POStatus),
        nullable=False,
        default=POStatus.DRAFT,
        index=True,
    )

    # Vendor Acknowledgement
    acknowledgement_status: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        default="PENDING",
    )
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )
    sent_to_vendor_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    # Fulfillment Tracking
    received_quantity_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0"),
    )
    billed_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
    )

    # Payment Terms
    payment_terms: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )
    credit_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Notes
    narration: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    terms_and_conditions: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    internal_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Workflow
    workflow_instance_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("wf_workflow_instance.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Relationships
    vendor: Mapped["Vendor"] = relationship(
        "Vendor",
        foreign_keys=[vendor_id],
        lazy="selectin",
    )
    organization: Mapped["Organization"] = relationship(
        "Organization",
        foreign_keys=[organization_id],
        lazy="selectin",
    )
    unit: Mapped[Optional["Unit"]] = relationship(
        "Unit",
        foreign_keys=[unit_id],
        lazy="selectin",
    )
    workflow_instance: Mapped[Optional["WorkflowInstance"]] = relationship(
        "WorkflowInstance",
        foreign_keys=[workflow_instance_id],
        lazy="selectin",
    )
    lines: Mapped[List["PurchaseOrderLine"]] = relationship(
        "PurchaseOrderLine",
        back_populates="purchase_order",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrder(number={self.po_number}, vendor={self.vendor_id})>"


class PurchaseOrderLine(BaseModel):
    """Purchase Order line item."""

    __tablename__ = "txn_purchase_order_line"

    # Parent
    purchase_order_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_purchase_order.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    line_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Item Details
    item_code: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    description: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    hsn_sac_code: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )
    uom: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
    )

    # Quantity and Price
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
        default=Decimal("1"),
    )
    unit_price: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
        default=Decimal("0"),
    )

    # Discount
    discount_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0"),
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
    )

    # Amounts
    taxable_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
    )

    # GST
    gst_rate_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_gst_rate.id", ondelete="SET NULL"),
        nullable=True,
    )
    cgst_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0"),
    )
    cgst_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
    )
    sgst_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0"),
    )
    sgst_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
    )
    igst_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0"),
    )
    igst_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
    )
    cess_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        default=Decimal("0"),
    )
    cess_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
    )

    # Total
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2),
        nullable=False,
        default=Decimal("0"),
    )

    # Fulfillment Tracking
    received_quantity: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
        default=Decimal("0"),
    )
    pending_quantity: Mapped[Decimal] = mapped_column(
        Numeric(18, 4),
        nullable=False,
        default=Decimal("0"),
    )
    is_closed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="lines",
        lazy="selectin",
    )
    gst_rate: Mapped[Optional["GSTRate"]] = relationship(
        "GSTRate",
        foreign_keys=[gst_rate_id],
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<PurchaseOrderLine(po={self.purchase_order_id}, line={self.line_number})>"
