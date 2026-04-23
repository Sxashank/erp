"""Stock Balance and Transaction schemas."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, AuditSchema
from app.models.inventory.stock import TransactionType, TransactionStatus


class StockBalanceResponse(AuditSchema):
    """Stock balance response schema."""

    id: UUID
    organization_id: UUID
    item_id: UUID
    item_code: Optional[str] = None
    item_name: Optional[str] = None
    warehouse_id: UUID
    warehouse_code: Optional[str] = None
    warehouse_name: Optional[str] = None

    quantity_on_hand: Decimal
    quantity_reserved: Decimal
    quantity_in_transit: Decimal
    available_quantity: Decimal

    average_cost: Decimal
    total_value: Decimal

    last_transaction_date: Optional[datetime] = None


class StockTransactionCreate(BaseSchema):
    """Base schema for creating a stock transaction."""

    item_id: UUID
    warehouse_id: UUID
    quantity: Decimal = Field(..., gt=0)
    unit_cost: Decimal = Field(Decimal("0"), ge=0)
    transaction_date: date = Field(default_factory=date.today)

    batch_number: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    expiry_date: Optional[date] = None

    reference_type: Optional[str] = Field(None, max_length=50)
    reference_id: Optional[UUID] = None
    reference_number: Optional[str] = Field(None, max_length=50)

    remarks: Optional[str] = Field(None, max_length=500)
    organization_id: UUID


class StockInCreate(StockTransactionCreate):
    """Schema for stock in transaction."""
    pass


class StockOutCreate(StockTransactionCreate):
    """Schema for stock out transaction."""
    pass


class StockTransferCreate(BaseSchema):
    """Schema for stock transfer between warehouses."""

    item_id: UUID
    from_warehouse_id: UUID
    to_warehouse_id: UUID
    quantity: Decimal = Field(..., gt=0)
    transaction_date: date = Field(default_factory=date.today)

    batch_number: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)

    remarks: Optional[str] = Field(None, max_length=500)
    organization_id: UUID


class StockAdjustmentCreate(BaseSchema):
    """Schema for stock adjustment."""

    item_id: UUID
    warehouse_id: UUID
    adjustment_quantity: Decimal = Field(...)  # Positive or negative
    adjustment_reason: str = Field(..., min_length=1, max_length=500)
    transaction_date: date = Field(default_factory=date.today)

    batch_number: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)

    organization_id: UUID


class StockTransactionUpdate(BaseSchema):
    """Schema for updating a stock transaction (draft only)."""

    quantity: Optional[Decimal] = Field(None, gt=0)
    unit_cost: Optional[Decimal] = Field(None, ge=0)
    transaction_date: Optional[date] = None

    batch_number: Optional[str] = Field(None, max_length=100)
    serial_number: Optional[str] = Field(None, max_length=100)
    expiry_date: Optional[date] = None

    remarks: Optional[str] = Field(None, max_length=500)


class StockTransactionResponse(AuditSchema):
    """Stock transaction response schema."""

    id: UUID
    organization_id: UUID
    transaction_number: str
    transaction_type: TransactionType
    transaction_date: date
    status: TransactionStatus

    item_id: UUID
    item_code: Optional[str] = None
    item_name: Optional[str] = None

    warehouse_id: UUID
    warehouse_code: Optional[str] = None
    warehouse_name: Optional[str] = None

    to_warehouse_id: Optional[UUID] = None
    to_warehouse_code: Optional[str] = None
    to_warehouse_name: Optional[str] = None

    quantity: Decimal
    unit_cost: Decimal
    total_cost: Decimal

    balance_before: Decimal
    balance_after: Decimal

    batch_number: Optional[str] = None
    serial_number: Optional[str] = None
    expiry_date: Optional[date] = None

    reference_type: Optional[str] = None
    reference_id: Optional[UUID] = None
    reference_number: Optional[str] = None

    remarks: Optional[str] = None

    approved_by: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
