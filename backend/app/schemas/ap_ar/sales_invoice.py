"""Sales Invoice schemas."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from app.schemas.base import CamelSchema


class SalesInvoiceLineBase(CamelSchema):
    """Base schema for sales invoice line."""

    line_number: int = Field(..., ge=1)
    description: str = Field(..., min_length=1, max_length=500)
    hsn_sac_code: str | None = Field(None, max_length=20)
    quantity: Decimal = Field(default=Decimal("1"), ge=0)
    unit_price: Decimal = Field(default=Decimal("0"), ge=0)
    discount_percent: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    discount_amount: Decimal = Field(default=Decimal("0"), ge=0)
    taxable_amount: Decimal = Field(default=Decimal("0"), ge=0)
    gst_rate_id: UUID | None = None
    cgst_rate: Decimal = Field(default=Decimal("0"), ge=0)
    cgst_amount: Decimal = Field(default=Decimal("0"), ge=0)
    sgst_rate: Decimal = Field(default=Decimal("0"), ge=0)
    sgst_amount: Decimal = Field(default=Decimal("0"), ge=0)
    igst_rate: Decimal = Field(default=Decimal("0"), ge=0)
    igst_amount: Decimal = Field(default=Decimal("0"), ge=0)
    cess_rate: Decimal = Field(default=Decimal("0"), ge=0)
    cess_amount: Decimal = Field(default=Decimal("0"), ge=0)
    total_amount: Decimal = Field(default=Decimal("0"), ge=0)
    revenue_account_id: UUID | None = None


class SalesInvoiceLineCreate(SalesInvoiceLineBase):
    """Schema for creating a sales invoice line."""

    pass


class SalesInvoiceLineResponse(SalesInvoiceLineBase):
    """Schema for sales invoice line response."""

    id: UUID
    invoice_id: UUID


class SalesInvoiceBase(CamelSchema):
    """Base schema for sales invoice."""

    invoice_date: date
    due_date: date
    customer_id: UUID
    organization_id: UUID
    unit_id: UUID | None = None
    place_of_supply: str | None = Field(None, max_length=2)
    supply_type: str | None = None
    is_reverse_charge: bool = False
    tcs_amount: Decimal = Field(default=Decimal("0"), ge=0)
    round_off: Decimal = Field(default=Decimal("0"))
    narration: str | None = None
    reference_number: str | None = Field(None, max_length=100)
    po_number: str | None = Field(None, max_length=100)
    po_date: date | None = None
    shipping_address: str | None = None
    transporter_name: str | None = Field(None, max_length=200)
    vehicle_number: str | None = Field(None, max_length=20)
    e_invoice_required: bool = False
    irn: str | None = Field(None, max_length=64)
    irn_date: datetime | None = None
    ack_number: str | None = Field(None, max_length=50)
    ack_date: datetime | None = None
    e_invoice_status: str | None = None
    eway_bill_number: str | None = Field(None, max_length=20)
    eway_bill_date: date | None = None


class SalesInvoiceCreate(SalesInvoiceBase):
    """Schema for creating a sales invoice."""

    lines: list[SalesInvoiceLineCreate] = Field(..., min_length=1)


class SalesInvoiceUpdate(CamelSchema):
    """Schema for updating a sales invoice."""

    invoice_date: date | None = None
    due_date: date | None = None
    unit_id: UUID | None = None
    place_of_supply: str | None = Field(None, max_length=2)
    supply_type: str | None = None
    is_reverse_charge: bool | None = None
    tcs_amount: Decimal | None = None
    round_off: Decimal | None = None
    narration: str | None = None
    reference_number: str | None = Field(None, max_length=100)
    po_number: str | None = Field(None, max_length=100)
    po_date: date | None = None
    shipping_address: str | None = None
    transporter_name: str | None = Field(None, max_length=200)
    vehicle_number: str | None = Field(None, max_length=20)
    e_invoice_required: bool | None = None
    irn: str | None = Field(None, max_length=64)
    irn_date: datetime | None = None
    ack_number: str | None = Field(None, max_length=50)
    ack_date: datetime | None = None
    e_invoice_status: str | None = None
    eway_bill_number: str | None = Field(None, max_length=20)
    eway_bill_date: date | None = None
    lines: list[SalesInvoiceLineCreate] | None = None


class SalesInvoiceResponse(CamelSchema):
    """Schema for sales invoice response."""

    id: UUID
    invoice_number: str
    invoice_date: date
    due_date: date
    customer_id: UUID
    organization_id: UUID
    unit_id: UUID | None
    subtotal: Decimal
    discount_amount: Decimal
    taxable_amount: Decimal
    cgst_amount: Decimal
    sgst_amount: Decimal
    igst_amount: Decimal
    cess_amount: Decimal
    tcs_amount: Decimal
    round_off: Decimal
    total_amount: Decimal
    balance_amount: Decimal
    is_reverse_charge: bool
    supply_type: str | None
    customer_gstin: str | None
    place_of_supply: str | None
    e_invoice_required: bool
    irn: str | None
    irn_date: datetime | None
    ack_number: str | None
    ack_date: datetime | None
    e_invoice_status: str | None
    status: str
    receipt_status: str
    voucher_id: UUID | None
    is_posted: bool
    narration: str | None
    reference_number: str | None
    po_number: str | None
    po_date: date | None
    shipping_address: str | None
    transporter_name: str | None
    vehicle_number: str | None
    eway_bill_number: str | None
    eway_bill_date: date | None
    lines: list[SalesInvoiceLineResponse]
    created_at: datetime
    updated_at: datetime | None
    is_active: bool


class SalesInvoiceListResponse(CamelSchema):
    """Schema for sales invoice list response."""

    id: UUID
    invoice_number: str
    invoice_date: date
    due_date: date
    customer_id: UUID
    customer_name: str | None
    total_amount: Decimal
    balance_amount: Decimal
    status: str
    receipt_status: str
    e_invoice_status: str | None
    is_posted: bool
