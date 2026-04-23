"""Vendor Invoice Models.

Handles vendor invoice submission with 2-way/3-way matching support.
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
from app.models.vendor_portal.enums import (
    InvoiceMatchingType,
    InvoiceMatchingStatus,
    VendorInvoiceStatus,
    InvoiceDocumentType,
)

if TYPE_CHECKING:
    from app.models.vendor_portal.portal_vendor_user import PortalVendorUser
    from app.models.ap_ar.vendor import Vendor
    from app.models.ap_ar.purchase_bill import PurchaseBill


class VendorInvoice(BaseModel):
    """Vendor submitted invoice.

    Supports Indian GST structure with 2-way and 3-way matching.
    """

    __tablename__ = "portal_vendor_invoice"

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

    submitted_by_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("portal_vendor_user.id"),
        nullable=False,
    )

    # Invoice Details
    invoice_number: Mapped[str] = mapped_column(String(100), nullable=False)
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[Optional[date]] = mapped_column(Date)

    # References
    purchase_order_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        index=True,
    )
    purchase_order_number: Mapped[Optional[str]] = mapped_column(String(50))
    grn_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    grn_number: Mapped[Optional[str]] = mapped_column(String(50))

    # GST Details
    vendor_gstin: Mapped[Optional[str]] = mapped_column(String(15))
    place_of_supply: Mapped[Optional[str]] = mapped_column(String(2))  # State code
    is_reverse_charge: Mapped[bool] = mapped_column(Boolean, default=False)
    is_igst_applicable: Mapped[bool] = mapped_column(Boolean, default=False)

    # Amounts
    subtotal: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0.00")
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0.00")
    )
    taxable_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False, default=Decimal("0.00")
    )

    # GST Amounts
    cgst_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0.00")
    )
    sgst_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0.00")
    )
    igst_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0.00")
    )
    cess_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0.00")
    )

    # TDS
    tds_applicable: Mapped[bool] = mapped_column(Boolean, default=False)
    tds_section: Mapped[Optional[str]] = mapped_column(String(20))
    tds_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0.00")
    )
    tds_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0.00")
    )

    # Total
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False
    )
    round_off: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0.00")
    )
    payable_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), nullable=False
    )

    # E-Invoice Details (India GST)
    irn: Mapped[Optional[str]] = mapped_column(String(64))  # Invoice Reference Number
    irn_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    e_invoice_status: Mapped[Optional[str]] = mapped_column(String(50))

    # E-Way Bill
    e_way_bill_number: Mapped[Optional[str]] = mapped_column(String(20))
    e_way_bill_date: Mapped[Optional[date]] = mapped_column(Date)
    e_way_bill_valid_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    # Matching
    matching_type: Mapped[InvoiceMatchingType] = mapped_column(
        default=InvoiceMatchingType.TWO_WAY
    )
    matching_status: Mapped[InvoiceMatchingStatus] = mapped_column(
        default=InvoiceMatchingStatus.PENDING
    )
    po_matched: Mapped[bool] = mapped_column(Boolean, default=False)
    grn_matched: Mapped[bool] = mapped_column(Boolean, default=False)
    matching_remarks: Mapped[Optional[str]] = mapped_column(Text)
    matching_exceptions: Mapped[Optional[List[dict]]] = mapped_column(JSONB)

    # Tolerance Settings (% variance allowed)
    price_tolerance: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0.00")
    )
    quantity_tolerance: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0.00")
    )

    # Workflow Status
    status: Mapped[VendorInvoiceStatus] = mapped_column(
        default=VendorInvoiceStatus.DRAFT
    )
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Approval
    approved_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id"),
        nullable=True,
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    approval_remarks: Mapped[Optional[str]] = mapped_column(Text)

    # Rejection
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text)
    rejected_by_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_user.id"),
        nullable=True,
    )
    rejected_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Linked Purchase Bill (when approved and converted)
    purchase_bill_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("txn_purchase_bill.id"),
        nullable=True,
    )

    # Payment Info
    payment_status: Mapped[Optional[str]] = mapped_column(String(50))
    paid_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0.00")
    )
    balance_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0.00")
    )

    # Vendor Remarks
    vendor_remarks: Mapped[Optional[str]] = mapped_column(Text)
    internal_notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    vendor: Mapped["Vendor"] = relationship(
        "Vendor",
        foreign_keys=[vendor_id],
    )
    submitted_by: Mapped["PortalVendorUser"] = relationship(
        "PortalVendorUser",
        foreign_keys=[submitted_by_id],
    )
    purchase_bill: Mapped[Optional["PurchaseBill"]] = relationship(
        "PurchaseBill",
        foreign_keys=[purchase_bill_id],
    )
    lines: Mapped[List["VendorInvoiceLine"]] = relationship(
        "VendorInvoiceLine",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )
    documents: Mapped[List["VendorInvoiceDocument"]] = relationship(
        "VendorInvoiceDocument",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_portal_vendor_inv_org_vendor", "organization_id", "vendor_id"),
        Index("ix_portal_vendor_inv_status", "organization_id", "status"),
        Index("ix_portal_vendor_inv_po", "purchase_order_id"),
        Index("ix_portal_vendor_inv_num", "organization_id", "vendor_id", "invoice_number"),
    )


class VendorInvoiceLine(BaseModel):
    """Vendor invoice line item.

    Supports GST per line and matching with PO/GRN.
    """

    __tablename__ = "portal_vendor_invoice_line"

    invoice_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("portal_vendor_invoice.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Line Number
    line_number: Mapped[int] = mapped_column(Integer, nullable=False)

    # PO Reference
    po_line_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))
    po_line_number: Mapped[Optional[int]] = mapped_column(Integer)

    # GRN Reference
    grn_line_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True))

    # Item Details
    item_code: Mapped[Optional[str]] = mapped_column(String(50))
    item_description: Mapped[str] = mapped_column(Text, nullable=False)
    hsn_sac_code: Mapped[Optional[str]] = mapped_column(String(10))
    uom: Mapped[str] = mapped_column(String(20), nullable=False)

    # Quantities
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)

    # Amounts
    line_total: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    discount_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0.00")
    )
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0.00")
    )
    taxable_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # GST Rates & Amounts
    cgst_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0.00")
    )
    cgst_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0.00")
    )
    sgst_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0.00")
    )
    sgst_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0.00")
    )
    igst_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0.00")
    )
    igst_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0.00")
    )
    cess_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), default=Decimal("0.00")
    )
    cess_amount: Mapped[Decimal] = mapped_column(
        Numeric(18, 2), default=Decimal("0.00")
    )

    # Net Amount
    net_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)

    # Matching Details (for variance tracking)
    po_quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))
    po_unit_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))
    grn_quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))

    # Variance
    quantity_variance: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 4))
    price_variance: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    amount_variance: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    has_variance: Mapped[bool] = mapped_column(Boolean, default=False)
    variance_remarks: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    invoice: Mapped["VendorInvoice"] = relationship(
        "VendorInvoice", back_populates="lines"
    )

    __table_args__ = (
        Index("ix_portal_vendor_inv_line_inv", "invoice_id", "line_number"),
        Index("ix_portal_vendor_inv_line_po", "po_line_id"),
    )


class VendorInvoiceDocument(BaseModel):
    """Documents attached to vendor invoice.

    Stores uploaded documents like invoice PDF, e-way bill, etc.
    """

    __tablename__ = "portal_vendor_invoice_document"

    invoice_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("portal_vendor_invoice.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Document Details
    document_type: Mapped[InvoiceDocumentType] = mapped_column(nullable=False)
    document_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    original_filename: Mapped[Optional[str]] = mapped_column(String(255))

    # Document Metadata
    document_number: Mapped[Optional[str]] = mapped_column(String(100))
    document_date: Mapped[Optional[date]] = mapped_column(Date)

    # Verification
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    verified_remarks: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    invoice: Mapped["VendorInvoice"] = relationship(
        "VendorInvoice", back_populates="documents"
    )

    __table_args__ = (
        Index("ix_portal_vendor_inv_doc_type", "invoice_id", "document_type"),
    )
