"""Voucher schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from app.schemas.base import BaseSchema, AuditSchema
from app.core.constants import VoucherStatus, PartyType, VoucherClass


class VoucherLineCreate(BaseSchema):
    """Schema for creating a voucher line."""

    account_id: UUID
    debit_amount: Decimal = Decimal("0.00")
    credit_amount: Decimal = Decimal("0.00")
    narration: Optional[str] = Field(None, max_length=500)
    cost_center_id: Optional[UUID] = None
    party_type: Optional[PartyType] = None
    party_id: Optional[UUID] = None
    reference_type: Optional[str] = Field(None, max_length=50)
    reference_id: Optional[UUID] = None
    reference_number: Optional[str] = Field(None, max_length=100)
    cheque_number: Optional[str] = Field(None, max_length=50)
    cheque_date: Optional[date] = None

    @model_validator(mode="after")
    def validate_amounts(self):
        """Ensure only debit or credit is set, not both."""
        if self.debit_amount > 0 and self.credit_amount > 0:
            raise ValueError("Cannot have both debit and credit amounts on the same line")
        if self.debit_amount <= 0 and self.credit_amount <= 0:
            raise ValueError("Either debit or credit amount must be greater than zero")
        return self


class VoucherLineResponse(BaseSchema):
    """Voucher Line response schema."""

    id: UUID
    line_number: int
    account_id: UUID
    account_code: Optional[str] = None
    account_name: Optional[str] = None
    debit_amount: Decimal
    credit_amount: Decimal
    narration: Optional[str] = None
    cost_center_id: Optional[UUID] = None
    party_type: Optional[PartyType] = None
    party_id: Optional[UUID] = None
    reference_type: Optional[str] = None
    reference_id: Optional[UUID] = None
    reference_number: Optional[str] = None
    cheque_number: Optional[str] = None
    cheque_date: Optional[date] = None


class VoucherCreate(BaseSchema):
    """Schema for creating a voucher."""

    voucher_type_id: UUID
    voucher_date: date
    reference_number: Optional[str] = Field(None, max_length=100)
    reference_date: Optional[date] = None
    narration: Optional[str] = None
    unit_id: Optional[UUID] = None
    lines: List[VoucherLineCreate]
    organization_id: Optional[UUID] = None

    @field_validator("lines")
    @classmethod
    def validate_lines(cls, v: List[VoucherLineCreate]) -> List[VoucherLineCreate]:
        """Ensure at least 2 lines and balanced amounts."""
        if len(v) < 2:
            raise ValueError("Voucher must have at least 2 lines")

        total_debit = sum(line.debit_amount for line in v)
        total_credit = sum(line.credit_amount for line in v)

        if total_debit != total_credit:
            raise ValueError(f"Voucher is not balanced. Debit: {total_debit}, Credit: {total_credit}")

        return v


class VoucherUpdate(BaseSchema):
    """Schema for updating a voucher (only draft vouchers)."""

    voucher_date: Optional[date] = None
    reference_number: Optional[str] = Field(None, max_length=100)
    reference_date: Optional[date] = None
    narration: Optional[str] = None
    unit_id: Optional[UUID] = None
    lines: Optional[List[VoucherLineCreate]] = None

    @field_validator("lines")
    @classmethod
    def validate_lines(cls, v: Optional[List[VoucherLineCreate]]) -> Optional[List[VoucherLineCreate]]:
        """Ensure at least 2 lines and balanced amounts if provided."""
        if v is None:
            return v

        if len(v) < 2:
            raise ValueError("Voucher must have at least 2 lines")

        total_debit = sum(line.debit_amount for line in v)
        total_credit = sum(line.credit_amount for line in v)

        if total_debit != total_credit:
            raise ValueError(f"Voucher is not balanced. Debit: {total_debit}, Credit: {total_credit}")

        return v


class VoucherResponse(AuditSchema):
    """Voucher response schema (list view)."""

    id: UUID
    voucher_type_id: UUID
    voucher_type_code: Optional[str] = None
    voucher_type_name: Optional[str] = None
    voucher_class: Optional[VoucherClass] = None
    voucher_number: str
    voucher_date: date
    financial_year_id: UUID
    financial_year_code: Optional[str] = None
    period_id: UUID
    reference_number: Optional[str] = None
    narration: Optional[str] = None
    total_debit: Decimal
    total_credit: Decimal
    status: VoucherStatus
    organization_id: UUID
    unit_id: Optional[UUID] = None
    unit_name: Optional[str] = None


class VoucherDetailResponse(VoucherResponse):
    """Voucher detail response with lines."""

    reference_date: Optional[date] = None
    approval_status: Optional[List[dict]] = None
    current_approval_level: int = 0
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    posted_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    rejection_reason: Optional[str] = None
    is_reversed: bool = False
    reversal_voucher_id: Optional[UUID] = None
    original_voucher_id: Optional[UUID] = None
    lines: List[VoucherLineResponse] = []


class VoucherApprovalRequest(BaseSchema):
    """Request to approve a voucher."""

    remarks: Optional[str] = Field(None, max_length=500)


class VoucherRejectRequest(BaseSchema):
    """Request to reject a voucher."""

    reason: str = Field(..., min_length=1, max_length=500)


class VoucherCancelRequest(BaseSchema):
    """Request to cancel a voucher."""

    reason: str = Field(..., min_length=1, max_length=500)
