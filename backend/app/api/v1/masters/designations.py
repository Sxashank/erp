"""Designation API endpoints."""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user, RequirePermissions
from app.models.auth.user import User
from app.services.masters.designation_service import DesignationService
from app.schemas.masters.designation import (
    DesignationCreate,
    DesignationUpdate,
    DesignationResponse,
)
from app.schemas.base import PaginatedResponse, MessageResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse[DesignationResponse])
async def list_designations(
    department_id: Optional[UUID] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    include_inactive: bool = Query(False),
    current_user: User = Depends(RequirePermissions("MASTER_DESIG_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """
    Get paginated list of designations.
    Requires MASTER_DESIG_VIEW permission.
    """
    desig_service = DesignationService(db)
    skip = (page - 1) * page_size
    desigs, total = await desig_service.get_all(department_id, skip, page_size, include_inactive)

    items = [_desig_to_response(d) for d in desigs]

    return PaginatedResponse.create(items, total, page, page_size)


@router.post("", response_model=DesignationResponse)
async def create_designation(
    data: DesignationCreate,
    current_user: User = Depends(RequirePermissions("MASTER_DESIG_CREATE")),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new designation.
    Requires MASTER_DESIG_CREATE permission.
    """
    desig_service = DesignationService(db)
    desig = await desig_service.create(data, current_user.id)

    return _desig_to_response(desig)


@router.get("/{desig_id}", response_model=DesignationResponse)
async def get_designation(
    desig_id: UUID,
    current_user: User = Depends(RequirePermissions("MASTER_DESIG_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """
    Get designation by ID.
    Requires MASTER_DESIG_VIEW permission.
    """
    desig_service = DesignationService(db)
    desig = await desig_service.get(desig_id)

    return _desig_to_response(desig)


@router.put("/{desig_id}", response_model=DesignationResponse)
async def update_designation(
    desig_id: UUID,
    data: DesignationUpdate,
    current_user: User = Depends(RequirePermissions("MASTER_DESIG_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """
    Update an existing designation.
    Requires MASTER_DESIG_UPDATE permission.
    """
    desig_service = DesignationService(db)
    desig = await desig_service.update(desig_id, data, current_user.id)

    return _desig_to_response(desig)


@router.delete("/{desig_id}", response_model=MessageResponse)
async def delete_designation(
    desig_id: UUID,
    current_user: User = Depends(RequirePermissions("MASTER_DESIG_DELETE")),
    db: AsyncSession = Depends(get_db),
):
    """
    Soft delete a designation.
    Requires MASTER_DESIG_DELETE permission.
    """
    desig_service = DesignationService(db)
    await desig_service.delete(desig_id, current_user.id)

    return MessageResponse(message="Designation deleted successfully")


@router.get("/{desig_id}/reports", response_model=List[DesignationResponse])
async def get_designation_reports(
    desig_id: UUID,
    current_user: User = Depends(RequirePermissions("MASTER_DESIG_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """
    Get designations that report to this designation.
    Requires MASTER_DESIG_VIEW permission.
    """
    desig_service = DesignationService(db)
    reports = await desig_service.get_reports(desig_id)

    return [_desig_to_response(d) for d in reports]


@router.get("/{desig_id}/hierarchy", response_model=List[DesignationResponse])
async def get_designation_hierarchy(
    desig_id: UUID,
    current_user: User = Depends(RequirePermissions("MASTER_DESIG_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """
    Get reporting hierarchy for a designation.
    Requires MASTER_DESIG_VIEW permission.
    """
    desig_service = DesignationService(db)
    hierarchy = await desig_service.get_hierarchy(desig_id)

    return [_desig_to_response(d) for d in hierarchy]


def _desig_to_response(desig) -> DesignationResponse:
    """Convert Designation model to DesignationResponse."""
    return DesignationResponse(
        id=desig.id,
        code=desig.code,
        name=desig.name,
        short_name=desig.short_name,
        description=desig.description,
        department_id=desig.department_id,
        level=desig.level,
        reporting_to_id=desig.reporting_to_id,
        min_experience_years=desig.min_experience_years,
        min_qualification=desig.min_qualification,
        job_description=desig.job_description,
        responsibilities=desig.responsibilities,
        status=desig.status,
        created_at=desig.created_at,
        updated_at=desig.updated_at,
        is_active=desig.is_active,
        department_name=desig.department.name if desig.department else None,
        reporting_to_name=desig.reporting_to.name if desig.reporting_to else None,
    )
