"""HRIS performance management API endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_db_with_tenant
from app.core.constants import Permissions
from app.core.exceptions import BadRequestException
from app.models.auth.user import User
from app.schemas.hris.performance import (
    AppraisalCycleCreate,
    AppraisalCycleListBundleResponse,
    AppraisalCycleResponse,
    AppraisalCycleUpdate,
    EmployeePerformanceDetailResponse,
    PerformanceCalibrationSubmit,
    PerformanceEmployeeSummaryResponse,
    PerformanceGoalCreate,
    PerformanceGoalUpdate,
    PerformanceManagerReviewSubmit,
    PerformanceSelfAppraisalSubmit,
)
from app.services.hris.performance_service import PerformanceService

router = APIRouter()


def _require_organization_id(current_user: User) -> UUID:
    if not current_user.organization_id:
        raise BadRequestException(
            detail="Current user is not assigned to an organization",
            error_code="ORGANIZATION_CONTEXT_REQUIRED",
        )
    return current_user.organization_id


@router.get(
    "/performance/cycles",
    response_model=AppraisalCycleListBundleResponse,
    response_model_by_alias=True,
)
async def list_appraisal_cycles(
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(
        RequirePermissions(
            Permissions.HRIS_APPRAISAL_VIEW,
            Permissions.HRIS_GOAL_VIEW,
            require_all=False,
        )
    ),
):
    """List appraisal cycles for the active organization."""
    service = PerformanceService(db)
    return await service.list_cycles(
        organization_id=_require_organization_id(current_user),
        skip=skip,
        limit=limit,
        status=status_filter,
        search=search,
    )


@router.post(
    "/performance/cycles",
    response_model=AppraisalCycleResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
async def create_appraisal_cycle(
    data: AppraisalCycleCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_APPRAISAL_CREATE)),
):
    """Create a new appraisal cycle."""
    service = PerformanceService(db)
    cycle = await service.create_cycle(
        organization_id=_require_organization_id(current_user),
        data=data,
        created_by=current_user.id,
    )
    await db.commit()
    return cycle


@router.get(
    "/performance/cycles/{cycle_id}",
    response_model=AppraisalCycleResponse,
    response_model_by_alias=True,
)
async def get_appraisal_cycle(
    cycle_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_APPRAISAL_VIEW)),
):
    """Get appraisal cycle details."""
    service = PerformanceService(db)
    return await service.get_cycle(cycle_id)


@router.put(
    "/performance/cycles/{cycle_id}",
    response_model=AppraisalCycleResponse,
    response_model_by_alias=True,
)
async def update_appraisal_cycle(
    cycle_id: UUID,
    data: AppraisalCycleUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_APPRAISAL_UPDATE)),
):
    """Update appraisal cycle metadata."""
    service = PerformanceService(db)
    cycle = await service.update_cycle(cycle_id, data, current_user.id)
    await db.commit()
    return cycle


@router.post(
    "/performance/cycles/{cycle_id}/start",
    response_model=AppraisalCycleResponse,
    response_model_by_alias=True,
)
async def start_appraisal_cycle(
    cycle_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_APPRAISAL_UPDATE)),
):
    """Move an appraisal cycle into goal-setting."""
    service = PerformanceService(db)
    cycle = await service.start_cycle(cycle_id, current_user.id)
    await db.commit()
    return cycle


@router.post(
    "/performance/cycles/{cycle_id}/close",
    response_model=AppraisalCycleResponse,
    response_model_by_alias=True,
)
async def close_appraisal_cycle(
    cycle_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_APPRAISAL_UPDATE)),
):
    """Close an appraisal cycle after all appraisals are completed."""
    service = PerformanceService(db)
    cycle = await service.close_cycle(cycle_id, current_user.id)
    await db.commit()
    return cycle


@router.get(
    "/performance/cycles/{cycle_id}/employees",
    response_model=list[PerformanceEmployeeSummaryResponse],
    response_model_by_alias=True,
)
async def list_cycle_employees(
    cycle_id: UUID,
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(
        RequirePermissions(
            Permissions.HRIS_APPRAISAL_VIEW,
            Permissions.HRIS_GOAL_VIEW,
            require_all=False,
        )
    ),
):
    """List employees participating in an appraisal cycle."""
    service = PerformanceService(db)
    return await service.list_cycle_employees(
        cycle_id=cycle_id,
        search=search,
        status=status_filter,
    )


@router.get(
    "/performance/cycles/{cycle_id}/employees/{employee_id}",
    response_model=EmployeePerformanceDetailResponse,
    response_model_by_alias=True,
)
async def get_employee_performance_detail(
    cycle_id: UUID,
    employee_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(
        RequirePermissions(
            Permissions.HRIS_APPRAISAL_VIEW,
            Permissions.HRIS_GOAL_VIEW,
            require_all=False,
        )
    ),
):
    """Get the full performance packet for one employee inside a cycle."""
    service = PerformanceService(db)
    return await service.get_employee_performance_detail(cycle_id, employee_id)


@router.post(
    "/performance/cycles/{cycle_id}/employees/{employee_id}/goals",
    response_model=EmployeePerformanceDetailResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
async def create_employee_goal(
    cycle_id: UUID,
    employee_id: UUID,
    data: PerformanceGoalCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_GOAL_CREATE)),
):
    """Create a goal for an employee within an appraisal cycle."""
    service = PerformanceService(db)
    detail = await service.create_goal(cycle_id, employee_id, data, current_user.id)
    await db.commit()
    return detail


@router.put(
    "/performance/goals/{goal_id}",
    response_model=EmployeePerformanceDetailResponse,
    response_model_by_alias=True,
)
async def update_employee_goal(
    goal_id: UUID,
    data: PerformanceGoalUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_GOAL_UPDATE)),
):
    """Update an appraisal goal."""
    service = PerformanceService(db)
    detail = await service.update_goal(goal_id, data, current_user.id)
    await db.commit()
    return detail


@router.delete(
    "/performance/goals/{goal_id}",
    response_model=EmployeePerformanceDetailResponse,
    response_model_by_alias=True,
)
async def delete_employee_goal(
    goal_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_GOAL_UPDATE)),
):
    """Soft-delete a goal and return the refreshed employee packet."""
    service = PerformanceService(db)
    cycle_id, employee_id = await service.delete_goal(goal_id, current_user.id)
    detail = await service.get_employee_performance_detail(cycle_id, employee_id)
    await db.commit()
    return detail


@router.post(
    "/performance/cycles/{cycle_id}/employees/{employee_id}/goals/submit",
    response_model=EmployeePerformanceDetailResponse,
    response_model_by_alias=True,
)
async def submit_employee_goals(
    cycle_id: UUID,
    employee_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(
        RequirePermissions(
            Permissions.HRIS_GOAL_APPROVE,
            Permissions.HRIS_GOAL_UPDATE,
            require_all=False,
        )
    ),
):
    """Submit employee goals for the next stage."""
    service = PerformanceService(db)
    detail = await service.submit_goals(cycle_id, employee_id, current_user.id)
    await db.commit()
    return detail


@router.post(
    "/performance/cycles/{cycle_id}/employees/{employee_id}/self-appraisal",
    response_model=EmployeePerformanceDetailResponse,
    response_model_by_alias=True,
)
async def submit_employee_self_appraisal(
    cycle_id: UUID,
    employee_id: UUID,
    data: PerformanceSelfAppraisalSubmit,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_SELF_APPRAISAL)),
):
    """Submit the employee self-appraisal payload."""
    service = PerformanceService(db)
    detail = await service.submit_self_appraisal(cycle_id, employee_id, data, current_user.id)
    await db.commit()
    return detail


@router.post(
    "/performance/cycles/{cycle_id}/employees/{employee_id}/manager-review",
    response_model=EmployeePerformanceDetailResponse,
    response_model_by_alias=True,
)
async def submit_manager_review(
    cycle_id: UUID,
    employee_id: UUID,
    data: PerformanceManagerReviewSubmit,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_MANAGER_REVIEW)),
):
    """Submit manager review for an employee appraisal."""
    service = PerformanceService(db)
    detail = await service.submit_manager_review(cycle_id, employee_id, data, current_user.id)
    await db.commit()
    return detail


@router.post(
    "/performance/cycles/{cycle_id}/employees/{employee_id}/calibration",
    response_model=EmployeePerformanceDetailResponse,
    response_model_by_alias=True,
)
async def calibrate_employee_appraisal(
    cycle_id: UUID,
    employee_id: UUID,
    data: PerformanceCalibrationSubmit,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_CALIBRATION)),
):
    """Calibrate and close out an employee appraisal."""
    service = PerformanceService(db)
    detail = await service.calibrate_appraisal(cycle_id, employee_id, data, current_user.id)
    await db.commit()
    return detail
