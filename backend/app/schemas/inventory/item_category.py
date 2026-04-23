"""Item Category schemas."""

from typing import List, Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, AuditSchema


class ItemCategoryCreate(BaseSchema):
    """Schema for creating an item category."""

    category_code: str = Field(..., min_length=1, max_length=20)
    category_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    parent_category_id: Optional[UUID] = None
    is_stockable: bool = True
    requires_serial_number: bool = False
    requires_batch_number: bool = False
    gl_inventory_account_id: Optional[UUID] = None
    gl_expense_account_id: Optional[UUID] = None
    organization_id: UUID


class ItemCategoryUpdate(BaseSchema):
    """Schema for updating an item category."""

    category_code: Optional[str] = Field(None, min_length=1, max_length=20)
    category_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    parent_category_id: Optional[UUID] = None
    is_stockable: Optional[bool] = None
    requires_serial_number: Optional[bool] = None
    requires_batch_number: Optional[bool] = None
    gl_inventory_account_id: Optional[UUID] = None
    gl_expense_account_id: Optional[UUID] = None


class ItemCategoryResponse(AuditSchema):
    """Item category response schema."""

    id: UUID
    organization_id: UUID
    category_code: str
    category_name: str
    description: Optional[str] = None
    parent_category_id: Optional[UUID] = None
    parent_category_name: Optional[str] = None
    is_stockable: bool
    requires_serial_number: bool
    requires_batch_number: bool
    gl_inventory_account_id: Optional[UUID] = None
    gl_inventory_account_name: Optional[str] = None
    gl_expense_account_id: Optional[UUID] = None
    gl_expense_account_name: Optional[str] = None
    item_count: int = 0


class ItemCategoryTreeResponse(BaseSchema):
    """Item category tree node for hierarchical display."""

    id: UUID
    category_code: str
    category_name: str
    is_stockable: bool
    item_count: int = 0
    children: List["ItemCategoryTreeResponse"] = []


# Update forward reference
ItemCategoryTreeResponse.model_rebuild()
