"""Cost Center API endpoints."""

from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.auth.user import User
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
from app.services.finance.cost_center_service import CostCenterService

router = APIRouter()


@router.get("", response_model=dict)
async def list_cost_centers(
    organization_id: UUID,
    include_inactive: bool = False,
    parent_id: Optional[UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List cost centers for an organization."""
    service = CostCenterService(db)
    items, total = await service.get_by_organization(
        organization_id=organization_id,
        include_inactive=include_inactive,
        parent_id=parent_id,
        skip=skip,
        limit=limit,
    )

    return {
        "items": [service.to_list_response(cc) for cc in items],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/tree", response_model=List[CostCenterTreeNode])
async def get_cost_center_tree(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get cost center hierarchy as tree."""
    service = CostCenterService(db)
    return await service.get_tree(organization_id)


@router.get("/root", response_model=List[CostCenterListResponse])
async def get_root_cost_centers(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get root level cost centers."""
    service = CostCenterService(db)
    items = await service.get_root_cost_centers(organization_id)
    return [service.to_list_response(cc) for cc in items]


@router.get("/allocatable", response_model=List[CostCenterListResponse])
async def get_allocatable_cost_centers(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get cost centers that can have expenses allocated."""
    service = CostCenterService(db)
    items = await service.get_allocatable(organization_id)
    return [service.to_list_response(cc) for cc in items]


@router.get("/with-budgets", response_model=List[CostCenterListResponse])
async def get_cost_centers_with_budgets(
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get cost centers with budget tracking enabled."""
    service = CostCenterService(db)
    items = await service.get_with_budgets(organization_id)
    return [service.to_list_response(cc) for cc in items]


@router.get("/search", response_model=List[CostCenterListResponse])
async def search_cost_centers(
    organization_id: UUID,
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Search cost centers by code or name."""
    service = CostCenterService(db)
    items = await service.search(organization_id, q, limit)
    return [service.to_list_response(cc) for cc in items]


@router.get("/by-code/{code}", response_model=CostCenterResponse)
async def get_cost_center_by_code(
    code: str,
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get cost center by code."""
    service = CostCenterService(db)
    cost_center = await service.get_by_code(organization_id, code)
    if not cost_center:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cost center not found",
        )
    return service.to_response(cost_center)


@router.post("", response_model=CostCenterResponse, status_code=status.HTTP_201_CREATED)
async def create_cost_center(
    data: CostCenterCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new cost center."""
    service = CostCenterService(db)
    try:
        cost_center = await service.create(data, current_user.id)
        return service.to_response(cost_center)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/bulk", response_model=List[CostCenterResponse], status_code=status.HTTP_201_CREATED)
async def bulk_create_cost_centers(
    data: BulkCostCenterCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create multiple cost centers at once."""
    service = CostCenterService(db)
    try:
        cost_centers = await service.bulk_create(data, current_user.id)
        return [service.to_response(cc) for cc in cost_centers]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/{id}", response_model=CostCenterResponse)
async def get_cost_center(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get cost center by ID."""
    service = CostCenterService(db)
    cost_center = await service.get(id)
    if not cost_center:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cost center not found",
        )
    return service.to_response(cost_center)


@router.get("/{id}/children", response_model=List[CostCenterListResponse])
async def get_cost_center_children(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get child cost centers."""
    service = CostCenterService(db)
    children = await service.get_children(id)
    return [service.to_list_response(cc) for cc in children]


@router.get("/{id}/expense-summary", response_model=CostCenterExpenseSummary)
async def get_cost_center_expense_summary(
    id: UUID,
    from_date: date,
    to_date: date,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get expense summary for a cost center."""
    service = CostCenterService(db)
    try:
        return await service.get_expense_summary(id, from_date, to_date)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/{id}/budget-summary", response_model=CostCenterBudgetSummary)
async def get_cost_center_budget_summary(
    id: UUID,
    financial_year_start: date,
    as_of_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get budget vs actual summary for a cost center."""
    service = CostCenterService(db)
    try:
        return await service.get_budget_summary(id, financial_year_start, as_of_date)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put("/{id}", response_model=CostCenterResponse)
async def update_cost_center(
    id: UUID,
    data: CostCenterUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a cost center."""
    service = CostCenterService(db)
    try:
        cost_center = await service.update(id, data, current_user.id)
        if not cost_center:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cost center not found",
            )
        return service.to_response(cost_center)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put("/{id}/budget", response_model=CostCenterResponse)
async def update_cost_center_budget(
    id: UUID,
    annual_budget: Decimal,
    has_budget: bool = True,
    variance_threshold: Optional[Decimal] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update budget settings for a cost center."""
    service = CostCenterService(db)
    cost_center = await service.update_budget(
        id, annual_budget, has_budget, variance_threshold
    )
    if not cost_center:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cost center not found",
        )
    return service.to_response(cost_center)


@router.post("/{id}/activate", response_model=CostCenterResponse)
async def activate_cost_center(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Activate a cost center."""
    service = CostCenterService(db)
    cost_center = await service.activate(id)
    if not cost_center:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cost center not found",
        )
    return service.to_response(cost_center)


@router.post("/{id}/deactivate", response_model=CostCenterResponse)
async def deactivate_cost_center(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Deactivate a cost center."""
    service = CostCenterService(db)
    cost_center = await service.deactivate(id)
    if not cost_center:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cost center not found",
        )
    return service.to_response(cost_center)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cost_center(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a cost center."""
    service = CostCenterService(db)
    try:
        deleted = await service.delete(id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cost center not found",
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
