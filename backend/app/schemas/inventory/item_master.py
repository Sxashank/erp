"""Item Master schemas."""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, AuditSchema
from app.models.inventory.item_master import UnitOfMeasure, ItemType


class ItemMasterCreate(BaseSchema):
    """Schema for creating an item master."""

    category_id: UUID
    item_code: str = Field(..., min_length=1, max_length=50)
    item_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    item_type: ItemType = ItemType.STOCK
    uom: UnitOfMeasure = UnitOfMeasure.EACH

    brand: Optional[str] = Field(None, max_length=100)
    model_number: Optional[str] = Field(None, max_length=100)
    sku: Optional[str] = Field(None, max_length=100)
    barcode: Optional[str] = Field(None, max_length=100)

    is_stockable: bool = True
    requires_serial_number: bool = False
    requires_batch_number: bool = False
    shelf_life_days: Optional[int] = Field(None, ge=0)

    minimum_stock_level: Decimal = Field(Decimal("0"), ge=0)
    maximum_stock_level: Decimal = Field(Decimal("0"), ge=0)
    reorder_quantity: Decimal = Field(Decimal("0"), ge=0)

    standard_cost: Decimal = Field(Decimal("0"), ge=0)
    selling_price: Decimal = Field(Decimal("0"), ge=0)

    hsn_code: Optional[str] = Field(None, max_length=20)
    gst_rate: Decimal = Field(Decimal("0"), ge=0, le=100)

    gl_inventory_account_id: Optional[UUID] = None
    gl_expense_account_id: Optional[UUID] = None

    organization_id: UUID


class ItemMasterUpdate(BaseSchema):
    """Schema for updating an item master."""

    category_id: Optional[UUID] = None
    item_code: Optional[str] = Field(None, min_length=1, max_length=50)
    item_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    item_type: Optional[ItemType] = None
    uom: Optional[UnitOfMeasure] = None

    brand: Optional[str] = Field(None, max_length=100)
    model_number: Optional[str] = Field(None, max_length=100)
    sku: Optional[str] = Field(None, max_length=100)
    barcode: Optional[str] = Field(None, max_length=100)

    is_stockable: Optional[bool] = None
    requires_serial_number: Optional[bool] = None
    requires_batch_number: Optional[bool] = None
    shelf_life_days: Optional[int] = Field(None, ge=0)

    minimum_stock_level: Optional[Decimal] = Field(None, ge=0)
    maximum_stock_level: Optional[Decimal] = Field(None, ge=0)
    reorder_quantity: Optional[Decimal] = Field(None, ge=0)

    standard_cost: Optional[Decimal] = Field(None, ge=0)
    selling_price: Optional[Decimal] = Field(None, ge=0)

    hsn_code: Optional[str] = Field(None, max_length=20)
    gst_rate: Optional[Decimal] = Field(None, ge=0, le=100)

    gl_inventory_account_id: Optional[UUID] = None
    gl_expense_account_id: Optional[UUID] = None


class ItemMasterResponse(AuditSchema):
    """Item master response schema."""

    id: UUID
    organization_id: UUID
    category_id: UUID
    category_name: Optional[str] = None

    item_code: str
    item_name: str
    description: Optional[str] = None
    item_type: ItemType
    uom: UnitOfMeasure

    brand: Optional[str] = None
    model_number: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None

    is_stockable: bool
    requires_serial_number: bool
    requires_batch_number: bool
    shelf_life_days: Optional[int] = None

    minimum_stock_level: Decimal
    maximum_stock_level: Decimal
    reorder_quantity: Decimal

    standard_cost: Decimal
    selling_price: Decimal

    hsn_code: Optional[str] = None
    gst_rate: Decimal

    gl_inventory_account_id: Optional[UUID] = None
    gl_expense_account_id: Optional[UUID] = None

    # Computed fields
    current_stock: Decimal = Decimal("0")
    stock_value: Decimal = Decimal("0")
