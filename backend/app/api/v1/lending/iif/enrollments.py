"""Loan ↔ scheme enrollment endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_current_user, get_db_with_tenant
from app.core.exceptions import BadRequestException
from app.models.auth.user import User
from app.schemas.lending.iif import (
    EligibilityCheckResponse,
    EnrollmentStatusActionRequest,
    LoanSubventionEnrollmentCreate,
    LoanSubventionEnrollmentListResponse,
    LoanSubventionEnrollmentResponse,
    LoanSubventionEnrollmentUpdate,
)
from app.services.lending.iif import SubventionEnrollmentService

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
    response_model=LoanSubventionEnrollmentListResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def list_enrollments(
    status_filter: str | None = Query(None, alias="status"),
    scheme_id: UUID | None = Query(None),
    loan_account_id: UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> LoanSubventionEnrollmentListResponse:
    org_id = _require_org(current_user)
    skip = (page - 1) * page_size
    service = SubventionEnrollmentService(db)
    items, total = await service.list_enrollments(
        organization_id=org_id,
        status=status_filter,
        scheme_id=scheme_id,
        loan_account_id=loan_account_id,
        skip=skip,
        limit=page_size,
    )
    return LoanSubventionEnrollmentListResponse.create(
        [LoanSubventionEnrollmentResponse.model_validate(e) for e in items],
        total,
        page,
        page_size,
    )


@router.get(
    "/{enrollment_id}",
    response_model=LoanSubventionEnrollmentResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def get_enrollment(
    enrollment_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> LoanSubventionEnrollmentResponse:
    org_id = _require_org(current_user)
    service = SubventionEnrollmentService(db)
    enrollment = await service.get(org_id, enrollment_id)
    return LoanSubventionEnrollmentResponse.model_validate(enrollment)


@router.get(
    "/{enrollment_id}/eligibility-check",
    response_model=EligibilityCheckResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def check_enrollment_eligibility(
    enrollment_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> EligibilityCheckResponse:
    """Re-evaluate eligibility for an existing enrollment."""
    org_id = _require_org(current_user)
    service = SubventionEnrollmentService(db)
    enrollment = await service.get(org_id, enrollment_id, with_relations=False)
    return await service.check_eligibility(org_id, enrollment.loan_account_id, enrollment.scheme_id)


@router.post(
    "",
    response_model=LoanSubventionEnrollmentResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def create_enrollment(
    data: LoanSubventionEnrollmentCreate,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> LoanSubventionEnrollmentResponse:
    _require_idempotency_key(idempotency_key)
    org_id = _require_org(current_user)
    async with db.begin():
        service = SubventionEnrollmentService(db)
        enrollment = await service.create(org_id, data, current_user)
    # Re-fetch with relations for the response.
    async with db.begin():
        service = SubventionEnrollmentService(db)
        enrollment = await service.get(org_id, enrollment.id)
    return LoanSubventionEnrollmentResponse.model_validate(enrollment)


@router.put(
    "/{enrollment_id}",
    response_model=LoanSubventionEnrollmentResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def update_enrollment(
    enrollment_id: UUID,
    data: LoanSubventionEnrollmentUpdate,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> LoanSubventionEnrollmentResponse:
    _require_idempotency_key(idempotency_key)
    org_id = _require_org(current_user)
    async with db.begin():
        service = SubventionEnrollmentService(db)
        await service.update(org_id, enrollment_id, data, current_user)
    async with db.begin():
        service = SubventionEnrollmentService(db)
        enrollment = await service.get(org_id, enrollment_id)
    return LoanSubventionEnrollmentResponse.model_validate(enrollment)


@router.post(
    "/{enrollment_id}/approve",
    response_model=LoanSubventionEnrollmentResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def approve_enrollment(
    enrollment_id: UUID,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> LoanSubventionEnrollmentResponse:
    _require_idempotency_key(idempotency_key)
    org_id = _require_org(current_user)
    async with db.begin():
        service = SubventionEnrollmentService(db)
        await service.approve(org_id, enrollment_id, current_user)
    async with db.begin():
        service = SubventionEnrollmentService(db)
        enrollment = await service.get(org_id, enrollment_id)
    return LoanSubventionEnrollmentResponse.model_validate(enrollment)


@router.post(
    "/{enrollment_id}/reject",
    response_model=LoanSubventionEnrollmentResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def reject_enrollment(
    enrollment_id: UUID,
    data: EnrollmentStatusActionRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> LoanSubventionEnrollmentResponse:
    _require_idempotency_key(idempotency_key)
    org_id = _require_org(current_user)
    async with db.begin():
        service = SubventionEnrollmentService(db)
        await service.reject(org_id, enrollment_id, data.reason, current_user)
    async with db.begin():
        service = SubventionEnrollmentService(db)
        enrollment = await service.get(org_id, enrollment_id)
    return LoanSubventionEnrollmentResponse.model_validate(enrollment)


@router.post(
    "/{enrollment_id}/suspend",
    response_model=LoanSubventionEnrollmentResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def suspend_enrollment(
    enrollment_id: UUID,
    data: EnrollmentStatusActionRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> LoanSubventionEnrollmentResponse:
    _require_idempotency_key(idempotency_key)
    org_id = _require_org(current_user)
    async with db.begin():
        service = SubventionEnrollmentService(db)
        await service.suspend(org_id, enrollment_id, data.reason, current_user)
    async with db.begin():
        service = SubventionEnrollmentService(db)
        enrollment = await service.get(org_id, enrollment_id)
    return LoanSubventionEnrollmentResponse.model_validate(enrollment)


@router.post(
    "/{enrollment_id}/reinstate",
    response_model=LoanSubventionEnrollmentResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def reinstate_enrollment(
    enrollment_id: UUID,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> LoanSubventionEnrollmentResponse:
    _require_idempotency_key(idempotency_key)
    org_id = _require_org(current_user)
    async with db.begin():
        service = SubventionEnrollmentService(db)
        await service.reinstate(org_id, enrollment_id, current_user)
    async with db.begin():
        service = SubventionEnrollmentService(db)
        enrollment = await service.get(org_id, enrollment_id)
    return LoanSubventionEnrollmentResponse.model_validate(enrollment)
