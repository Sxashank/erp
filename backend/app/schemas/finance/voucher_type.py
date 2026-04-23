"""Voucher Type schemas."""

from typing import Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, AuditSchema
from app.core.constants import VoucherClass


class VoucherTypeCreate(BaseSchema):
    """Schema for creating a voucher type."""

    code: str = Field(..., min_length=1, max_length=20, description="Voucher type code")
    name: str = Field(..., min_length=1, max_length=100, description="Display name")
    voucher_class: VoucherClass
    prefix: str = Field(..., min_length=1, max_length=20, description="Number prefix")
    auto_numbering: bool = True
    starting_number: int = 1
    number_format: Optional[str] = Field(None, max_length=50)
    requires_approval: bool = False
    approval_levels: int = 1
    default_narration: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=500)
    organization_id: UUID


class VoucherTypeUpdate(BaseSchema):
    """Schema for updating a voucher type."""

    code: Optional[str] = Field(None, min_length=1, max_length=20)
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    prefix: Optional[str] = Field(None, min_length=1, max_length=20)
    auto_numbering: Optional[bool] = None
    number_format: Optional[str] = Field(None, max_length=50)
    requires_approval: Optional[bool] = None
    approval_levels: Optional[int] = None
    default_narration: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=500)


class VoucherTypeResponse(AuditSchema):
    """Voucher Type response schema."""

    id: UUID
    code: str
    name: str
    voucher_class: VoucherClass
    prefix: str
    auto_numbering: bool
    starting_number: int
    current_number: int
    number_format: Optional[str] = None
    requires_approval: bool
    approval_levels: int
    default_narration: Optional[str] = None
    description: Optional[str] = None
    is_system: bool
    organization_id: UUID
