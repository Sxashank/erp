"""Admin endpoints for integrated scheme-portal users."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_current_user, get_db_with_tenant
from app.core.exceptions import AppException, BadRequestException
from app.models.auth.user import User
from app.schemas.portal.admin_user import (
    AdminPortalInviteResponse,
    AdminPortalUserCreateRequest,
    AdminPortalUserDetail,
    AdminPortalUserListResponse,
    AdminPortalUserUpdateRequest,
)
from app.services.portal.admin_user_service import PortalAdminUserService

router = APIRouter(
    prefix="/portal-users",
    tags=["Admin · Scheme Portal Users"],
)


def _require_org(user: User) -> UUID:
    if user.organization_id is None:
        raise BadRequestException(
            "Current user has no organization context",
            error_code="MISSING_ORG_CONTEXT",
        )
    return user.organization_id


@router.get(
    "",
    response_model=AdminPortalUserListResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
    summary="List scheme-portal users in the current tenant",
)
async def list_portal_users(
    actor_role: str | None = Query(None, alias="actorRole"),
    status: str | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200, alias="pageSize"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> AdminPortalUserListResponse:
    service = PortalAdminUserService(db)
    return await service.list_users(
        organization_id=_require_org(current_user),
        actor_role=actor_role,
        status=status,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{portal_user_id}",
    response_model=AdminPortalUserDetail,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
    summary="Get one scheme-portal user",
)
async def get_portal_user_detail(
    portal_user_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> AdminPortalUserDetail:
    service = PortalAdminUserService(db)
    return await service.get_user(
        organization_id=_require_org(current_user),
        portal_user_id=portal_user_id,
    )


@router.post(
    "",
    response_model=AdminPortalUserDetail,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
    summary="Create a scheme-portal user for the current tenant",
)
async def create_portal_user(
    payload: AdminPortalUserCreateRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> AdminPortalUserDetail:
    service = PortalAdminUserService(db)
    result = await service.create_user(
        organization_id=_require_org(current_user),
        current_user_id=current_user.id,
        payload=payload,
    )
    await db.commit()
    return result


@router.patch(
    "/{portal_user_id}",
    response_model=AdminPortalUserDetail,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
    summary="Update a scheme-portal user",
)
async def update_portal_user(
    portal_user_id: UUID,
    payload: AdminPortalUserUpdateRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> AdminPortalUserDetail:
    service = PortalAdminUserService(db)
    result = await service.update_user(
        organization_id=_require_org(current_user),
        current_user_id=current_user.id,
        portal_user_id=portal_user_id,
        payload=payload,
    )
    await db.commit()
    return result


@router.post(
    "/{portal_user_id}/invite",
    response_model=AdminPortalInviteResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
    summary="Issue or rotate an activation invite for an internal scheme-portal user",
)
async def invite_portal_user(
    portal_user_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> AdminPortalInviteResponse:
    service = PortalAdminUserService(db)
    try:
        result = await service.issue_invite(
            organization_id=_require_org(current_user),
            current_user_id=current_user.id,
            portal_user_id=portal_user_id,
        )
    except ValueError as exc:
        status_code = (
            status.HTTP_503_SERVICE_UNAVAILABLE
            if "Email delivery" in str(exc)
            else status.HTTP_400_BAD_REQUEST
        )
        raise AppException(
            status_code=status_code,
            detail=str(exc),
            error_code="UPSTREAM_ERROR",
        ) from exc
    await db.commit()
    return result
