"""Warehouse schemas."""

from typing import Optional
from uuid import UUID

from pydantic import Field, EmailStr

from app.schemas.base import BaseSchema, AuditSchema
from app.models.inventory.warehouse import WarehouseType


class WarehouseCreate(BaseSchema):
    """Schema for creating a warehouse."""

    warehouse_code: str = Field(..., min_length=1, max_length=20)
    warehouse_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    warehouse_type: WarehouseType = WarehouseType.MAIN
    unit_id: Optional[UUID] = None

    address_line1: Optional[str] = Field(None, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, max_length=10)

    contact_person: Optional[str] = Field(None, max_length=100)
    contact_phone: Optional[str] = Field(None, max_length=20)
    contact_email: Optional[str] = Field(None, max_length=100)

    is_default: bool = False
    allow_negative_stock: bool = False

    organization_id: UUID


class WarehouseUpdate(BaseSchema):
    """Schema for updating a warehouse."""

    warehouse_code: Optional[str] = Field(None, min_length=1, max_length=20)
    warehouse_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    warehouse_type: Optional[WarehouseType] = None
    unit_id: Optional[UUID] = None

    address_line1: Optional[str] = Field(None, max_length=200)
    address_line2: Optional[str] = Field(None, max_length=200)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    pincode: Optional[str] = Field(None, max_length=10)

    contact_person: Optional[str] = Field(None, max_length=100)
    contact_phone: Optional[str] = Field(None, max_length=20)
    contact_email: Optional[str] = Field(None, max_length=100)

    is_default: Optional[bool] = None
    allow_negative_stock: Optional[bool] = None


class WarehouseResponse(AuditSchema):
    """Warehouse response schema."""

    id: UUID
    organization_id: UUID
    unit_id: Optional[UUID] = None
    unit_name: Optional[str] = None

    warehouse_code: str
    warehouse_name: str
    description: Optional[str] = None
    warehouse_type: WarehouseType

    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None

    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None

    is_default: bool
    allow_negative_stock: bool

    # Computed fields
    total_items: int = 0
    total_value: float = 0.0
