"""Approval-checklist endpoints.

Mounted under ``/api/v1/lending/checklist``. This router is intentionally
transactional only: per-loan checklist application and item lifecycle.
Checklist template master CRUD lives under ``/api/v1/lending/masters``.

All routes use ``get_db_with_tenant`` (RLS — CLAUDE.md §3.4), wire is
camelCase (``response_model_by_alias=True``), and every mutating
endpoint requires an ``Idempotency-Key`` header (CLAUDE.md §6.3).
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_current_user, get_db_with_tenant
from app.core.exceptions import BadRequestException
from app.models.auth.user import User
from app.schemas.lending.approval_checklist import (
    ApplyTemplateRequest,
    LoanChecklistItemResponse,
    LoanChecklistItemUpdate,
    LoanChecklistResponse,
    MarkMetRequest,
    MarkNotApplicableRequest,
    WaiveRequest,
)
from app.services.lending.checklist import (
    LoanChecklistService,
)

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


# =============================================================================
# Per-loan checklist
# =============================================================================


@router.get(
    "/applications/{application_id}/checklist",
    response_model=LoanChecklistResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def get_application_checklist(
    application_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> LoanChecklistResponse:
    org_id = _require_org(current_user)
    service = LoanChecklistService(db)
    checklist = await service.get_for_application(org_id, application_id)
    return LoanChecklistResponse.model_validate(checklist)


@router.post(
    "/applications/{application_id}/checklist/apply",
    response_model=LoanChecklistResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def apply_checklist_template(
    application_id: UUID,
    data: ApplyTemplateRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> LoanChecklistResponse:
    _require_idempotency_key(idempotency_key)
    org_id = _require_org(current_user)
    async with db.begin():
        service = LoanChecklistService(db)
        checklist = await service.apply_template_to_application(
            organization_id=org_id,
            template_id=data.template_id,
            application_id=application_id,
            due_date_anchor=data.due_date_anchor,
            current_user=current_user,
        )
    await db.refresh(checklist, attribute_names=["items"])
    return LoanChecklistResponse.model_validate(checklist)


@router.post(
    "/applications/{application_id}/checklist/replace",
    response_model=LoanChecklistResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def replace_checklist_template(
    application_id: UUID,
    data: ApplyTemplateRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> LoanChecklistResponse:
    _require_idempotency_key(idempotency_key)
    org_id = _require_org(current_user)
    async with db.begin():
        service = LoanChecklistService(db)
        checklist = await service.replace_template_for_application(
            organization_id=org_id,
            template_id=data.template_id,
            application_id=application_id,
            due_date_anchor=data.due_date_anchor,
            current_user=current_user,
        )
    await db.refresh(checklist, attribute_names=["items"])
    return LoanChecklistResponse.model_validate(checklist)


@router.put(
    "/applications/{application_id}/checklist/items/{item_id}",
    response_model=LoanChecklistItemResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def update_checklist_item(
    application_id: UUID,
    item_id: UUID,
    data: LoanChecklistItemUpdate,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> LoanChecklistItemResponse:
    _require_idempotency_key(idempotency_key)
    org_id = _require_org(current_user)
    async with db.begin():
        service = LoanChecklistService(db)
        item = await service.update_item(org_id, application_id, item_id, data, current_user)
    await db.refresh(item)
    return LoanChecklistItemResponse.model_validate(item)


@router.post(
    "/applications/{application_id}/checklist/items/{item_id}/mark-met",
    response_model=LoanChecklistItemResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def mark_checklist_item_met(
    application_id: UUID,
    item_id: UUID,
    data: MarkMetRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> LoanChecklistItemResponse:
    _require_idempotency_key(idempotency_key)
    org_id = _require_org(current_user)
    async with db.begin():
        service = LoanChecklistService(db)
        item = await service.mark_met(org_id, application_id, item_id, data, current_user)
    await db.refresh(item)
    return LoanChecklistItemResponse.model_validate(item)


@router.post(
    "/applications/{application_id}/checklist/items/{item_id}/waive",
    response_model=LoanChecklistItemResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def waive_checklist_item(
    application_id: UUID,
    item_id: UUID,
    data: WaiveRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> LoanChecklistItemResponse:
    _require_idempotency_key(idempotency_key)
    org_id = _require_org(current_user)
    async with db.begin():
        service = LoanChecklistService(db)
        item = await service.waive(org_id, application_id, item_id, data, current_user)
    await db.refresh(item)
    return LoanChecklistItemResponse.model_validate(item)


@router.post(
    "/applications/{application_id}/checklist/items/{item_id}/mark-not-applicable",
    response_model=LoanChecklistItemResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def mark_checklist_item_not_applicable(
    application_id: UUID,
    item_id: UUID,
    data: MarkNotApplicableRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> LoanChecklistItemResponse:
    _require_idempotency_key(idempotency_key)
    org_id = _require_org(current_user)
    async with db.begin():
        service = LoanChecklistService(db)
        item = await service.mark_not_applicable(
            org_id, application_id, item_id, data, current_user
        )
    await db.refresh(item)
    return LoanChecklistItemResponse.model_validate(item)


@router.post(
    "/applications/{application_id}/checklist/items/{item_id}/reset",
    response_model=LoanChecklistItemResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def reset_checklist_item(
    application_id: UUID,
    item_id: UUID,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> LoanChecklistItemResponse:
    _require_idempotency_key(idempotency_key)
    org_id = _require_org(current_user)
    async with db.begin():
        service = LoanChecklistService(db)
        item = await service.reset_item(org_id, application_id, item_id, current_user)
    await db.refresh(item)
    return LoanChecklistItemResponse.model_validate(item)
