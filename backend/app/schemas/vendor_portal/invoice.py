"""Vendor Invoice Schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, AuditSchema
from app.models.vendor_portal.enums import (
    InvoiceMatchingType,
    InvoiceMatchingStatus,
    VendorInvoiceStatus,
    InvoiceDocumentType,
)


class VendorInvoiceLineCreate(BaseSchema):
    """Create invoice line item."""

    po_line_id: Optional[UUID] = None
    po_line_number: Optional[int] = None

    item_code: Optional[str] = Field(None, max_length=50)
    item_description: str = Field(..., max_length=500)
    hsn_sac_code: Optional[str] = Field(None, max_length=10)
    uom: str = Field(..., max_length=20)

    quantity: Decimal = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)

    discount_percent: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    discount_amount: Decimal = Field(default=Decimal("0"), ge=0)

    cgst_rate: Decimal = Field(default=Decimal("0"), ge=0, le=50)
    sgst_rate: Decimal = Field(default=Decimal("0"), ge=0, le=50)
    igst_rate: Decimal = Field(default=Decimal("0"), ge=0, le=50)
    cess_rate: Decimal = Field(default=Decimal("0"), ge=0, le=50)


class VendorInvoiceLineUpdate(BaseSchema):
    """Update invoice line item."""

    item_code: Optional[str] = Field(None, max_length=50)
    item_description: Optional[str] = Field(None, max_length=500)
    hsn_sac_code: Optional[str] = Field(None, max_length=10)
    uom: Optional[str] = Field(None, max_length=20)

    quantity: Optional[Decimal] = Field(None, gt=0)
    unit_price: Optional[Decimal] = Field(None, ge=0)

    discount_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    discount_amount: Optional[Decimal] = Field(None, ge=0)

    cgst_rate: Optional[Decimal] = Field(None, ge=0, le=50)
    sgst_rate: Optional[Decimal] = Field(None, ge=0, le=50)
    igst_rate: Optional[Decimal] = Field(None, ge=0, le=50)
    cess_rate: Optional[Decimal] = Field(None, ge=0, le=50)


class VendorInvoiceLineResponse(BaseSchema):
    """Invoice line item response."""

    id: UUID
    line_number: int
    po_line_id: Optional[UUID] = None
    po_line_number: Optional[int] = None
    grn_line_id: Optional[UUID] = None

    item_code: Optional[str] = None
    item_description: str
    hsn_sac_code: Optional[str] = None
    uom: str

    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal
    discount_percent: Decimal
    discount_amount: Decimal
    taxable_amount: Decimal

    cgst_rate: Decimal
    cgst_amount: Decimal
    sgst_rate: Decimal
    sgst_amount: Decimal
    igst_rate: Decimal
    igst_amount: Decimal
    cess_rate: Decimal
    cess_amount: Decimal
    net_amount: Decimal

    # Matching details
    po_quantity: Optional[Decimal] = None
    po_unit_price: Optional[Decimal] = None
    grn_quantity: Optional[Decimal] = None
    quantity_variance: Optional[Decimal] = None
    price_variance: Optional[Decimal] = None
    amount_variance: Optional[Decimal] = None
    has_variance: bool = False
    variance_remarks: Optional[str] = None


class VendorInvoiceCreate(BaseSchema):
    """Create vendor invoice."""

    invoice_number: str = Field(..., max_length=100)
    invoice_date: date
    due_date: Optional[date] = None

    # References
    purchase_order_id: Optional[UUID] = None
    purchase_order_number: Optional[str] = Field(None, max_length=50)
    grn_id: Optional[UUID] = None
    grn_number: Optional[str] = Field(None, max_length=50)

    # GST Details
    vendor_gstin: Optional[str] = Field(None, max_length=15)
    place_of_supply: Optional[str] = Field(None, max_length=2)
    is_reverse_charge: bool = False

    # Matching Type
    matching_type: InvoiceMatchingType = InvoiceMatchingType.TWO_WAY

    # E-Invoice
    irn: Optional[str] = Field(None, max_length=64)

    # E-Way Bill
    e_way_bill_number: Optional[str] = Field(None, max_length=20)
    e_way_bill_date: Optional[date] = None

    # Lines
    lines: List[VendorInvoiceLineCreate] = []

    # Remarks
    vendor_remarks: Optional[str] = None


class VendorInvoiceUpdate(BaseSchema):
    """Update vendor invoice."""

    invoice_number: Optional[str] = Field(None, max_length=100)
    invoice_date: Optional[date] = None
    due_date: Optional[date] = None

    purchase_order_id: Optional[UUID] = None
    purchase_order_number: Optional[str] = Field(None, max_length=50)
    grn_id: Optional[UUID] = None
    grn_number: Optional[str] = Field(None, max_length=50)

    vendor_gstin: Optional[str] = Field(None, max_length=15)
    place_of_supply: Optional[str] = Field(None, max_length=2)
    is_reverse_charge: Optional[bool] = None

    matching_type: Optional[InvoiceMatchingType] = None

    irn: Optional[str] = Field(None, max_length=64)
    e_way_bill_number: Optional[str] = Field(None, max_length=20)
    e_way_bill_date: Optional[date] = None

    vendor_remarks: Optional[str] = None


class VendorInvoiceDocumentCreate(BaseSchema):
    """Create invoice document."""

    document_type: InvoiceDocumentType
    document_name: str = Field(..., max_length=255)
    document_number: Optional[str] = Field(None, max_length=100)
    document_date: Optional[date] = None


class VendorInvoiceDocumentResponse(BaseSchema):
    """Invoice document response."""

    id: UUID
    document_type: InvoiceDocumentType
    document_name: str
    file_path: str
    file_size: int
    mime_type: str
    document_number: Optional[str] = None
    document_date: Optional[date] = None
    is_verified: bool
    created_at: datetime


class VendorInvoiceResponse(BaseSchema):
    """Invoice response."""

    id: UUID
    vendor_id: UUID
    organization_id: UUID

    invoice_number: str
    invoice_date: date
    due_date: Optional[date] = None

    purchase_order_id: Optional[UUID] = None
    purchase_order_number: Optional[str] = None
    grn_id: Optional[UUID] = None
    grn_number: Optional[str] = None

    vendor_gstin: Optional[str] = None
    place_of_supply: Optional[str] = None
    is_reverse_charge: bool
    is_igst_applicable: bool

    # Amounts
    subtotal: Decimal
    discount_amount: Decimal
    taxable_amount: Decimal
    cgst_amount: Decimal
    sgst_amount: Decimal
    igst_amount: Decimal
    cess_amount: Decimal
    tds_applicable: bool
    tds_section: Optional[str] = None
    tds_rate: Decimal
    tds_amount: Decimal
    total_amount: Decimal
    round_off: Decimal
    payable_amount: Decimal

    # E-Invoice
    irn: Optional[str] = None
    irn_date: Optional[datetime] = None
    e_invoice_status: Optional[str] = None

    # E-Way Bill
    e_way_bill_number: Optional[str] = None
    e_way_bill_date: Optional[date] = None

    # Matching
    matching_type: InvoiceMatchingType
    matching_status: InvoiceMatchingStatus
    po_matched: bool
    grn_matched: bool
    matching_remarks: Optional[str] = None

    # Status
    status: VendorInvoiceStatus
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

    # Payment
    payment_status: Optional[str] = None
    paid_amount: Decimal
    balance_amount: Decimal

    # Purchase Bill Link
    purchase_bill_id: Optional[UUID] = None

    vendor_remarks: Optional[str] = None

    lines: List[VendorInvoiceLineResponse] = []
    documents: List[VendorInvoiceDocumentResponse] = []

    created_at: datetime
    updated_at: Optional[datetime] = None


class InvoiceMatchingResult(BaseSchema):
    """Invoice matching validation result."""

    is_matched: bool
    matching_type: InvoiceMatchingType
    matching_status: InvoiceMatchingStatus

    po_matched: bool
    po_match_details: Optional[List[dict]] = None

    grn_matched: bool
    grn_match_details: Optional[List[dict]] = None

    exceptions: List[dict] = []
    warnings: List[str] = []

    can_submit: bool
    message: str


class InvoiceSubmitResponse(BaseSchema):
    """Invoice submission response."""

    success: bool
    invoice_id: UUID
    invoice_number: str
    status: VendorInvoiceStatus
    matching_status: InvoiceMatchingStatus
    message: str
    exceptions: List[dict] = []


class VendorInvoiceListResponse(BaseSchema):
    """Invoice list item response."""

    id: UUID
    invoice_number: str
    invoice_date: date
    due_date: Optional[date] = None
    purchase_order_number: Optional[str] = None
    total_amount: Decimal
    status: VendorInvoiceStatus
    matching_status: InvoiceMatchingStatus
    payment_status: Optional[str] = None
    paid_amount: Decimal
    balance_amount: Decimal
    created_at: datetime
