"""Audit Log API endpoints.

MCA-compliant audit trail viewer API.
Provides read-only access to audit logs - no create/update/delete endpoints
as audit logs are generated internally by services.

Also exposes `GET /verify-chain` — the hash-chain integrity check that
recomputes `audit_day_anchor` rows for a date range against the stored
values. See CLAUDE.md §8.5 and STAGE-5-PENDING-002.
"""

from datetime import date, datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import RequirePermissions, get_db_with_tenant
from app.models.auth.user import User
from app.services.common.audit_service import AuditService
from app.schemas.common.audit_log import (
    AuditLogResponse,
    AuditLogListResponse,
    EntityHistoryResponse,
)
from app.models.common.audit_log import EntityType, AuditAction
from app.core.exceptions import BadRequestException, NotFoundException

router = APIRouter()


@router.get("", response_model=AuditLogListResponse, response_model_by_alias=True)
async def list_audit_logs(
    entity_type: Optional[str] = Query(
        None,
        description="Filter by entity type (VOUCHER, PURCHASE_BILL, etc.)"
    ),
    action: Optional[str] = Query(
        None,
        description="Filter by action (CREATE, UPDATE, DELETE, etc.)"
    ),
    changed_by: Optional[UUID] = Query(
        None,
        description="Filter by user who made the change"
    ),
    date_from: Optional[date] = Query(
        None,
        description="Filter by date range start"
    ),
    date_to: Optional[date] = Query(
        None,
        description="Filter by date range end"
    ),
    search: Optional[str] = Query(
        None,
        description="Search in entity reference and change reason"
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(RequirePermissions("AUDIT_LOG_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get paginated list of audit logs with filters.

    Scoped to the caller's organization (JWT). For cross-organization
    audit-log viewing a separate platform-admin endpoint with
    `RequirePermissions("PLATFORM_ADMIN")` + an explicit
    `target_organization_id` parameter is required.

    Requires AUDIT_LOG_VIEW permission.
    Audit logs are read-only and immutable per MCA compliance.
    """
    service = AuditService(db)

    # Convert dates to datetime if provided
    dt_from = datetime.combine(date_from, datetime.min.time()) if date_from else None
    dt_to = datetime.combine(date_to, datetime.max.time()) if date_to else None

    return await service.get_audit_logs(
        organization_id=current_user.organization_id,
        page=page,
        page_size=page_size,
        entity_type=entity_type,
        action=action,
        changed_by=changed_by,
        date_from=dt_from,
        date_to=dt_to,
        search=search,
    )


@router.get("/entity-types", response_model=List[str], response_model_by_alias=True)
async def list_entity_types(
    current_user: User = Depends(RequirePermissions("AUDIT_LOG_VIEW")),
):
    """
    Get list of available entity types for filtering.

    Requires AUDIT_LOG_VIEW permission.
    """
    return [e.value for e in EntityType]


@router.get("/actions", response_model=List[str], response_model_by_alias=True)
async def list_audit_actions(
    current_user: User = Depends(RequirePermissions("AUDIT_LOG_VIEW")),
):
    """
    Get list of available audit actions for filtering.

    Requires AUDIT_LOG_VIEW permission.
    """
    return [a.value for a in AuditAction]


@router.get("/recent", response_model=List[AuditLogResponse], response_model_by_alias=True)
async def get_recent_changes(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(RequirePermissions("AUDIT_LOG_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get most recent audit log entries for activity feed/dashboard.

    Scoped to the caller's organization (JWT). Requires AUDIT_LOG_VIEW
    permission.
    """
    service = AuditService(db)
    return await service.get_recent_changes(
        organization_id=current_user.organization_id,
        limit=limit,
    )


@router.get("/entity/{entity_type}/{entity_id}", response_model=EntityHistoryResponse, response_model_by_alias=True)
async def get_entity_history(
    entity_type: str,
    entity_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(RequirePermissions("AUDIT_LOG_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get complete audit history for a specific entity.

    Useful for viewing all changes made to a voucher, invoice, etc.
    Requires AUDIT_LOG_VIEW permission.
    """
    # Validate entity type
    try:
        EntityType(entity_type)
    except ValueError:
        raise BadRequestException(
            detail=f"Invalid entity type: {entity_type}. Valid types: {[e.value for e in EntityType]}",
            error_code="INVALID_ENTITY_TYPE_VALID_TYPES",
        )

    service = AuditService(db)
    return await service.get_entity_history(
        entity_type=entity_type,
        entity_id=entity_id,
        page=page,
        page_size=page_size,
    )


@router.get("/{audit_log_id}", response_model=AuditLogResponse, response_model_by_alias=True)
async def get_audit_log(
    audit_log_id: UUID,
    current_user: User = Depends(RequirePermissions("AUDIT_LOG_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get a specific audit log entry by ID.

    Includes line item changes if any.
    Requires AUDIT_LOG_VIEW permission.
    """
    service = AuditService(db)
    audit_log = await service.repo.get(audit_log_id)

    if not audit_log:
        raise NotFoundException(
            detail="Audit log entry not found",
            error_code="AUDIT_LOG_ENTRY_NOT_FOUND",
        )

    return service._to_response(audit_log)


# ---------------------------------------------------------------------------
# Audit hash-chain integrity verification (STAGE-5-PENDING-002 closure).
# ---------------------------------------------------------------------------


class DayVerificationResponse(BaseModel):
    day: str  # ISO
    row_count: int
    stored_anchor: str
    recomputed_anchor: str
    is_valid: bool


class ChainVerificationResponse(BaseModel):
    organization_id: Optional[UUID]
    start_day: str
    end_day: str
    days_checked: int
    mismatches: List[str]  # ISO dates that failed
    is_chain_intact: bool


@router.get("/verify-chain", response_model=ChainVerificationResponse, response_model_by_alias=True)
async def verify_audit_chain(
    target_organization_id: Optional[UUID] = Query(
        None,
        description=(
            "Org to verify. Defaults to the caller's own organization. "
            "NULL is reserved for the system-global chain (platform-admin only)."
        ),
    ),
    start_day: Optional[date] = Query(
        None, description="Inclusive start. Defaults to 30 days before end_day."
    ),
    end_day: Optional[date] = Query(
        None, description="Inclusive end. Defaults to yesterday."
    ),
    current_user: User = Depends(RequirePermissions("AUDIT_CHAIN_VERIFY")),
    db: AsyncSession = Depends(get_db_with_tenant),
) -> ChainVerificationResponse:
    """Recompute the audit hash chain for the date range and compare to
    stored anchors. Any tampering with historical audit rows surfaces
    as a mismatch for that day and every subsequent day.

    Default scope is the caller's own organization (JWT). The
    `AUDIT_CHAIN_VERIFY` permission is platform-admin level (granted only
    to operators/compliance reviewers) — within that, an explicit
    `target_organization_id` may select a specific org or NULL for the
    system-global chain. This endpoint touches only hash columns — PII
    in the underlying rows is NOT exposed.
    """
    if end_day is None:
        end_day = date.today() - timedelta(days=1)
    if start_day is None:
        start_day = end_day - timedelta(days=30)
    if start_day > end_day:
        raise BadRequestException(
            detail="start_day must be <= end_day",
            error_code="START_DAY_MUST_BE_END_DAY",
        )

    from app.services.audit.audit_log_loader import load_rows_by_day
    from app.services.audit.hash_chain_service import verify_stored_chain

    # Default to caller's own org; an explicit target may be supplied by a
    # platform-admin holder of AUDIT_CHAIN_VERIFY.
    organization_id = (
        target_organization_id
        if target_organization_id is not None
        else current_user.organization_id
    )

    rows_by_day = await load_rows_by_day(
        db,
        organization_id=organization_id,
        start_day=start_day,
        end_day=end_day,
    )
    mismatches = await verify_stored_chain(
        db,
        organization_id=organization_id,
        rows_by_day=rows_by_day,
    )
    days_checked = (end_day - start_day).days + 1
    return ChainVerificationResponse(
        organization_id=organization_id,
        start_day=start_day.isoformat(),
        end_day=end_day.isoformat(),
        days_checked=days_checked,
        mismatches=mismatches,
        is_chain_intact=(len(mismatches) == 0),
    )
