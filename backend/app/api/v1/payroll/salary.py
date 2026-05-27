"""
Salary Component and Structure API Endpoints
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_db_with_tenant
from app.models.auth.user import User
from app.schemas.payroll.salary_component import (
    SalaryComponentCreate,
    SalaryComponentUpdate,
    SalaryComponentResponse,
    SalaryComponentList,
    SalaryStructureCreate,
    SalaryStructureUpdate,
    SalaryStructureResponse,
    SalaryStructureList,
    EmployeeSalaryCreate,
    EmployeeSalaryUpdate,
    EmployeeSalaryResponse,
    EmployeeSalaryList,
)
from app.services.payroll.salary_service import (
    SalaryComponentService,
    SalaryStructureService,
    EmployeeSalaryService,
)
from app.core.exceptions import BadRequestException, NotFoundException

router = APIRouter()


def _require_organization_id(current_user: User) -> UUID:
    if not current_user.organization_id:
        raise BadRequestException(
            detail="Current user is not assigned to an organization",
            error_code="ORGANIZATION_CONTEXT_REQUIRED",
        )
    return current_user.organization_id


# ============== Salary Components ==============


@router.get("/components", response_model=dict, response_model_by_alias=True)
async def list_salary_components(
    component_type: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    active_only: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """List salary components for an organization"""
    service = SalaryComponentService(db)
    items, total = await service.list(
        organization_id=current_user.organization_id,
        component_type=component_type,
        category=category,
        active_only=active_only,
        skip=skip,
        limit=limit,
    )
    return {
        "items": [SalaryComponentList.model_validate(item) for item in items],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post(
    "/components",
    response_model=SalaryComponentResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
async def create_salary_component(
    data: SalaryComponentCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Create a new salary component"""
    service = SalaryComponentService(db)

    # Check for duplicate code
    existing = await service.get_by_code(data.organization_id, data.component_code)
    if existing:
        raise BadRequestException(
            detail=f"Component with code {data.component_code} already exists",
            error_code="COMPONENT_WITH_CODE_ALREADY_EXISTS",
        )

    component = await service.create(data, current_user.id)
    return SalaryComponentResponse.model_validate(component)


@router.get(
    "/components/{id}", response_model=SalaryComponentResponse, response_model_by_alias=True
)
async def get_salary_component(
    id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get salary component by ID"""
    service = SalaryComponentService(db)
    component = await service.get(id)
    if not component:
        raise NotFoundException(detail="Component not found", error_code="COMPONENT_NOT_FOUND")
    return SalaryComponentResponse.model_validate(component)


@router.put(
    "/components/{id}", response_model=SalaryComponentResponse, response_model_by_alias=True
)
async def update_salary_component(
    id: UUID,
    data: SalaryComponentUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Update a salary component"""
    service = SalaryComponentService(db)
    component = await service.update(id, data, current_user.id)
    if not component:
        raise NotFoundException(detail="Component not found", error_code="COMPONENT_NOT_FOUND")
    return SalaryComponentResponse.model_validate(component)


@router.delete("/components/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_salary_component(
    id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Delete (deactivate) a salary component"""
    service = SalaryComponentService(db)
    deleted = await service.delete(id)
    if not deleted:
        raise NotFoundException(detail="Component not found", error_code="COMPONENT_NOT_FOUND")


# ============== Salary Structures ==============


@router.get("/structures", response_model=dict, response_model_by_alias=True)
async def list_salary_structures(
    active_only: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """List salary structures for an organization"""
    service = SalaryStructureService(db)
    items, total = await service.list(
        organization_id=current_user.organization_id,
        active_only=active_only,
        skip=skip,
        limit=limit,
    )
    return {
        "items": [SalaryStructureList.model_validate(item) for item in items],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post(
    "/structures",
    response_model=SalaryStructureResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
async def create_salary_structure(
    data: SalaryStructureCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Create a new salary structure"""
    service = SalaryStructureService(db)
    structure = await service.create(data, current_user.id)
    return SalaryStructureResponse.model_validate(structure)


@router.get(
    "/structures/{id}", response_model=SalaryStructureResponse, response_model_by_alias=True
)
async def get_salary_structure(
    id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get salary structure by ID"""
    service = SalaryStructureService(db)
    structure = await service.get(id)
    if not structure:
        raise NotFoundException(detail="Structure not found", error_code="STRUCTURE_NOT_FOUND")
    return SalaryStructureResponse.model_validate(structure)


@router.put(
    "/structures/{id}", response_model=SalaryStructureResponse, response_model_by_alias=True
)
async def update_salary_structure(
    id: UUID,
    data: SalaryStructureUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Update a salary structure"""
    service = SalaryStructureService(db)
    structure = await service.update(id, data, current_user.id)
    if not structure:
        raise NotFoundException(detail="Structure not found", error_code="STRUCTURE_NOT_FOUND")
    return SalaryStructureResponse.model_validate(structure)


@router.delete("/structures/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_salary_structure(
    id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Delete (deactivate) a salary structure"""
    service = SalaryStructureService(db)
    deleted = await service.delete(id)
    if not deleted:
        raise NotFoundException(detail="Structure not found", error_code="STRUCTURE_NOT_FOUND")


# ============== Employee Salaries ==============


@router.get("/employee-salaries", response_model=dict, response_model_by_alias=True)
async def list_employee_salaries(
    employee_id: Optional[UUID] = Query(None),
    active_only: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """List employee salaries"""
    service = EmployeeSalaryService(db)
    items, total = await service.list(
        organization_id=_require_organization_id(current_user),
        employee_id=employee_id,
        active_only=active_only,
        skip=skip,
        limit=limit,
    )
    return {
        "items": [EmployeeSalaryList.model_validate(item) for item in items],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post(
    "/employee-salaries",
    response_model=EmployeeSalaryResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
async def create_employee_salary(
    data: EmployeeSalaryCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Assign salary to an employee"""
    service = EmployeeSalaryService(db)
    salary = await service.create(data, current_user.id)
    return EmployeeSalaryResponse.model_validate(salary)


@router.get(
    "/employee-salaries/{id}", response_model=EmployeeSalaryResponse, response_model_by_alias=True
)
async def get_employee_salary(
    id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get employee salary by ID"""
    service = EmployeeSalaryService(db)
    salary = await service.get(id)
    if not salary:
        raise NotFoundException(
            detail="Employee salary not found",
            error_code="EMPLOYEE_SALARY_NOT_FOUND",
        )
    return EmployeeSalaryResponse.model_validate(salary)


@router.get(
    "/employee-salaries/employee/{employee_id}/current",
    response_model=EmployeeSalaryResponse,
    response_model_by_alias=True,
)
async def get_current_employee_salary(
    employee_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
):
    """Get current active salary for an employee"""
    service = EmployeeSalaryService(db)
    salary = await service.get_active_salary(employee_id)
    if not salary:
        raise NotFoundException(
            detail="No active salary found for employee",
            error_code="NO_ACTIVE_SALARY_FOUND_FOR_EMPLOYEE",
        )
    return EmployeeSalaryResponse.model_validate(salary)
