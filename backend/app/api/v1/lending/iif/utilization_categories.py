"""Fund-utilization category endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_current_user, get_db_with_tenant
from app.core.exceptions import BadRequestException
from app.models.auth.user import User
from app.schemas.base import MessageResponse
from app.schemas.lending.iif import (
    FundUtilizationCategoryCreate,
    FundUtilizationCategoryListResponse,
    FundUtilizationCategoryResponse,
    FundUtilizationCategoryUpdate,
)
from app.services.lending.iif import FundUtilizationCategoryService

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
    response_model=FundUtilizationCategoryListResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def list_categories(
    scheme_id: UUID | None = Query(None),
    include_inactive: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=200),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> FundUtilizationCategoryListResponse:
    org_id = _require_org(current_user)
    skip = (page - 1) * page_size
    service = FundUtilizationCategoryService(db)
    items, total = await service.list_categories(
        organization_id=org_id,
        scheme_id=scheme_id,
        include_inactive=include_inactive,
        skip=skip,
        limit=page_size,
    )
    return FundUtilizationCategoryListResponse.create(
        [FundUtilizationCategoryResponse.model_validate(i) for i in items],
        total,
        page,
        page_size,
    )


@router.get(
    "/{category_id}",
    response_model=FundUtilizationCategoryResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def get_category(
    category_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> FundUtilizationCategoryResponse:
    org_id = _require_org(current_user)
    service = FundUtilizationCategoryService(db)
    cat = await service.get(org_id, category_id)
    return FundUtilizationCategoryResponse.model_validate(cat)


@router.post(
    "",
    response_model=FundUtilizationCategoryResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def create_category(
    data: FundUtilizationCategoryCreate,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> FundUtilizationCategoryResponse:
    _require_idempotency_key(idempotency_key)
    async with db.begin():
        service = FundUtilizationCategoryService(db)
        cat = await service.create(data, current_user)
    await db.refresh(cat)
    return FundUtilizationCategoryResponse.model_validate(cat)


@router.put(
    "/{category_id}",
    response_model=FundUtilizationCategoryResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def update_category(
    category_id: UUID,
    data: FundUtilizationCategoryUpdate,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> FundUtilizationCategoryResponse:
    _require_idempotency_key(idempotency_key)
    org_id = _require_org(current_user)
    async with db.begin():
        service = FundUtilizationCategoryService(db)
        cat = await service.update(org_id, category_id, data, current_user)
    await db.refresh(cat)
    return FundUtilizationCategoryResponse.model_validate(cat)


@router.delete(
    "/{category_id}",
    response_model=MessageResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def delete_category(
    category_id: UUID,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    _require_idempotency_key(idempotency_key)
    org_id = _require_org(current_user)
    async with db.begin():
        service = FundUtilizationCategoryService(db)
        await service.soft_delete(org_id, category_id, current_user)
    return MessageResponse(message="Category deleted")
