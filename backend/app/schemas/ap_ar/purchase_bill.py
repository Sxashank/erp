"""Purchase Bill schemas."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from app.schemas.base import CamelSchema


class PurchaseBillLineBase(CamelSchema):
    """Base schema for purchase bill line."""
    line_number: int = Field(..., ge=1)
    description: str = Field(..., max_length=500)
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
    expense_account_id: UUID | None = None


class PurchaseBillLineCreate(PurchaseBillLineBase):
    """Schema for creating a purchase bill line."""
    pass


class PurchaseBillLineResponse(PurchaseBillLineBase):
    """Schema for purchase bill line response."""
    id: UUID
    bill_id: UUID


class PurchaseBillBase(CamelSchema):
    """Base schema for purchase bill."""
    vendor_invoice_number: str | None = Field(None, max_length=100)
    vendor_invoice_date: date | None = None
    bill_date: date
    due_date: date | None = None
    vendor_id: UUID
    organization_id: UUID
    unit_id: UUID | None = None

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
    supply_type: str | None = None
    vendor_gstin: str | None = Field(None, max_length=15)
    place_of_supply: str | None = Field(None, max_length=2)

    # Notes
    narration: str | None = None
    reference_number: str | None = Field(None, max_length=100)


class PurchaseBillCreate(PurchaseBillBase):
    """Schema for creating a purchase bill."""
    lines: list[PurchaseBillLineCreate] = Field(..., min_length=1)


class PurchaseBillUpdate(CamelSchema):
    """Schema for updating a purchase bill."""
    vendor_invoice_number: str | None = Field(None, max_length=100)
    vendor_invoice_date: date | None = None
    bill_date: date | None = None
    due_date: date | None = None
    unit_id: UUID | None = None

    # Amounts
    subtotal: Decimal | None = None
    discount_amount: Decimal | None = None
    taxable_amount: Decimal | None = None
    cgst_amount: Decimal | None = None
    sgst_amount: Decimal | None = None
    igst_amount: Decimal | None = None
    cess_amount: Decimal | None = None
    tds_amount: Decimal | None = None
    round_off: Decimal | None = None
    total_amount: Decimal | None = None

    # GST
    is_reverse_charge: bool | None = None
    supply_type: str | None = None
    place_of_supply: str | None = Field(None, max_length=2)

    # Notes
    narration: str | None = None
    reference_number: str | None = Field(None, max_length=100)

    # Lines
    lines: list[PurchaseBillLineCreate] | None = None


class PurchaseBillResponse(CamelSchema):
    """Schema for purchase bill response."""
    id: UUID
    bill_number: str
    vendor_invoice_number: str | None
    vendor_invoice_date: date | None
    bill_date: date
    due_date: date | None
    vendor_id: UUID
    organization_id: UUID
    unit_id: UUID | None

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
    supply_type: str | None
    vendor_gstin: str | None
    place_of_supply: str | None

    # Status
    status: str
    payment_status: str

    # GL
    voucher_id: UUID | None
    is_posted: bool

    # Notes
    narration: str | None
    reference_number: str | None

    # Lines
    lines: list[PurchaseBillLineResponse]

    # Audit
    created_at: datetime
    updated_at: datetime | None
    is_active: bool


class PurchaseBillListResponse(CamelSchema):
    """Schema for purchase bill list response."""
    id: UUID
    bill_number: str
    vendor_invoice_number: str | None
    bill_date: date
    due_date: date | None
    vendor_id: UUID
    vendor_name: str | None = None
    total_amount: Decimal
    balance_amount: Decimal
    status: str
    payment_status: str
    is_posted: bool
