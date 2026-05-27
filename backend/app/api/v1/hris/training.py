"""API endpoints for HRIS training programs."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_current_user, get_db_with_tenant
from app.core.constants import Permissions
from app.core.exceptions import BadRequestException, NotFoundException
from app.models.auth.user import User
from app.schemas.hris.training import (
    TrainingAvailableEmployeeResponse,
    TrainingFeedbackBundleResponse,
    TrainingFeedbackCreate,
    TrainingNominationBulkCreate,
    TrainingNominationResponse,
    TrainingNominationStatusUpdate,
    TrainingProgramCreate,
    TrainingProgramFilters,
    TrainingProgramListBundleResponse,
    TrainingProgramResponse,
    TrainingProgramUpdate,
)
from app.services.hris.training_service import TrainingService

router = APIRouter()


def _require_organization_id(current_user: User) -> UUID:
    if not current_user.organization_id:
        raise BadRequestException(
            detail="Current user is not assigned to an organization",
            error_code="ORGANIZATION_CONTEXT_REQUIRED",
        )
    return current_user.organization_id


@router.get(
    "/training/programs",
    response_model=TrainingProgramListBundleResponse,
    response_model_by_alias=True,
)
async def list_training_programs(
    category: Optional[str] = None,
    mode: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_TRAINING_VIEW)),
):
    """List training programs for the active organization."""
    service = TrainingService(db)
    filters = TrainingProgramFilters(
        organization_id=_require_organization_id(current_user),
        category=category,
        mode=mode,
        status=status_filter,
        search=search,
    )
    items, total, summary = await service.list_programs(filters, skip, limit)
    return TrainingProgramListBundleResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
        summary=summary,
    )


@router.post(
    "/training/programs",
    response_model=TrainingProgramResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
async def create_training_program(
    data: TrainingProgramCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_TRAINING_CREATE)),
):
    """Create a new training program."""
    payload = data.model_copy(update={"organization_id": _require_organization_id(current_user)})
    service = TrainingService(db)
    program = await service.create_program(payload, current_user.id)
    await db.commit()
    hydrated_program = await service.get_program(program.id)
    if not hydrated_program:
        raise NotFoundException(
            detail="Training program not found after creation",
            error_code="TRAINING_PROGRAM_NOT_FOUND",
        )
    return service._program_response(hydrated_program)


@router.get(
    "/training/programs/{program_id}",
    response_model=TrainingProgramResponse,
    response_model_by_alias=True,
)
async def get_training_program(
    program_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_TRAINING_VIEW)),
):
    """Get a training program by ID."""
    service = TrainingService(db)
    program = await service.get_program(program_id)
    if not program:
        raise NotFoundException(
            detail="Training program not found",
            error_code="TRAINING_PROGRAM_NOT_FOUND",
        )
    return service._program_response(program)


@router.put(
    "/training/programs/{program_id}",
    response_model=TrainingProgramResponse,
    response_model_by_alias=True,
)
async def update_training_program(
    program_id: UUID,
    data: TrainingProgramUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_TRAINING_UPDATE)),
):
    """Update a training program."""
    service = TrainingService(db)
    program = await service.update_program(program_id, data, current_user.id)
    if not program:
        raise NotFoundException(
            detail="Training program not found",
            error_code="TRAINING_PROGRAM_NOT_FOUND",
        )
    await db.commit()
    hydrated_program = await service.get_program(program.id)
    if not hydrated_program:
        raise NotFoundException(
            detail="Training program not found after update",
            error_code="TRAINING_PROGRAM_NOT_FOUND",
        )
    return service._program_response(hydrated_program)


@router.get(
    "/training/programs/{program_id}/available-employees",
    response_model=list[TrainingAvailableEmployeeResponse],
    response_model_by_alias=True,
)
async def list_available_training_employees(
    program_id: UUID,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_TRAINING_NOMINATE)),
):
    """List active employees that are not yet nominated for the program."""
    service = TrainingService(db)
    return await service.list_available_employees(
        _require_organization_id(current_user),
        program_id,
        search,
    )


@router.get(
    "/training/programs/{program_id}/nominations",
    response_model=list[TrainingNominationResponse],
    response_model_by_alias=True,
)
async def list_training_nominations(
    program_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_TRAINING_VIEW)),
):
    """List nominations for a training program."""
    service = TrainingService(db)
    return await service.list_nominations(program_id)


@router.post(
    "/training/programs/{program_id}/nominations",
    response_model=list[TrainingNominationResponse],
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
async def add_training_nominations(
    program_id: UUID,
    data: TrainingNominationBulkCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_TRAINING_NOMINATE)),
):
    """Nominate one or more employees to a training program."""
    service = TrainingService(db)
    nominations = await service.add_nominations(program_id, data.employee_ids, current_user.id)
    await db.commit()
    return nominations


@router.patch(
    "/training/programs/{program_id}/nominations/{nomination_id}",
    response_model=TrainingNominationResponse,
    response_model_by_alias=True,
)
async def update_training_nomination(
    program_id: UUID,
    nomination_id: UUID,
    data: TrainingNominationStatusUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(
        RequirePermissions(
            Permissions.HRIS_TRAINING_APPROVE,
            Permissions.HRIS_TRAINING_NOMINATE,
            require_all=False,
        )
    ),
):
    """Update nomination status or attendance."""
    service = TrainingService(db)
    nomination = await service.update_nomination_status(
        program_id,
        nomination_id,
        data.status,
        current_user.id,
        data.attendance_marked,
    )
    if not nomination:
        raise NotFoundException(
            detail="Training nomination not found",
            error_code="TRAINING_NOMINATION_NOT_FOUND",
        )
    await db.commit()
    return nomination


@router.get(
    "/training/programs/{program_id}/feedback",
    response_model=TrainingFeedbackBundleResponse,
    response_model_by_alias=True,
)
async def get_training_feedback(
    program_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_TRAINING_FEEDBACK)),
):
    """Get feedback summary and individual responses for a training program."""
    service = TrainingService(db)
    bundle = await service.get_feedback_bundle(program_id)
    if not bundle:
        raise NotFoundException(
            detail="Training program not found",
            error_code="TRAINING_PROGRAM_NOT_FOUND",
        )
    return bundle


@router.post(
    "/training/programs/{program_id}/feedback",
    response_model=TrainingFeedbackBundleResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
async def record_training_feedback(
    program_id: UUID,
    data: TrainingFeedbackCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(RequirePermissions(Permissions.HRIS_TRAINING_FEEDBACK)),
):
    """Create or update manual feedback for a nominated employee."""
    service = TrainingService(db)
    bundle = await service.upsert_feedback(program_id, data, current_user.id)
    await db.commit()
    return bundle
