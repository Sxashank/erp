"""Cost Center service."""

from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance.cost_center import CostCenter
from app.repositories.finance.cost_center_repo import CostCenterRepository
from app.schemas.finance.cost_center import (
    CostCenterCreate,
    CostCenterUpdate,
    CostCenterResponse,
    CostCenterListResponse,
    CostCenterTreeNode,
    CostCenterBudgetSummary,
    CostCenterExpenseSummary,
    BulkCostCenterCreate,
)


class CostCenterService:
    """Service for Cost Center operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = CostCenterRepository(session)

    async def create(
        self,
        data: CostCenterCreate,
        created_by: Optional[UUID] = None,
    ) -> CostCenter:
        """Create a new cost center."""
        # Check for duplicate code
        if await self.repository.code_exists(data.code, data.organization_id):
            raise ValueError(f"Cost center code '{data.code}' already exists")

        # Determine level and path based on parent
        level = 0
        path = f"/{data.code}"

        if data.parent_id:
            parent = await self.repository.get(data.parent_id)
            if not parent:
                raise ValueError("Parent cost center not found")
            if parent.organization_id != data.organization_id:
                raise ValueError("Parent cost center belongs to different organization")
            level = parent.level + 1
            path = f"{parent.path}/{data.code}"

        # Create cost center
        cost_center_data = data.model_dump()
        cost_center_data["level"] = level
        cost_center_data["path"] = path
        if created_by:
            cost_center_data["created_by"] = created_by

        cost_center = CostCenter(**cost_center_data)
        return await self.repository.create(cost_center)

    async def update(
        self,
        id: UUID,
        data: CostCenterUpdate,
        updated_by: Optional[UUID] = None,
    ) -> Optional[CostCenter]:
        """Update a cost center."""
        cost_center = await self.repository.get(id)
        if not cost_center:
            return None

        update_data = data.model_dump(exclude_unset=True)

        # Check code uniqueness if changing code
        if "code" in update_data and update_data["code"] != cost_center.code:
            if await self.repository.code_exists(
                update_data["code"],
                cost_center.organization_id,
                exclude_id=id,
            ):
                raise ValueError(f"Cost center code '{update_data['code']}' already exists")

        # Handle parent change
        if "parent_id" in update_data:
            new_parent_id = update_data["parent_id"]
            if new_parent_id:
                # Validate parent
                parent = await self.repository.get(new_parent_id)
                if not parent:
                    raise ValueError("Parent cost center not found")
                if parent.organization_id != cost_center.organization_id:
                    raise ValueError("Parent cost center belongs to different organization")

                # Check for circular reference
                if await self._would_create_cycle(id, new_parent_id):
                    raise ValueError("Cannot set parent: would create circular reference")

                update_data["level"] = parent.level + 1
                new_code = update_data.get("code", cost_center.code)
                update_data["path"] = f"{parent.path}/{new_code}"
            else:
                update_data["level"] = 0
                new_code = update_data.get("code", cost_center.code)
                update_data["path"] = f"/{new_code}"

            # Update children paths if needed
            if new_parent_id != cost_center.parent_id:
                await self._update_descendants_path(cost_center, update_data.get("path", cost_center.path))

        if updated_by:
            update_data["updated_by"] = updated_by

        return await self.repository.update(id, update_data)

    async def _would_create_cycle(self, cost_center_id: UUID, new_parent_id: UUID) -> bool:
        """Check if setting new_parent_id as parent would create a cycle."""
        # If the new parent is the same as the cost center, it's a cycle
        if cost_center_id == new_parent_id:
            return True

        # Check if new_parent_id is a descendant of cost_center_id
        descendants = await self.repository.get_all_descendants(cost_center_id)
        return any(d.id == new_parent_id for d in descendants)

    async def _update_descendants_path(self, cost_center: CostCenter, new_path: str) -> None:
        """Update paths of all descendants when parent path changes."""
        old_path = cost_center.path
        descendants = await self.repository.get_all_descendants(cost_center.id)

        for descendant in descendants:
            if descendant.path and old_path:
                new_descendant_path = descendant.path.replace(old_path, new_path, 1)
                new_level = new_descendant_path.count("/") - 1
                await self.repository.update(
                    descendant.id,
                    {"path": new_descendant_path, "level": new_level}
                )

    async def delete(self, id: UUID) -> bool:
        """Soft delete a cost center."""
        cost_center = await self.repository.get_with_children(id)
        if not cost_center:
            return False

        # Check for children
        if cost_center.children and len(cost_center.children) > 0:
            raise ValueError("Cannot delete cost center with children. Delete children first.")

        # Check for transactions
        if await self.repository.has_transactions(id):
            raise ValueError("Cannot delete cost center with transactions. Deactivate instead.")

        return await self.repository.delete(id)

    async def deactivate(self, id: UUID) -> Optional[CostCenter]:
        """Deactivate a cost center (soft disable)."""
        return await self.repository.update(id, {"is_active": False})

    async def activate(self, id: UUID) -> Optional[CostCenter]:
        """Activate a cost center."""
        return await self.repository.update(id, {"is_active": True})

    async def get(self, id: UUID) -> Optional[CostCenter]:
        """Get a cost center by ID."""
        return await self.repository.get_with_details(id)

    async def get_by_code(
        self,
        organization_id: UUID,
        code: str,
    ) -> Optional[CostCenter]:
        """Get a cost center by code."""
        return await self.repository.get_by_code(organization_id, code)

    async def get_by_organization(
        self,
        organization_id: UUID,
        include_inactive: bool = False,
        parent_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[CostCenter], int]:
        """Get cost centers for an organization."""
        return await self.repository.get_by_organization(
            organization_id=organization_id,
            include_inactive=include_inactive,
            parent_id=parent_id,
            skip=skip,
            limit=limit,
        )

    async def get_root_cost_centers(
        self,
        organization_id: UUID,
    ) -> List[CostCenter]:
        """Get root level cost centers."""
        return await self.repository.get_root_cost_centers(organization_id)

    async def get_children(self, parent_id: UUID) -> List[CostCenter]:
        """Get child cost centers."""
        return await self.repository.get_children(parent_id)

    async def get_tree(self, organization_id: UUID) -> List[CostCenterTreeNode]:
        """Get cost center hierarchy as tree."""
        root_centers = await self.repository.get_root_cost_centers(organization_id)
        return [await self._build_tree_node(cc) for cc in root_centers]

    async def _build_tree_node(self, cost_center: CostCenter) -> CostCenterTreeNode:
        """Build a tree node from a cost center."""
        children = await self.repository.get_children(cost_center.id)
        child_nodes = [await self._build_tree_node(c) for c in children]

        return CostCenterTreeNode(
            id=cost_center.id,
            code=cost_center.code,
            name=cost_center.name,
            level=cost_center.level,
            has_budget=cost_center.has_budget,
            annual_budget=cost_center.annual_budget,
            is_allocatable=cost_center.is_allocatable,
            children=child_nodes,
        )

    async def get_allocatable(self, organization_id: UUID) -> List[CostCenter]:
        """Get cost centers that can have expenses allocated."""
        return await self.repository.get_allocatable(organization_id)

    async def get_with_budgets(self, organization_id: UUID) -> List[CostCenter]:
        """Get cost centers with budget tracking enabled."""
        return await self.repository.get_with_budgets(organization_id)

    async def search(
        self,
        organization_id: UUID,
        query: str,
        limit: int = 20,
    ) -> List[CostCenter]:
        """Search cost centers by code or name."""
        return await self.repository.search(organization_id, query, limit)

    async def get_expense_summary(
        self,
        cost_center_id: UUID,
        from_date: date,
        to_date: date,
    ) -> CostCenterExpenseSummary:
        """Get expense summary for a cost center."""
        cost_center = await self.repository.get(cost_center_id)
        if not cost_center:
            raise ValueError("Cost center not found")

        summary = await self.repository.get_expense_summary(
            cost_center_id, from_date, to_date
        )

        return CostCenterExpenseSummary(
            cost_center_id=cost_center_id,
            cost_center_code=cost_center.code,
            cost_center_name=cost_center.name,
            period_from=from_date,
            period_to=to_date,
            total_expense=summary["net_expense"],
            transaction_count=summary["transaction_count"],
        )

    async def get_budget_summary(
        self,
        cost_center_id: UUID,
        financial_year_start: date,
        as_of_date: Optional[date] = None,
    ) -> CostCenterBudgetSummary:
        """Get budget vs actual summary for a cost center."""
        cost_center = await self.repository.get(cost_center_id)
        if not cost_center:
            raise ValueError("Cost center not found")

        if not cost_center.has_budget:
            raise ValueError("Budget tracking not enabled for this cost center")

        as_of = as_of_date or date.today()

        # Get YTD actual expenses
        expense_summary = await self.repository.get_expense_summary(
            cost_center_id, financial_year_start, as_of
        )
        ytd_actual = expense_summary["net_expense"]

        # Calculate YTD budget (pro-rated)
        days_in_year = 365
        days_elapsed = (as_of - financial_year_start).days + 1
        ytd_budget = (cost_center.annual_budget * Decimal(days_elapsed)) / Decimal(days_in_year)

        # Calculate variance
        variance = ytd_budget - ytd_actual
        variance_percentage = Decimal("0.00")
        if ytd_budget > 0:
            variance_percentage = (variance / ytd_budget) * Decimal("100")

        return CostCenterBudgetSummary(
            cost_center_id=cost_center_id,
            cost_center_code=cost_center.code,
            cost_center_name=cost_center.name,
            annual_budget=cost_center.annual_budget,
            ytd_actual=ytd_actual,
            ytd_budget=ytd_budget.quantize(Decimal("0.01")),
            variance=variance.quantize(Decimal("0.01")),
            variance_percentage=variance_percentage.quantize(Decimal("0.01")),
            is_over_budget=ytd_actual > ytd_budget,
        )

    async def bulk_create(
        self,
        data: BulkCostCenterCreate,
        created_by: Optional[UUID] = None,
    ) -> List[CostCenter]:
        """Create multiple cost centers at once."""
        created = []
        for cc_data in data.cost_centers:
            # Ensure organization_id is set
            if cc_data.organization_id != data.organization_id:
                cc_data.organization_id = data.organization_id
            cost_center = await self.create(cc_data, created_by)
            created.append(cost_center)
        return created

    async def update_budget(
        self,
        id: UUID,
        annual_budget: Decimal,
        has_budget: bool = True,
        variance_threshold: Optional[Decimal] = None,
    ) -> Optional[CostCenter]:
        """Update budget settings for a cost center."""
        update_data = {
            "has_budget": has_budget,
            "annual_budget": annual_budget,
        }
        if variance_threshold is not None:
            update_data["budget_variance_threshold"] = variance_threshold

        return await self.repository.update(id, update_data)

    def to_response(self, cost_center: CostCenter) -> CostCenterResponse:
        """Convert cost center to response schema."""
        return CostCenterResponse(
            id=cost_center.id,
            organization_id=cost_center.organization_id,
            code=cost_center.code,
            name=cost_center.name,
            description=cost_center.description,
            parent_id=cost_center.parent_id,
            parent_code=cost_center.parent.code if cost_center.parent else None,
            parent_name=cost_center.parent.name if cost_center.parent else None,
            level=cost_center.level,
            path=cost_center.path,
            category=cost_center.category,
            cost_type=cost_center.cost_type,
            has_budget=cost_center.has_budget,
            annual_budget=cost_center.annual_budget,
            budget_variance_threshold=cost_center.budget_variance_threshold,
            is_allocatable=cost_center.is_allocatable,
            allocation_basis=cost_center.allocation_basis,
            allocation_percentage=cost_center.allocation_percentage,
            manager_id=cost_center.manager_id,
            manager_name=cost_center.manager_name,
            effective_from=cost_center.effective_from,
            effective_to=cost_center.effective_to,
            default_expense_account_id=cost_center.default_expense_account_id,
            external_code=cost_center.external_code,
            is_leaf=cost_center.is_leaf,
            created_at=cost_center.created_at.date() if cost_center.created_at else date.today(),
            updated_at=cost_center.updated_at.date() if cost_center.updated_at else None,
            is_active=cost_center.is_active,
        )

    def to_list_response(self, cost_center: CostCenter) -> CostCenterListResponse:
        """Convert cost center to list response schema."""
        return CostCenterListResponse(
            id=cost_center.id,
            organization_id=cost_center.organization_id,
            code=cost_center.code,
            name=cost_center.name,
            parent_id=cost_center.parent_id,
            parent_code=cost_center.parent.code if cost_center.parent else None,
            level=cost_center.level,
            category=cost_center.category,
            has_budget=cost_center.has_budget,
            annual_budget=cost_center.annual_budget,
            is_allocatable=cost_center.is_allocatable,
            is_leaf=cost_center.is_leaf,
            is_active=cost_center.is_active,
        )
