"""Fixed Assets Configuration API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.exceptions import NotFoundException
from app.schemas.fixed_assets.fa_config import (
    FAConfigurationCreate,
    FAConfigurationUpdate,
    FAConfigurationResponse,
)
from app.services.fixed_assets.fa_config_service import FAConfigurationService

router = APIRouter(prefix="/config", tags=["FA Configuration"])


def get_fa_config_service(
    session: Annotated[AsyncSession, Depends(get_db)],
) -> FAConfigurationService:
    """Get FA configuration service instance."""
    return FAConfigurationService(session)


@router.get(
    "/{organization_id}",
    response_model=FAConfigurationResponse,
    summary="Get FA configuration for organization",
)
async def get_configuration(
    organization_id: UUID,
    service: Annotated[FAConfigurationService, Depends(get_fa_config_service)],
) -> FAConfigurationResponse:
    """
    Get Fixed Assets configuration for an organization.

    Returns the active configuration or raises 404 if not found.
    """
    config = await service.get_by_organization(organization_id)
    if not config:
        raise NotFoundException(
            f"FA configuration not found for organization {organization_id}"
        )
    return config


@router.get(
    "/{organization_id}/default",
    response_model=FAConfigurationResponse,
    summary="Get or create default FA configuration",
)
async def get_or_create_default_configuration(
    organization_id: UUID,
    service: Annotated[FAConfigurationService, Depends(get_fa_config_service)],
    # current_user: Annotated[User, Depends(get_current_user)],
) -> FAConfigurationResponse:
    """
    Get FA configuration for an organization, creating default if not exists.

    This endpoint is useful for ensuring a configuration exists before
    performing operations that depend on it.
    """
    config = await service.get_or_create_default(
        organization_id=organization_id,
        created_by=None,  # Replace with current_user.id when auth is integrated
    )
    return config


@router.post(
    "",
    response_model=FAConfigurationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create FA configuration",
)
async def create_configuration(
    data: FAConfigurationCreate,
    service: Annotated[FAConfigurationService, Depends(get_fa_config_service)],
    # current_user: Annotated[User, Depends(get_current_user)],
) -> FAConfigurationResponse:
    """
    Create Fixed Assets configuration for an organization.

    Only one active configuration can exist per organization.
    """
    config = await service.create(
        data=data,
        created_by=None,  # Replace with current_user.id when auth is integrated
    )
    return config


@router.put(
    "/{organization_id}",
    response_model=FAConfigurationResponse,
    summary="Update FA configuration",
)
async def update_configuration(
    organization_id: UUID,
    data: FAConfigurationUpdate,
    service: Annotated[FAConfigurationService, Depends(get_fa_config_service)],
    # current_user: Annotated[User, Depends(get_current_user)],
) -> FAConfigurationResponse:
    """
    Update Fixed Assets configuration for an organization.

    Only fields provided in the request body will be updated.
    """
    config = await service.update(
        organization_id=organization_id,
        data=data,
        updated_by=None,  # Replace with current_user.id when auth is integrated
    )
    return config


@router.delete(
    "/{organization_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete FA configuration",
)
async def delete_configuration(
    organization_id: UUID,
    service: Annotated[FAConfigurationService, Depends(get_fa_config_service)],
    # current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    """
    Soft delete Fixed Assets configuration for an organization.

    The configuration can be recreated after deletion.
    """
    deleted = await service.delete(
        organization_id=organization_id,
        deleted_by=None,  # Replace with current_user.id when auth is integrated
    )
    if not deleted:
        raise NotFoundException(
            f"FA configuration not found for organization {organization_id}"
        )
