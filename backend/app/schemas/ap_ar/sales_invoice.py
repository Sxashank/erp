"""Sales Invoice schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SalesInvoiceLineBase(BaseModel):
    """Base schema for sales invoice line."""

    line_number: int = Field(..., ge=1)
    description: str = Field(..., min_length=1, max_length=500)
    hsn_sac_code: Optional[str] = Field(None, max_length=20)
    quantity: Decimal = Field(default=Decimal("1"), ge=0)
    unit_price: Decimal = Field(default=Decimal("0"), ge=0)
    discount_percent: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    discount_amount: Decimal = Field(default=Decimal("0"), ge=0)
    taxable_amount: Decimal = Field(default=Decimal("0"), ge=0)
    gst_rate_id: Optional[UUID] = None
    cgst_rate: Decimal = Field(default=Decimal("0"), ge=0)
    cgst_amount: Decimal = Field(default=Decimal("0"), ge=0)
    sgst_rate: Decimal = Field(default=Decimal("0"), ge=0)
    sgst_amount: Decimal = Field(default=Decimal("0"), ge=0)
    igst_rate: Decimal = Field(default=Decimal("0"), ge=0)
    igst_amount: Decimal = Field(default=Decimal("0"), ge=0)
    cess_rate: Decimal = Field(default=Decimal("0"), ge=0)
    cess_amount: Decimal = Field(default=Decimal("0"), ge=0)
    total_amount: Decimal = Field(default=Decimal("0"), ge=0)
    revenue_account_id: Optional[UUID] = None


class SalesInvoiceLineCreate(SalesInvoiceLineBase):
    """Schema for creating a sales invoice line."""

    pass


class SalesInvoiceLineResponse(SalesInvoiceLineBase):
    """Schema for sales invoice line response."""

    id: UUID
    invoice_id: UUID

    class Config:
        from_attributes = True


class SalesInvoiceBase(BaseModel):
    """Base schema for sales invoice."""

    invoice_date: date
    due_date: date
    customer_id: UUID
    organization_id: UUID
    unit_id: Optional[UUID] = None
    place_of_supply: Optional[str] = Field(None, max_length=2)
    supply_type: Optional[str] = None
    is_reverse_charge: bool = False
    tcs_amount: Decimal = Field(default=Decimal("0"), ge=0)
    round_off: Decimal = Field(default=Decimal("0"))
    narration: Optional[str] = None
    reference_number: Optional[str] = Field(None, max_length=100)
    po_number: Optional[str] = Field(None, max_length=100)
    po_date: Optional[date] = None
    shipping_address: Optional[str] = None
    transporter_name: Optional[str] = Field(None, max_length=200)
    vehicle_number: Optional[str] = Field(None, max_length=20)


class SalesInvoiceCreate(SalesInvoiceBase):
    """Schema for creating a sales invoice."""

    lines: List[SalesInvoiceLineCreate] = Field(..., min_length=1)


class SalesInvoiceUpdate(BaseModel):
    """Schema for updating a sales invoice."""

    invoice_date: Optional[date] = None
    due_date: Optional[date] = None
    unit_id: Optional[UUID] = None
    place_of_supply: Optional[str] = Field(None, max_length=2)
    supply_type: Optional[str] = None
    is_reverse_charge: Optional[bool] = None
    tcs_amount: Optional[Decimal] = None
    round_off: Optional[Decimal] = None
    narration: Optional[str] = None
    reference_number: Optional[str] = Field(None, max_length=100)
    po_number: Optional[str] = Field(None, max_length=100)
    po_date: Optional[date] = None
    shipping_address: Optional[str] = None
    transporter_name: Optional[str] = Field(None, max_length=200)
    vehicle_number: Optional[str] = Field(None, max_length=20)
    lines: Optional[List[SalesInvoiceLineCreate]] = None


class SalesInvoiceResponse(BaseModel):
    """Schema for sales invoice response."""

    id: UUID
    invoice_number: str
    invoice_date: date
    due_date: date
    customer_id: UUID
    organization_id: UUID
    unit_id: Optional[UUID]
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
    supply_type: Optional[str]
    customer_gstin: Optional[str]
    place_of_supply: Optional[str]
    e_invoice_required: bool
    irn: Optional[str]
    e_invoice_status: Optional[str]
    status: str
    receipt_status: str
    voucher_id: Optional[UUID]
    is_posted: bool
    narration: Optional[str]
    reference_number: Optional[str]
    po_number: Optional[str]
    po_date: Optional[date]
    shipping_address: Optional[str]
    transporter_name: Optional[str]
    vehicle_number: Optional[str]
    eway_bill_number: Optional[str]
    eway_bill_date: Optional[date]
    lines: List[SalesInvoiceLineResponse]
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool

    class Config:
        from_attributes = True


class SalesInvoiceListResponse(BaseModel):
    """Schema for sales invoice list response."""

    id: UUID
    invoice_number: str
    invoice_date: date
    due_date: date
    customer_id: UUID
    customer_name: Optional[str]
    total_amount: Decimal
    balance_amount: Decimal
    status: str
    receipt_status: str
    e_invoice_status: Optional[str]
    is_posted: bool

    class Config:
        from_attributes = True
