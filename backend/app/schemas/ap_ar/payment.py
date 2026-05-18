"""Payment Entry Schemas."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field, model_validator

from app.models.ap_ar.payment import (
    ChequeStatus,
    DocumentType,
    PartyType,
    PaymentMode,
    PaymentStatus,
    PaymentType,
)
from app.schemas.base import CamelSchema

# ============ Payment Allocation Schemas ============


class PaymentAllocationBase(CamelSchema):
    """Base schema for payment allocation."""

    document_type: DocumentType
    document_id: UUID
    document_number: str = Field(..., max_length=50)
    document_date: date
    document_amount: Decimal = Field(..., ge=0)
    outstanding_before: Decimal = Field(..., ge=0)
    allocated_amount: Decimal = Field(..., gt=0)
    allocation_date: date


class PaymentAllocationCreate(CamelSchema):
    """Schema for creating payment allocation."""

    document_type: DocumentType
    document_id: UUID
    allocated_amount: Decimal = Field(..., gt=0)


class PaymentAllocationResponse(PaymentAllocationBase):
    """Response schema for payment allocation."""

    id: UUID


# ============ Payment Schemas ============


class PaymentBase(CamelSchema):
    """Base schema for payment."""

    payment_date: date
    payment_type: PaymentType
    party_type: PartyType
    vendor_id: UUID | None = None
    customer_id: UUID | None = None
    unit_id: UUID | None = None

    payment_mode: PaymentMode
    bank_account_id: UUID | None = None
    cash_account_id: UUID | None = None

    amount: Decimal = Field(..., gt=0)
    tds_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    tds_section_id: UUID | None = None
    tds_rate: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    discount_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    write_off_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    currency_code: str = Field(default="INR", max_length=3)
    exchange_rate: Decimal = Field(default=Decimal("1.000000"), gt=0)

    # Cheque details
    cheque_number: str | None = Field(None, max_length=20)
    cheque_date: date | None = None
    cheque_bank_name: str | None = Field(None, max_length=100)
    cheque_branch: str | None = Field(None, max_length=100)

    reference_number: str | None = Field(None, max_length=100)
    narration: str | None = None

    @model_validator(mode="after")
    def validate_party(self) -> "PaymentBase":
        """Validate party type and ID consistency."""
        if self.party_type == PartyType.VENDOR:
            if not self.vendor_id:
                raise ValueError("vendor_id is required for vendor payment")
            if self.customer_id:
                raise ValueError("customer_id must be null for vendor payment")
        elif self.party_type == PartyType.CUSTOMER:
            if not self.customer_id:
                raise ValueError("customer_id is required for customer receipt")
            if self.vendor_id:
                raise ValueError("vendor_id must be null for customer receipt")
        return self

    @model_validator(mode="after")
    def validate_payment_mode_account(self) -> "PaymentBase":
        """Validate payment mode and account consistency."""
        if self.payment_mode == PaymentMode.CASH:
            if not self.cash_account_id:
                raise ValueError("cash_account_id is required for cash payment")
        else:
            if not self.bank_account_id:
                raise ValueError("bank_account_id is required for non-cash payment")
        return self

    @model_validator(mode="after")
    def validate_cheque_details(self) -> "PaymentBase":
        """Validate cheque details if payment mode is cheque."""
        if self.payment_mode == PaymentMode.CHEQUE:
            if not self.cheque_number:
                raise ValueError("cheque_number is required for cheque payment")
            if not self.cheque_date:
                raise ValueError("cheque_date is required for cheque payment")
        return self


class PaymentCreate(PaymentBase):
    """Schema for creating payment."""

    organization_id: UUID
    allocations: list[PaymentAllocationCreate] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_allocations(self) -> "PaymentCreate":
        """Validate allocation amounts."""
        total_allocated = sum(a.allocated_amount for a in self.allocations)
        net_amount = self.amount - self.tds_amount - self.discount_amount - self.write_off_amount
        if total_allocated > net_amount:
            raise ValueError(
                f"Total allocated ({total_allocated}) exceeds net amount ({net_amount})"
            )
        return self


class PaymentUpdate(CamelSchema):
    """Schema for updating payment (only draft payments)."""

    payment_date: date | None = None
    payment_type: PaymentType | None = None
    party_type: PartyType | None = None
    vendor_id: UUID | None = None
    customer_id: UUID | None = None
    unit_id: UUID | None = None

    payment_mode: PaymentMode | None = None
    bank_account_id: UUID | None = None
    cash_account_id: UUID | None = None

    amount: Decimal | None = Field(None, gt=0)
    tds_amount: Decimal | None = Field(None, ge=0)
    tds_section_id: UUID | None = None
    tds_rate: Decimal | None = Field(None, ge=0, le=100)
    discount_amount: Decimal | None = Field(None, ge=0)
    write_off_amount: Decimal | None = Field(None, ge=0)

    cheque_number: str | None = Field(None, max_length=20)
    cheque_date: date | None = None
    cheque_bank_name: str | None = Field(None, max_length=100)
    cheque_branch: str | None = Field(None, max_length=100)

    reference_number: str | None = Field(None, max_length=100)
    narration: str | None = None

    allocations: list[PaymentAllocationCreate] | None = None


class ChequeStatusUpdate(CamelSchema):
    """Schema for updating cheque status."""

    cheque_status: ChequeStatus
    cleared_date: date | None = None
    bounced_date: date | None = None
    bounced_reason: str | None = Field(None, max_length=200)

    @model_validator(mode="after")
    def validate_status_fields(self) -> "ChequeStatusUpdate":
        """Validate status-specific fields."""
        if self.cheque_status == ChequeStatus.CLEARED and not self.cleared_date:
            raise ValueError("cleared_date is required when marking cheque as cleared")
        if self.cheque_status == ChequeStatus.BOUNCED:
            if not self.bounced_date:
                raise ValueError("bounced_date is required when marking cheque as bounced")
            if not self.bounced_reason:
                raise ValueError("bounced_reason is required when marking cheque as bounced")
        return self


class PaymentResponse(CamelSchema):
    """Response schema for payment."""

    id: UUID
    payment_number: str
    payment_date: date
    payment_type: PaymentType
    party_type: PartyType
    vendor_id: UUID | None
    customer_id: UUID | None
    organization_id: UUID
    unit_id: UUID | None

    payment_mode: PaymentMode
    bank_account_id: UUID | None
    cash_account_id: UUID | None

    amount: Decimal
    tds_amount: Decimal
    tds_section_id: UUID | None
    tds_rate: Decimal
    discount_amount: Decimal
    write_off_amount: Decimal
    net_amount: Decimal
    currency_code: str
    exchange_rate: Decimal

    cheque_number: str | None
    cheque_date: date | None
    cheque_bank_name: str | None
    cheque_branch: str | None
    cheque_status: ChequeStatus | None
    cheque_cleared_date: date | None
    cheque_bounced_date: date | None
    cheque_bounced_reason: str | None

    reference_number: str | None
    narration: str | None

    status: PaymentStatus
    submitted_at: datetime | None
    approved_at: datetime | None
    cancelled_at: datetime | None
    cancellation_reason: str | None

    voucher_id: UUID | None
    is_posted: bool
    posted_at: datetime | None

    # Computed
    allocated_amount: Decimal
    unallocated_amount: Decimal

    # Related names
    vendor_name: str | None = None
    customer_name: str | None = None
    bank_account_name: str | None = None
    cash_account_name: str | None = None
    tds_section_code: str | None = None

    created_at: datetime
    updated_at: datetime | None


class PaymentDetailResponse(PaymentResponse):
    """Detailed response schema with allocations."""

    allocations: list[PaymentAllocationResponse] = Field(default_factory=list)


class PaymentListResponse(CamelSchema):
    """Response schema for payment list."""

    id: UUID
    payment_number: str
    payment_date: date
    payment_type: PaymentType
    party_type: PartyType
    party_name: str | None
    payment_mode: PaymentMode
    amount: Decimal
    net_amount: Decimal
    status: PaymentStatus
    cheque_status: ChequeStatus | None
    is_posted: bool
    created_at: datetime


class PendingChequeResponse(CamelSchema):
    """Response schema for pending cheques."""

    id: UUID
    payment_number: str
    payment_date: date
    party_type: PartyType
    party_name: str | None
    cheque_number: str
    cheque_date: date
    cheque_bank_name: str | None
    amount: Decimal
    cheque_status: ChequeStatus
    days_pending: int


class OutstandingDocumentResponse(CamelSchema):
    """Response schema for outstanding documents for allocation."""

    document_type: DocumentType
    document_id: UUID
    document_number: str
    document_date: date
    due_date: date | None
    total_amount: Decimal
    paid_amount: Decimal
    outstanding_amount: Decimal
    days_overdue: int
