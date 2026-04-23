"""Advanced Shipping Notice (ASN) Models.

Handles ASN creation and tracking from vendor portal.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    String,
    Boolean,
    ForeignKey,
    Text,
    DateTime,
    Date,
    Index,
    Integer,
    Numeric,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.vendor_portal.enums import ASNStatus

if TYPE_CHECKING:
    from app.models.vendor_portal.portal_vendor_user import PortalVendorUser
    from app.models.ap_ar.vendor import Vendor


class AdvancedShippingNotice(BaseModel):
    """Advanced Shipping Notice from vendor.

    Notifies buyer about incoming shipment details before delivery.
    """

    __tablename__ = "portal_asn"

    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id"),
        nullable=False,
        index=True,
    )

    vendor_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_vendor.id"),
        nullable=False,
        index=True,
    )

    created_by_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("portal_vendor_user.id"),
        nullable=False,
    )

    # ASN Details
    asn_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False
    )
    asn_date: Mapped[date] = mapped_column(Date, nullable=False)

    # PO Reference
    purchase_order_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    purchase_order_number: Mapped[str] = mapped_column(String(50), nullable=False)

    # Shipment Details
    ship_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_delivery_date: Mapped[date] = mapped_column(Date, nullable=False)
    actual_delivery_date: Mapped[Optional[date]] = mapped_column(Date)

    # Carrier Information
    carrier_name: Mapped[Optional[str]] = mapped_column(String(100))
    carrier_code: Mapped[Optional[str]] = mapped_column(String(50))
    tracking_number: Mapped[Optional[str]] = mapped_column(String(100))
    tracking_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Vehicle Details
    vehicle_number: Mapped[Optional[str]] = mapped_column(String(20))
    vehicle_type: Mapped[Optional[str]] = mapped_column(String(50))
    driver_name: Mapped[Optional[str]] = mapped_column(String(100))
    driver_phone: Mapped[Optional[str]] = mapped_column(String(15))

    # Packaging Details
    total_packages: Mapped[int] = mapped_column(Integer, default=1)
    total_weight: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 3))
    weight_uom: Mapped[Optional[str]] = mapped_column(String(10))  # KG, LB
    total_volume: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 3))
    volume_uom: Mapped[Optional[str]] = mapped_column(String(10))  # CBM, CFT

    # Shipping Address
    ship_from_address: Mapped[Optional[str]] = mapped_column(Text)
    ship_to_address: Mapped[Optional[str]] = mapped_column(Text)
    delivery_location: Mapped[Optional[str]] = mapped_column(String(200))

    # E-Way Bill (India)
    e_way_bill_number: Mapped[Optional[str]] = mapped_column(String(20))
    e_way_bill_date: Mapped[Optional[date]] = mapped_column(Date)
    e_way_bill_valid_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    # LR/Transport Document
    lr_number: Mapped[Optional[str]] = mapped_column(String(50))  # Lorry Receipt
    lr_date: Mapped[Optional[date]] = mapped_column(Date)
    transport_document_path: Mapped[Optional[str]] = mapped_column(String(500))

    # Status
    status: Mapped[ASNStatus] = mapped_column(default=ASNStatus.DRAFT)
    dispatched_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    in_transit_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Receipt Information
    received_by: Mapped[Optional[str]] = mapped_column(String(100))
    received_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    grn_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    grn_number: Mapped[Optional[str]] = mapped_column(String(50))

    # Remarks
    vendor_remarks: Mapped[Optional[str]] = mapped_column(Text)
    delivery_instructions: Mapped[Optional[str]] = mapped_column(Text)
    internal_notes: Mapped[Optional[str]] = mapped_column(Text)

    # Cancellation
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    vendor: Mapped["Vendor"] = relationship(
        "Vendor",
        foreign_keys=[vendor_id],
    )
    created_by: Mapped["PortalVendorUser"] = relationship(
        "PortalVendorUser",
        foreign_keys=[created_by_id],
    )
    lines: Mapped[List["ASNLine"]] = relationship(
        "ASNLine",
        back_populates="asn",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_portal_asn_org_vendor", "organization_id", "vendor_id"),
        Index("ix_portal_asn_po", "purchase_order_id"),
        Index("ix_portal_asn_status", "organization_id", "status"),
        Index("ix_portal_asn_tracking", "tracking_number"),
    )


class ASNLine(BaseModel):
    """ASN line item.

    Details of items being shipped in the ASN.
    """

    __tablename__ = "portal_asn_line"

    asn_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("portal_asn.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Line Number
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # PO Reference
    po_line_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        nullable=False,
    )
    po_line_number: Mapped[Optional[int]] = mapped_column(Integer)

    # Item Details
    item_code: Mapped[str] = mapped_column(String(50), nullable=False)
    item_description: Mapped[str] = mapped_column(Text, nullable=False)
    hsn_sac_code: Mapped[Optional[str]] = mapped_column(String(10))
    uom: Mapped[str] = mapped_column(String(20), nullable=False)

    # Quantities
    ordered_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    shipped_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    received_quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))
    rejected_quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))
    accepted_quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))

    # Batch/Serial Tracking
    batch_number: Mapped[Optional[str]] = mapped_column(String(50))
    serial_numbers: Mapped[Optional[List[str]]] = mapped_column(JSONB)
    manufacturing_date: Mapped[Optional[date]] = mapped_column(Date)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date)

    # Quality Details
    quality_check_required: Mapped[bool] = mapped_column(Boolean, default=False)
    quality_check_status: Mapped[Optional[str]] = mapped_column(String(50))
    quality_remarks: Mapped[Optional[str]] = mapped_column(Text)

    # Packaging
    package_count: Mapped[Optional[int]] = mapped_column(Integer)
    package_type: Mapped[Optional[str]] = mapped_column(String(50))  # Box, Pallet, etc.
    weight: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 3))

    # Price (for reference)
    unit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))
    line_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))

    # Remarks
    remarks: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    asn: Mapped["AdvancedShippingNotice"] = relationship(
        "AdvancedShippingNotice", back_populates="lines"
    )

    __table_args__ = (
        Index("ix_portal_asn_line_asn", "asn_id", "line_number"),
        Index("ix_portal_asn_line_po", "po_line_id"),
        Index("ix_portal_asn_line_batch", "batch_number"),
    )
