"""Cost Center schemas."""

from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CostCenterBase(BaseModel):
    """Base Cost Center schema."""

    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    cost_type: Optional[str] = Field(None, max_length=20)
    has_budget: bool = False
    annual_budget: Decimal = Decimal("0.00")
    budget_variance_threshold: Decimal = Decimal("10.00")
    is_allocatable: bool = True
    allocation_basis: Optional[str] = Field(None, max_length=50)
    allocation_percentage: Decimal = Decimal("100.00")
    manager_id: Optional[UUID] = None
    manager_name: Optional[str] = Field(None, max_length=200)
    effective_from: date = Field(default_factory=date.today)
    effective_to: Optional[date] = None
    default_expense_account_id: Optional[UUID] = None
    external_code: Optional[str] = Field(None, max_length=50)


class CostCenterCreate(CostCenterBase):
    """Schema for creating Cost Center."""

    organization_id: UUID
    parent_id: Optional[UUID] = None


class CostCenterUpdate(BaseModel):
    """Schema for updating Cost Center."""

    code: Optional[str] = Field(None, max_length=20)
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    category: Optional[str] = Field(None, max_length=50)
    cost_type: Optional[str] = Field(None, max_length=20)
    has_budget: Optional[bool] = None
    annual_budget: Optional[Decimal] = None
    budget_variance_threshold: Optional[Decimal] = None
    is_allocatable: Optional[bool] = None
    allocation_basis: Optional[str] = Field(None, max_length=50)
    allocation_percentage: Optional[Decimal] = None
    manager_id: Optional[UUID] = None
    manager_name: Optional[str] = Field(None, max_length=200)
    effective_from: Optional[date] = None
    effective_to: Optional[date] = None
    default_expense_account_id: Optional[UUID] = None
    external_code: Optional[str] = Field(None, max_length=50)


class CostCenterResponse(BaseModel):
    """Cost Center response schema."""

    id: UUID
    organization_id: UUID
    code: str
    name: str
    description: Optional[str]
    parent_id: Optional[UUID]
    parent_code: Optional[str] = None
    parent_name: Optional[str] = None
    level: int
    path: Optional[str]
    category: Optional[str]
    cost_type: Optional[str]
    has_budget: bool
    annual_budget: Decimal
    budget_variance_threshold: Decimal
    is_allocatable: bool
    allocation_basis: Optional[str]
    allocation_percentage: Decimal
    manager_id: Optional[UUID]
    manager_name: Optional[str]
    effective_from: date
    effective_to: Optional[date]
    default_expense_account_id: Optional[UUID]
    external_code: Optional[str]
    is_leaf: bool
    created_at: date
    updated_at: Optional[date]
    is_active: bool

    class Config:
        from_attributes = True


class CostCenterListResponse(BaseModel):
    """Cost Center list response."""

    id: UUID
    organization_id: UUID
    code: str
    name: str
    parent_id: Optional[UUID]
    parent_code: Optional[str] = None
    level: int
    category: Optional[str]
    has_budget: bool
    annual_budget: Decimal
    is_allocatable: bool
    is_leaf: bool
    is_active: bool

    class Config:
        from_attributes = True


class CostCenterTreeNode(BaseModel):
    """Cost Center tree node for hierarchical display."""

    id: UUID
    code: str
    name: str
    level: int
    has_budget: bool
    annual_budget: Decimal
    is_allocatable: bool
    children: List["CostCenterTreeNode"] = []

    class Config:
        from_attributes = True


CostCenterTreeNode.model_rebuild()


class CostCenterBudgetSummary(BaseModel):
    """Budget summary for a cost center."""

    cost_center_id: UUID
    cost_center_code: str
    cost_center_name: str
    annual_budget: Decimal
    ytd_actual: Decimal
    ytd_budget: Decimal
    variance: Decimal
    variance_percentage: Decimal
    is_over_budget: bool


class CostCenterExpenseSummary(BaseModel):
    """Expense summary for a cost center."""

    cost_center_id: UUID
    cost_center_code: str
    cost_center_name: str
    period_from: date
    period_to: date
    total_expense: Decimal
    transaction_count: int


class BulkCostCenterCreate(BaseModel):
    """Schema for bulk creating cost centers."""

    organization_id: UUID
    cost_centers: List[CostCenterCreate]
