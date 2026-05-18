"""Admin endpoints for reviewing borrower-portal registrations.

Mounted under ``/api/v1/admin/portal-registrations``. Auth: an
``mst_user`` with ``treasury:read`` permission (CLAUDE.md §8.2 — we
reuse an existing permission rather than minting a new one for this
pass; tighten in a follow-up if the admin UX warrants it).

Cross-tenant rule (CLAUDE.md §3.4): the list is *platform-wide* for
the pending queue (registrations don't yet belong to any tenant), but
``approve`` validates every supplied ``entity_id`` belongs to the
admin's organisation, so a curious admin cannot link a borrower to a
different tenant's entity.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_current_user, get_db_with_tenant
from app.core.exceptions import BadRequestException
from app.models.auth.user import User
from app.models.portal.enums import PortalRegistrationStatus
from app.schemas.portal.registration import (
    AdminRegistrationDetail,
    AdminRegistrationListResponse,
    ApproveRequest,
    RejectRequest,
)
from app.services.portal.registration_service import PortalRegistrationService

router = APIRouter(
    prefix="/portal-registrations",
    tags=["Admin · Borrower Portal Registrations"],
)


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
    response_model=AdminRegistrationListResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
    summary="List borrower-portal registrations",
)
async def list_registrations(
    status: PortalRegistrationStatus | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200, alias="pageSize"),
    db: AsyncSession = Depends(get_db_with_tenant),
) -> AdminRegistrationListResponse:
    """Platform-wide list. Approve-time enforces tenant scope."""
    service = PortalRegistrationService(db)
    return await service.admin_list(
        status=status,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{portal_user_id}",
    response_model=AdminRegistrationDetail,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
    summary="Get a single registration with same-org entity suggestions",
)
async def get_registration(
    portal_user_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> AdminRegistrationDetail:
    org_id = _require_org(current_user)
    service = PortalRegistrationService(db)
    return await service.admin_get(portal_user_id, org_id)


@router.post(
    "/{portal_user_id}/approve",
    response_model=AdminRegistrationDetail,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
    summary="Approve a registration and link it to one or more entities",
)
async def approve_registration(
    portal_user_id: UUID,
    payload: ApproveRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> AdminRegistrationDetail:
    """Approve and create ``mst_portal_user_entity`` links.

    Validates every ``entity_id`` belongs to the admin's organisation
    (400 ``ENTITY_CROSS_TENANT`` otherwise).
    """
    _require_idempotency_key(idempotency_key)
    org_id = _require_org(current_user)
    service = PortalRegistrationService(db)
    result = await service.admin_approve(
        portal_user_id=portal_user_id,
        entity_ids=payload.entity_ids,
        current_user_id=current_user.id,
        current_user_org_id=org_id,
    )
    await db.commit()
    return result


@router.post(
    "/{portal_user_id}/reject",
    response_model=AdminRegistrationDetail,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
    summary="Reject a registration with a reason",
)
async def reject_registration(
    portal_user_id: UUID,
    payload: RejectRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> AdminRegistrationDetail:
    _require_idempotency_key(idempotency_key)
    org_id = _require_org(current_user)
    service = PortalRegistrationService(db)
    result = await service.admin_reject(
        portal_user_id=portal_user_id,
        reason=payload.reason,
        current_user_id=current_user.id,
        current_user_org_id=org_id,
    )
    await db.commit()
    return result
