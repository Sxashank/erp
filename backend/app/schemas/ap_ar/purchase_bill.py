"""Purchase Bill schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PurchaseBillLineBase(BaseModel):
    """Base schema for purchase bill line."""
    line_number: int = Field(..., ge=1)
    description: str = Field(..., max_length=500)
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
    expense_account_id: Optional[UUID] = None


class PurchaseBillLineCreate(PurchaseBillLineBase):
    """Schema for creating a purchase bill line."""
    pass


class PurchaseBillLineResponse(PurchaseBillLineBase):
    """Schema for purchase bill line response."""
    id: UUID
    bill_id: UUID

    class Config:
        from_attributes = True


class PurchaseBillBase(BaseModel):
    """Base schema for purchase bill."""
    vendor_invoice_number: Optional[str] = Field(None, max_length=100)
    vendor_invoice_date: Optional[date] = None
    bill_date: date
    due_date: Optional[date] = None
    vendor_id: UUID
    organization_id: UUID
    unit_id: Optional[UUID] = None

    # Amounts (computed from lines)
    subtotal: Decimal = Field(default=Decimal("0"))
    discount_amount: Decimal = Field(default=Decimal("0"))
    taxable_amount: Decimal = Field(default=Decimal("0"))
    cgst_amount: Decimal = Field(default=Decimal("0"))
    sgst_amount: Decimal = Field(default=Decimal("0"))
    igst_amount: Decimal = Field(default=Decimal("0"))
    cess_amount: Decimal = Field(default=Decimal("0"))
    tds_amount: Decimal = Field(default=Decimal("0"))
    round_off: Decimal = Field(default=Decimal("0"))
    total_amount: Decimal = Field(default=Decimal("0"))

    # GST
    is_reverse_charge: bool = False
    supply_type: Optional[str] = None
    vendor_gstin: Optional[str] = Field(None, max_length=15)
    place_of_supply: Optional[str] = Field(None, max_length=2)

    # Notes
    narration: Optional[str] = None
    reference_number: Optional[str] = Field(None, max_length=100)


class PurchaseBillCreate(PurchaseBillBase):
    """Schema for creating a purchase bill."""
    lines: List[PurchaseBillLineCreate] = Field(..., min_length=1)


class PurchaseBillUpdate(BaseModel):
    """Schema for updating a purchase bill."""
    vendor_invoice_number: Optional[str] = Field(None, max_length=100)
    vendor_invoice_date: Optional[date] = None
    bill_date: Optional[date] = None
    due_date: Optional[date] = None
    unit_id: Optional[UUID] = None

    # Amounts
    subtotal: Optional[Decimal] = None
    discount_amount: Optional[Decimal] = None
    taxable_amount: Optional[Decimal] = None
    cgst_amount: Optional[Decimal] = None
    sgst_amount: Optional[Decimal] = None
    igst_amount: Optional[Decimal] = None
    cess_amount: Optional[Decimal] = None
    tds_amount: Optional[Decimal] = None
    round_off: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None

    # GST
    is_reverse_charge: Optional[bool] = None
    supply_type: Optional[str] = None
    place_of_supply: Optional[str] = Field(None, max_length=2)

    # Notes
    narration: Optional[str] = None
    reference_number: Optional[str] = Field(None, max_length=100)

    # Lines
    lines: Optional[List[PurchaseBillLineCreate]] = None


class PurchaseBillResponse(BaseModel):
    """Schema for purchase bill response."""
    id: UUID
    bill_number: str
    vendor_invoice_number: Optional[str]
    vendor_invoice_date: Optional[date]
    bill_date: date
    due_date: Optional[date]
    vendor_id: UUID
    organization_id: UUID
    unit_id: Optional[UUID]

    # Amounts
    subtotal: Decimal
    discount_amount: Decimal
    taxable_amount: Decimal
    cgst_amount: Decimal
    sgst_amount: Decimal
    igst_amount: Decimal
    cess_amount: Decimal
    tds_amount: Decimal
    round_off: Decimal
    total_amount: Decimal
    balance_amount: Decimal

    # GST
    is_reverse_charge: bool
    supply_type: Optional[str]
    vendor_gstin: Optional[str]
    place_of_supply: Optional[str]

    # Status
    status: str
    payment_status: str

    # GL
    voucher_id: Optional[UUID]
    is_posted: bool

    # Notes
    narration: Optional[str]
    reference_number: Optional[str]

    # Lines
    lines: List[PurchaseBillLineResponse]

    # Audit
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool

    class Config:
        from_attributes = True


class PurchaseBillListResponse(BaseModel):
    """Schema for purchase bill list response."""
    id: UUID
    bill_number: str
    vendor_invoice_number: Optional[str]
    bill_date: date
    due_date: Optional[date]
    vendor_id: UUID
    vendor_name: Optional[str] = None
    total_amount: Decimal
    balance_amount: Decimal
    status: str
    payment_status: str
    is_posted: bool

    class Config:
        from_attributes = True
