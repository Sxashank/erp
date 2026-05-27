"""ESS appraisal and goal API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ESSUserContext, get_current_ess_user, get_ess_db_with_tenant
from app.core.exceptions import BadRequestException
from app.schemas.ess.operations import ESSPerformanceGoalListResponse
from app.schemas.hris.performance import PerformanceSelfAppraisalSubmit
from app.services.hris.performance_service import PerformanceService

router = APIRouter(prefix="/performance", tags=["ESS Performance"])


async def _get_current_appraisal(
    session: AsyncSession,
    employee_id,
) -> ESSPerformanceGoalListResponse:
    service = PerformanceService(session)
    appraisal = await service.get_current_employee_appraisal(employee_id)
    return ESSPerformanceGoalListResponse(appraisal=appraisal)


@router.get("/goals", response_model=ESSPerformanceGoalListResponse, response_model_by_alias=True)
async def get_current_goals(
    session: AsyncSession = Depends(get_ess_db_with_tenant),
    ess_context: ESSUserContext = Depends(get_current_ess_user),
):
    """Return the active appraisal packet for the authenticated employee."""
    return await _get_current_appraisal(session, ess_context.employee_id)


@router.get(
    "/self-appraisal",
    response_model=ESSPerformanceGoalListResponse,
    response_model_by_alias=True,
)
async def get_self_appraisal(
    session: AsyncSession = Depends(get_ess_db_with_tenant),
    ess_context: ESSUserContext = Depends(get_current_ess_user),
):
    """Return the employee's current self-appraisal packet."""
    return await _get_current_appraisal(session, ess_context.employee_id)


@router.post(
    "/self-appraisal",
    response_model=ESSPerformanceGoalListResponse,
    response_model_by_alias=True,
)
async def submit_self_appraisal(
    data: PerformanceSelfAppraisalSubmit,
    session: AsyncSession = Depends(get_ess_db_with_tenant),
    ess_context: ESSUserContext = Depends(get_current_ess_user),
):
    """Submit self-appraisal for the authenticated employee's active cycle."""
    service = PerformanceService(session)
    appraisal = await service.get_current_employee_appraisal(ess_context.employee_id)
    if not appraisal:
        raise BadRequestException(
            detail="No active appraisal is available for the current employee",
            error_code="ACTIVE_APPRAISAL_NOT_FOUND",
        )
    if appraisal.appraisal.status != "SELF_APPRAISAL":
        raise BadRequestException(
            detail="Current appraisal is not in self-appraisal stage",
            error_code="SELF_APPRAISAL_STAGE_INVALID",
        )
    detail = await service.submit_self_appraisal(
        cycle_id=appraisal.cycle.id,
        employee_id=ess_context.employee_id,
        data=data,
        updated_by=ess_context.ess_user_id,
    )
    await session.commit()
    return ESSPerformanceGoalListResponse(appraisal=detail)
