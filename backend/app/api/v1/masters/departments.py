"""Department API endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user, RequirePermissions, get_db_with_tenant
from app.models.auth.user import User
from app.services.masters.department_service import DepartmentService
from app.schemas.masters.department import (
    DepartmentCreate,
    DepartmentUpdate,
    DepartmentResponse,
    DepartmentTreeResponse,
)
from app.schemas.base import PaginatedResponse, MessageResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse[DepartmentResponse], response_model_by_alias=True)
async def list_departments(
    organization_id: Optional[UUID] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    include_inactive: bool = Query(False),
    current_user: User = Depends(RequirePermissions("MASTER_DEPT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get paginated list of departments.
    Requires MASTER_DEPT_VIEW permission.
    """
    dept_service = DepartmentService(db)
    skip = (page - 1) * page_size
    depts, total = await dept_service.get_all(organization_id, skip, page_size, include_inactive)

    items = [_dept_to_response(d) for d in depts]

    return PaginatedResponse.create(items, total, page, page_size)


@router.post("", response_model=DepartmentResponse, response_model_by_alias=True)
async def create_department(
    data: DepartmentCreate,
    current_user: User = Depends(RequirePermissions("MASTER_DEPT_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Create a new department.
    Requires MASTER_DEPT_CREATE permission.
    """
    dept_service = DepartmentService(db)
    dept = await dept_service.create(data, current_user.id)

    return _dept_to_response(dept)


@router.get("/tree", response_model=List[DepartmentTreeResponse], response_model_by_alias=True)
async def get_department_tree(
    organization_id: UUID,
    current_user: User = Depends(RequirePermissions("MASTER_DEPT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get department hierarchy tree for an organization.
    Requires MASTER_DEPT_VIEW permission.
    """
    dept_service = DepartmentService(db)
    # Service now returns pre-built tree as dictionaries
    tree = await dept_service.get_tree(organization_id)
    return tree


@router.get("/{dept_id}", response_model=DepartmentResponse, response_model_by_alias=True)
async def get_department(
    dept_id: UUID,
    current_user: User = Depends(RequirePermissions("MASTER_DEPT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get department by ID.
    Requires MASTER_DEPT_VIEW permission.
    """
    dept_service = DepartmentService(db)
    result = await dept_service.get(dept_id)

    dept = result["department"]
    return DepartmentResponse(
        id=dept.id,
        code=dept.code,
        name=dept.name,
        short_name=dept.short_name,
        description=dept.description,
        organization_id=dept.organization_id,
        parent_dept_id=dept.parent_dept_id,
        level=dept.level,
        path=dept.path,
        cost_center_code=dept.cost_center_code,
        head_name=dept.head_name,
        email=dept.email,
        phone=dept.phone,
        status=dept.status,
        created_at=dept.created_at,
        updated_at=dept.updated_at,
        is_active=dept.is_active,
        organization_name=dept.organization.name if dept.organization else None,
        parent_dept_name=dept.parent_dept.name if dept.parent_dept else None,
        designation_count=result["designation_count"],
    )


@router.put("/{dept_id}", response_model=DepartmentResponse, response_model_by_alias=True)
async def update_department(
    dept_id: UUID,
    data: DepartmentUpdate,
    current_user: User = Depends(RequirePermissions("MASTER_DEPT_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Update an existing department.
    Requires MASTER_DEPT_UPDATE permission.
    """
    dept_service = DepartmentService(db)
    dept = await dept_service.update(dept_id, data, current_user.id)

    return _dept_to_response(dept)


@router.delete("/{dept_id}", response_model=MessageResponse, response_model_by_alias=True)
async def delete_department(
    dept_id: UUID,
    current_user: User = Depends(RequirePermissions("MASTER_DEPT_DELETE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Soft delete a department.
    Requires MASTER_DEPT_DELETE permission.
    """
    dept_service = DepartmentService(db)
    await dept_service.delete(dept_id, current_user.id)

    return MessageResponse(message="Department deleted successfully")


@router.get("/{dept_id}/children", response_model=List[DepartmentResponse], response_model_by_alias=True)
async def get_department_children(
    dept_id: UUID,
    current_user: User = Depends(RequirePermissions("MASTER_DEPT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get child departments of a department.
    Requires MASTER_DEPT_VIEW permission.
    """
    dept_service = DepartmentService(db)
    children = await dept_service.get_children(dept_id)

    return [_dept_to_response(d) for d in children]


def _dept_to_response(dept) -> DepartmentResponse:
    """Convert Department model to DepartmentResponse."""
    return DepartmentResponse(
        id=dept.id,
        code=dept.code,
        name=dept.name,
        short_name=dept.short_name,
        description=dept.description,
        organization_id=dept.organization_id,
        parent_dept_id=dept.parent_dept_id,
        level=dept.level,
        path=dept.path,
        cost_center_code=dept.cost_center_code,
        head_name=dept.head_name,
        email=dept.email,
        phone=dept.phone,
        status=dept.status,
        created_at=dept.created_at,
        updated_at=dept.updated_at,
        is_active=dept.is_active,
        organization_name=dept.organization.name if dept.organization else None,
        parent_dept_name=dept.parent_dept.name if dept.parent_dept else None,
    )


def _build_dept_tree(dept) -> DepartmentTreeResponse:
    """Build department tree response recursively."""
    return DepartmentTreeResponse(
        id=dept.id,
        code=dept.code,
        name=dept.name,
        level=dept.level,
        status=dept.status,
        designation_count=len(dept.designations) if hasattr(dept, 'designations') else 0,
        children=[_build_dept_tree(child) for child in dept.child_depts if child.is_active],
    )
