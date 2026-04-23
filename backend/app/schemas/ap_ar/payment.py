"""Payment Entry Schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.ap_ar.payment import (
    PaymentType,
    PartyType,
    PaymentMode,
    PaymentStatus,
    ChequeStatus,
    DocumentType,
)


# ============ Payment Allocation Schemas ============


class PaymentAllocationBase(BaseModel):
    """Base schema for payment allocation."""

    document_type: DocumentType
    document_id: UUID
    document_number: str = Field(..., max_length=50)
    document_date: date
    document_amount: Decimal = Field(..., ge=0)
    outstanding_before: Decimal = Field(..., ge=0)
    allocated_amount: Decimal = Field(..., gt=0)
    allocation_date: date


class PaymentAllocationCreate(BaseModel):
    """Schema for creating payment allocation."""

    document_type: DocumentType
    document_id: UUID
    allocated_amount: Decimal = Field(..., gt=0)


class PaymentAllocationResponse(PaymentAllocationBase):
    """Response schema for payment allocation."""

    id: UUID

    class Config:
        from_attributes = True


# ============ Payment Schemas ============


class PaymentBase(BaseModel):
    """Base schema for payment."""

    payment_date: date
    payment_type: PaymentType
    party_type: PartyType
    vendor_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None

    payment_mode: PaymentMode
    bank_account_id: Optional[UUID] = None
    cash_account_id: Optional[UUID] = None

    amount: Decimal = Field(..., gt=0)
    tds_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    tds_section_id: Optional[UUID] = None
    tds_rate: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    discount_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    write_off_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    currency_code: str = Field(default="INR", max_length=3)
    exchange_rate: Decimal = Field(default=Decimal("1.000000"), gt=0)

    # Cheque details
    cheque_number: Optional[str] = Field(None, max_length=20)
    cheque_date: Optional[date] = None
    cheque_bank_name: Optional[str] = Field(None, max_length=100)
    cheque_branch: Optional[str] = Field(None, max_length=100)

    reference_number: Optional[str] = Field(None, max_length=100)
    narration: Optional[str] = None

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


class PaymentUpdate(BaseModel):
    """Schema for updating payment (only draft payments)."""

    payment_date: Optional[date] = None
    payment_type: Optional[PaymentType] = None
    party_type: Optional[PartyType] = None
    vendor_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None

    payment_mode: Optional[PaymentMode] = None
    bank_account_id: Optional[UUID] = None
    cash_account_id: Optional[UUID] = None

    amount: Optional[Decimal] = Field(None, gt=0)
    tds_amount: Optional[Decimal] = Field(None, ge=0)
    tds_section_id: Optional[UUID] = None
    tds_rate: Optional[Decimal] = Field(None, ge=0, le=100)
    discount_amount: Optional[Decimal] = Field(None, ge=0)
    write_off_amount: Optional[Decimal] = Field(None, ge=0)

    cheque_number: Optional[str] = Field(None, max_length=20)
    cheque_date: Optional[date] = None
    cheque_bank_name: Optional[str] = Field(None, max_length=100)
    cheque_branch: Optional[str] = Field(None, max_length=100)

    reference_number: Optional[str] = Field(None, max_length=100)
    narration: Optional[str] = None

    allocations: Optional[list[PaymentAllocationCreate]] = None


class ChequeStatusUpdate(BaseModel):
    """Schema for updating cheque status."""

    cheque_status: ChequeStatus
    cleared_date: Optional[date] = None
    bounced_date: Optional[date] = None
    bounced_reason: Optional[str] = Field(None, max_length=200)

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


class PaymentResponse(BaseModel):
    """Response schema for payment."""

    id: UUID
    payment_number: str
    payment_date: date
    payment_type: PaymentType
    party_type: PartyType
    vendor_id: Optional[UUID]
    customer_id: Optional[UUID]
    organization_id: UUID
    unit_id: Optional[UUID]

    payment_mode: PaymentMode
    bank_account_id: Optional[UUID]
    cash_account_id: Optional[UUID]

    amount: Decimal
    tds_amount: Decimal
    tds_section_id: Optional[UUID]
    tds_rate: Decimal
    discount_amount: Decimal
    write_off_amount: Decimal
    net_amount: Decimal
    currency_code: str
    exchange_rate: Decimal

    cheque_number: Optional[str]
    cheque_date: Optional[date]
    cheque_bank_name: Optional[str]
    cheque_branch: Optional[str]
    cheque_status: Optional[ChequeStatus]
    cheque_cleared_date: Optional[date]
    cheque_bounced_date: Optional[date]
    cheque_bounced_reason: Optional[str]

    reference_number: Optional[str]
    narration: Optional[str]

    status: PaymentStatus
    submitted_at: Optional[datetime]
    approved_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    cancellation_reason: Optional[str]

    voucher_id: Optional[UUID]
    is_posted: bool
    posted_at: Optional[datetime]

    # Computed
    allocated_amount: Decimal
    unallocated_amount: Decimal

    # Related names
    vendor_name: Optional[str] = None
    customer_name: Optional[str] = None
    bank_account_name: Optional[str] = None
    cash_account_name: Optional[str] = None
    tds_section_code: Optional[str] = None

    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class PaymentDetailResponse(PaymentResponse):
    """Detailed response schema with allocations."""

    allocations: list[PaymentAllocationResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


class PaymentListResponse(BaseModel):
    """Response schema for payment list."""

    id: UUID
    payment_number: str
    payment_date: date
    payment_type: PaymentType
    party_type: PartyType
    party_name: Optional[str]
    payment_mode: PaymentMode
    amount: Decimal
    net_amount: Decimal
    status: PaymentStatus
    cheque_status: Optional[ChequeStatus]
    is_posted: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PendingChequeResponse(BaseModel):
    """Response schema for pending cheques."""

    id: UUID
    payment_number: str
    payment_date: date
    party_type: PartyType
    party_name: Optional[str]
    cheque_number: str
    cheque_date: date
    cheque_bank_name: Optional[str]
    amount: Decimal
    cheque_status: ChequeStatus
    days_pending: int

    class Config:
        from_attributes = True


class OutstandingDocumentResponse(BaseModel):
    """Response schema for outstanding documents for allocation."""

    document_type: DocumentType
    document_id: UUID
    document_number: str
    document_date: date
    due_date: Optional[date]
    total_amount: Decimal
    paid_amount: Decimal
    outstanding_amount: Decimal
    days_overdue: int

    class Config:
        from_attributes = True
