"""Subvention scheme endpoints.

All authenticated routes use ``get_db_with_tenant`` so RLS is honoured
(CLAUDE.md §3.4). Wire is camelCase via ``response_model_by_alias=True``.

Mutating endpoints require an ``Idempotency-Key`` header per
CLAUDE.md §6.3.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_current_user, get_db_with_tenant
from app.core.exceptions import BadRequestException
from app.models.auth.user import User
from app.schemas.base import MessageResponse
from app.schemas.lending.iif import (
    SubventionSchemeCreate,
    SubventionSchemeListResponse,
    SubventionSchemeResponse,
    SubventionSchemeUpdate,
)
from app.services.lending.iif import SubventionSchemeService

router = APIRouter()


def _require_idempotency_key(key: str | None) -> None:
    if not key:
        raise BadRequestException(
            "Idempotency-Key header is required for this operation",
            error_code="IDEMPOTENCY_KEY_REQUIRED",
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
    response_model=SubventionSchemeListResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def list_schemes(
    include_inactive: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> SubventionSchemeListResponse:
    org_id = _require_org(current_user)
    skip = (page - 1) * page_size
    service = SubventionSchemeService(db)
    items, total = await service.list_schemes(
        organization_id=org_id,
        include_inactive=include_inactive,
        skip=skip,
        limit=page_size,
    )
    return SubventionSchemeListResponse.create(
        [SubventionSchemeResponse.model_validate(i) for i in items],
        total,
        page,
        page_size,
    )


@router.get(
    "/{scheme_id}",
    response_model=SubventionSchemeResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def get_scheme(
    scheme_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> SubventionSchemeResponse:
    org_id = _require_org(current_user)
    service = SubventionSchemeService(db)
    scheme = await service.get(org_id, scheme_id)
    return SubventionSchemeResponse.model_validate(scheme)


@router.post(
    "",
    response_model=SubventionSchemeResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def create_scheme(
    data: SubventionSchemeCreate,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> SubventionSchemeResponse:
    _require_idempotency_key(idempotency_key)
    async with db.begin():
        service = SubventionSchemeService(db)
        scheme = await service.create(data, current_user)
    await db.refresh(scheme)
    return SubventionSchemeResponse.model_validate(scheme)


@router.put(
    "/{scheme_id}",
    response_model=SubventionSchemeResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def update_scheme(
    scheme_id: UUID,
    data: SubventionSchemeUpdate,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> SubventionSchemeResponse:
    _require_idempotency_key(idempotency_key)
    org_id = _require_org(current_user)
    async with db.begin():
        service = SubventionSchemeService(db)
        scheme = await service.update(org_id, scheme_id, data, current_user)
    await db.refresh(scheme)
    return SubventionSchemeResponse.model_validate(scheme)


@router.delete(
    "/{scheme_id}",
    response_model=MessageResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def delete_scheme(
    scheme_id: UUID,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    _require_idempotency_key(idempotency_key)
    org_id = _require_org(current_user)
    async with db.begin():
        service = SubventionSchemeService(db)
        await service.soft_delete(org_id, scheme_id, current_user)
    return MessageResponse(message="Scheme deleted")
