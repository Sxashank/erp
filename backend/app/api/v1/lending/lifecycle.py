"""Lifecycle event + application-query API endpoints.

Two reader endpoints (timeline) + three mutator endpoints (raise / respond
/ resolve query) + one lister (list queries on an application).

All routes are tenant-scoped via ``get_db_with_tenant`` (CLAUDE.md §3.4)
and permission-gated.

Borrower-side mirrors live under ``/api/v1/portal/...`` and call the same
service with ``borrower_visible_only=True`` and the portal user id.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_current_user, get_db_with_tenant
from app.models.lending.lifecycle_event import LifecycleSubjectType
from app.schemas.lending.lifecycle import (
    ApplicationQueryListResponse,
    ApplicationQueryResponse,
    LifecycleEventResponse,
    LifecycleTimelineResponse,
    RaiseQueryRequest,
    ResolveQueryRequest,
    RespondToQueryRequest,
)
from app.services.lending.application_query_service import ApplicationQueryService
from app.services.lending.lifecycle_service import LifecycleService

router = APIRouter()


# ---------------------------------------------------------------------------
# Timeline reads (admin LMS)
# ---------------------------------------------------------------------------


@router.get(
    "/applications/{application_id}/lifecycle",
    response_model=LifecycleTimelineResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("LOS_READ"))],
)
async def get_application_lifecycle(
    application_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> LifecycleTimelineResponse:
    """All events on an application — query bounces, sanction, KFS, etc."""
    service = LifecycleService(db)
    rows = await service.list_for_subject(
        subject_type=LifecycleSubjectType.APPLICATION,
        subject_id=application_id,
        organization_id=current_user.organization_id,
    )
    items = [LifecycleEventResponse.model_validate(r) for r in rows]
    return LifecycleTimelineResponse(items=items, total=len(items))


@router.get(
    "/loan-accounts/{loan_account_id}/lifecycle",
    response_model=LifecycleTimelineResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("LMS_READ"))],
)
async def get_loan_account_lifecycle(
    loan_account_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> LifecycleTimelineResponse:
    """Aggregate timeline: application → sanction → loan account.

    Resolves the upstream application + sanction ids from the loan account
    so the whole story comes back in one query.
    """
    from app.models.lending.loan_account import LoanAccount

    loan = await db.get(LoanAccount, loan_account_id)
    application_id = getattr(loan, "application_id", None) if loan else None
    sanction_id = getattr(loan, "sanction_id", None) if loan else None

    service = LifecycleService(db)
    rows = await service.list_for_loan_account(
        loan_account_id=loan_account_id,
        organization_id=current_user.organization_id,
        application_id=application_id,
        sanction_id=sanction_id,
    )
    items = [LifecycleEventResponse.model_validate(r) for r in rows]
    return LifecycleTimelineResponse(items=items, total=len(items))


# ---------------------------------------------------------------------------
# Application queries (lender)
# ---------------------------------------------------------------------------


@router.get(
    "/applications/{application_id}/queries",
    response_model=ApplicationQueryListResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("LOS_READ"))],
)
async def list_application_queries(
    application_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> ApplicationQueryListResponse:
    service = ApplicationQueryService(db)
    rows = await service.list_for_application(
        organization_id=current_user.organization_id,
        application_id=application_id,
    )
    items = [ApplicationQueryResponse.model_validate(r) for r in rows]
    return ApplicationQueryListResponse(items=items, total=len(items))


@router.post(
    "/applications/{application_id}/queries",
    response_model=ApplicationQueryResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("LOS_WRITE"))],
)
async def raise_application_query(
    application_id: UUID,
    data: RaiseQueryRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> ApplicationQueryResponse:
    async with db.begin():
        service = ApplicationQueryService(db)
        query = await service.raise_query(
            organization_id=current_user.organization_id,
            application_id=application_id,
            raised_by_user_id=current_user.id,
            query_text=data.query_text,
            raised_reason_code=data.raised_reason_code,
            required_attachments=data.required_attachments,
            sla_hours=data.sla_hours,
        )
    await db.refresh(query)
    return ApplicationQueryResponse.model_validate(query)


@router.post(
    "/applications/{application_id}/queries/{query_id}/resolve",
    response_model=ApplicationQueryResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("LOS_WRITE"))],
)
async def resolve_application_query(
    application_id: UUID,  # noqa: ARG001 — kept on the path for REST clarity
    query_id: UUID,
    data: ResolveQueryRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> ApplicationQueryResponse:
    async with db.begin():
        service = ApplicationQueryService(db)
        query = await service.resolve_query(
            organization_id=current_user.organization_id,
            query_id=query_id,
            resolved_by_user_id=current_user.id,
            resolution_remark=data.resolution_remark,
            move_to_under_review=data.move_to_under_review,
        )
    await db.refresh(query)
    return ApplicationQueryResponse.model_validate(query)


# ---------------------------------------------------------------------------
# Application queries (borrower portal)
# ---------------------------------------------------------------------------
# The portal version of "respond" is registered on the portal router so it
# uses the portal auth dependency. Defined here for centralisation; mounted
# by app/api/v1/portal/router.py.


@router.post(
    "/applications/{application_id}/queries/{query_id}/respond",
    response_model=ApplicationQueryResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("LOS_WRITE"))],
)
async def respond_to_application_query_admin_only(
    application_id: UUID,  # noqa: ARG001
    query_id: UUID,
    data: RespondToQueryRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> ApplicationQueryResponse:
    """Admin-side respond — only used when ops needs to reply on the borrower's behalf.

    The borrower's own portal route is mounted under ``/portal/`` with the
    portal user dependency; see ``app/api/v1/portal/lifecycle.py``.
    """
    async with db.begin():
        service = ApplicationQueryService(db)
        query = await service.respond_to_query(
            organization_id=current_user.organization_id,
            query_id=query_id,
            portal_user_id=current_user.id,
            response_text=data.response_text,
            response_attachments=data.response_attachments,
        )
    await db.refresh(query)
    return ApplicationQueryResponse.model_validate(query)
