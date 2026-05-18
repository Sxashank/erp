"""Cost Center schemas."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from app.schemas.base import CamelSchema


class CostCenterBase(CamelSchema):
    """Base Cost Center schema."""

    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=200)
    description: str | None = None
    category: str | None = Field(None, max_length=50)
    cost_type: str | None = Field(None, max_length=20)
    has_budget: bool = False
    annual_budget: Decimal = Decimal("0.00")
    budget_variance_threshold: Decimal = Decimal("10.00")
    is_allocatable: bool = True
    allocation_basis: str | None = Field(None, max_length=50)
    allocation_percentage: Decimal = Decimal("100.00")
    manager_id: UUID | None = None
    manager_name: str | None = Field(None, max_length=200)
    effective_from: date = Field(default_factory=date.today)
    effective_to: date | None = None
    default_expense_account_id: UUID | None = None
    external_code: str | None = Field(None, max_length=50)


class CostCenterCreate(CostCenterBase):
    """Schema for creating Cost Center."""

    organization_id: UUID
    parent_id: UUID | None = None


class CostCenterUpdate(CamelSchema):
    """Schema for updating Cost Center."""

    code: str | None = Field(None, max_length=20)
    name: str | None = Field(None, max_length=200)
    description: str | None = None
    parent_id: UUID | None = None
    category: str | None = Field(None, max_length=50)
    cost_type: str | None = Field(None, max_length=20)
    has_budget: bool | None = None
    annual_budget: Decimal | None = None
    budget_variance_threshold: Decimal | None = None
    is_allocatable: bool | None = None
    allocation_basis: str | None = Field(None, max_length=50)
    allocation_percentage: Decimal | None = None
    manager_id: UUID | None = None
    manager_name: str | None = Field(None, max_length=200)
    effective_from: date | None = None
    effective_to: date | None = None
    default_expense_account_id: UUID | None = None
    external_code: str | None = Field(None, max_length=50)


class CostCenterResponse(CamelSchema):
    """Cost Center response schema."""

    id: UUID
    organization_id: UUID
    code: str
    name: str
    description: str | None
    parent_id: UUID | None
    parent_code: str | None = None
    parent_name: str | None = None
    level: int
    path: str | None
    category: str | None
    cost_type: str | None
    has_budget: bool
    annual_budget: Decimal
    budget_variance_threshold: Decimal
    is_allocatable: bool
    allocation_basis: str | None
    allocation_percentage: Decimal
    manager_id: UUID | None
    manager_name: str | None
    effective_from: date
    effective_to: date | None
    default_expense_account_id: UUID | None
    external_code: str | None
    is_leaf: bool
    created_at: date
    updated_at: date | None
    is_active: bool


class CostCenterListResponse(CamelSchema):
    """Cost Center list response."""

    id: UUID
    organization_id: UUID
    code: str
    name: str
    parent_id: UUID | None
    parent_code: str | None = None
    level: int
    category: str | None
    has_budget: bool
    annual_budget: Decimal
    is_allocatable: bool
    is_leaf: bool
    is_active: bool


class CostCenterTreeNode(CamelSchema):
    """Cost Center tree node for hierarchical display."""

    id: UUID
    code: str
    name: str
    level: int
    has_budget: bool
    annual_budget: Decimal
    is_allocatable: bool
    children: list["CostCenterTreeNode"] = Field(default_factory=list)



CostCenterTreeNode.model_rebuild()


class CostCenterBudgetSummary(CamelSchema):
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


class CostCenterExpenseSummary(CamelSchema):
    """Expense summary for a cost center."""

    cost_center_id: UUID
    cost_center_code: str
    cost_center_name: str
    period_from: date
    period_to: date
    total_expense: Decimal
    transaction_count: int


class BulkCostCenterCreate(CamelSchema):
    """Schema for bulk creating cost centers."""

    organization_id: UUID
    cost_centers: list[CostCenterCreate]
