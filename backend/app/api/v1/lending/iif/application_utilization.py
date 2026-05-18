"""Per-application fund-utilization endpoints.

Pre-mounted under ``/applications`` — full paths are
``/applications/{application_id}/utilization``,
``/applications/{application_id}/utilization/{line_id}``, and
``/applications/{application_id}/utilization/approved``.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_current_user, get_db_with_tenant
from app.core.exceptions import BadRequestException
from app.models.auth.user import User
from app.schemas.base import MessageResponse
from app.schemas.lending.iif import (
    ApplicationUtilizationBulkReplace,
    ApplicationUtilizationListResponse,
    ApplicationUtilizationResponse,
    ApprovedBreakdownRequest,
)
from app.services.lending.iif import LoanUtilizationService
from app.services.lending.iif.loan_utilization_service import (
    UtilizationListResult,
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


def _to_response(
    result: UtilizationListResult,
) -> ApplicationUtilizationListResponse:
    """Map service result to the camelCase response model."""
    difference = (
        (result.total_amount - result.requested_amount)
        if result.requested_amount is not None
        else None
    )
    approved_difference = None
    if result.total_approved_amount is not None and result.sanctioned_amount is not None:
        approved_difference = result.total_approved_amount - result.sanctioned_amount
    return ApplicationUtilizationListResponse(
        items=[ApplicationUtilizationResponse.model_validate(r) for r in result.rows],
        total_amount=result.total_amount,
        requested_amount=result.requested_amount,
        difference=difference,
        balanced=result.balanced,
        total_approved_amount=result.total_approved_amount,
        sanctioned_amount=result.sanctioned_amount,
        approved_difference=approved_difference,
        approved_balanced=result.approved_balanced,
    )


@router.get(
    "/{application_id}/utilization",
    response_model=ApplicationUtilizationListResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def list_application_utilization(
    application_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> ApplicationUtilizationListResponse:
    org_id = _require_org(current_user)
    service = LoanUtilizationService(db)
    result = await service.list_for_application(org_id, application_id)
    return _to_response(result)


@router.post(
    "/{application_id}/utilization",
    response_model=ApplicationUtilizationListResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def bulk_replace_application_utilization(
    application_id: UUID,
    data: ApplicationUtilizationBulkReplace,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> ApplicationUtilizationListResponse:
    _require_idempotency_key(idempotency_key)
    org_id = _require_org(current_user)
    async with db.begin():
        service = LoanUtilizationService(db)
        result = await service.bulk_replace(org_id, application_id, data, current_user)
    return _to_response(result)


@router.post(
    "/{application_id}/utilization/approved",
    response_model=ApplicationUtilizationListResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def submit_approved_breakdown(
    application_id: UUID,
    data: ApprovedBreakdownRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> ApplicationUtilizationListResponse:
    """Submit the lender-approved per-category breakdown.

    Updates only ``approved_amount`` on existing lines; the borrower's
    requested split (``amount``) is left untouched. Sum must equal the
    application's active sanction's ``sanctioned_amount`` (±0.01).
    """
    _require_idempotency_key(idempotency_key)
    org_id = _require_org(current_user)
    async with db.begin():
        service = LoanUtilizationService(db)
        result = await service.submit_approved_breakdown(org_id, application_id, data, current_user)
    return _to_response(result)


@router.delete(
    "/{application_id}/utilization/{line_id}",
    response_model=MessageResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def delete_application_utilization_line(
    application_id: UUID,
    line_id: UUID,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    _require_idempotency_key(idempotency_key)
    org_id = _require_org(current_user)
    async with db.begin():
        service = LoanUtilizationService(db)
        await service.delete_line(org_id, application_id, line_id, current_user)
    return MessageResponse(message="Utilization line deleted")
