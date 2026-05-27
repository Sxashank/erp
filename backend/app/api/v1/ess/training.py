"""ESS training API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ESSUserContext, get_current_ess_user, get_ess_db_with_tenant
from app.schemas.ess.operations import ESSTrainingDetailResponse, ESSTrainingListResponse
from app.services.ess.training_service import ESSTrainingService

router = APIRouter(prefix="/training", tags=["ESS Training"])


@router.get("", response_model=ESSTrainingListResponse, response_model_by_alias=True)
async def list_training_programs(
    session: AsyncSession = Depends(get_ess_db_with_tenant),
    ess_context: ESSUserContext = Depends(get_current_ess_user),
):
    """List employee training nominations and history."""
    service = ESSTrainingService(session)
    return await service.list_employee_training(ess_context.employee_id)


@router.get(
    "/{program_id}",
    response_model=ESSTrainingDetailResponse,
    response_model_by_alias=True,
)
async def get_training_program_detail(
    program_id: UUID,
    session: AsyncSession = Depends(get_ess_db_with_tenant),
    ess_context: ESSUserContext = Depends(get_current_ess_user),
):
    """Return detail for one employee-nominated training program."""
    service = ESSTrainingService(session)
    return await service.get_training_detail(ess_context.employee_id, program_id)
