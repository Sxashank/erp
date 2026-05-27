"""Physical Verification API endpoints."""

from typing import List, Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db_with_tenant
from app.schemas.fixed_assets.common import OffsetPaginatedResponse
from app.models.auth.user import User
from app.core.constants import Permissions
from app.core.permissions import PermissionChecker
from app.schemas.fixed_assets.physical_verification import (
    VerificationScheduleCreate,
    VerificationScheduleUpdate,
    VerificationScheduleResponse,
    VerificationEntryCreate,
    VerificationEntryUpdate,
    VerificationEntryResponse,
    DiscrepancyUpdate,
    DiscrepancyResponse,
    VerificationSummaryResponse,
    StartVerificationRequest,
    CompleteVerificationRequest,
    BulkVerificationRequest,
)
from app.schemas.base import MessageResponse
from app.services.fixed_assets.physical_verification_service import PhysicalVerificationService
from app.core.exceptions import BadRequestException, NotFoundException

router = APIRouter()


def _schedule_status_to_response(status_value: str) -> str:
    return "SCHEDULED" if status_value == "DRAFT" else status_value


def _schedule_to_response(schedule) -> VerificationScheduleResponse:
    """Convert schedule model to response schema."""
    return VerificationScheduleResponse(
        id=schedule.id,
        organization_id=schedule.organization_id,
        schedule_reference=schedule.schedule_reference,
        schedule_name=schedule.schedule_name,
        financial_year=schedule.financial_year,
        location_id=schedule.location_id,
        location_name=schedule.location.name if schedule.location else None,
        category_ids=schedule.category_ids,
        scheduled_start_date=schedule.scheduled_start_date,
        scheduled_end_date=schedule.scheduled_end_date,
        actual_start_date=schedule.actual_start_date,
        actual_end_date=schedule.actual_end_date,
        assigned_to=schedule.assigned_to,
        team_members=schedule.team_members,
        total_assets=schedule.total_assets,
        verified_count=schedule.verified_count,
        found_count=schedule.found_count,
        missing_count=schedule.missing_count,
        discrepancy_count=schedule.discrepancy_count,
        total_value_verified=schedule.total_value_verified,
        total_value_missing=schedule.total_value_missing,
        status=_schedule_status_to_response(schedule.status),
        remarks=schedule.remarks,
        approved_by=schedule.approved_by,
        approved_at=schedule.approved_at,
        is_active=True,
        created_at=schedule.created_at,
        updated_at=schedule.updated_at,
        created_by=schedule.created_by,
        updated_by=schedule.updated_by,
    )


def _entry_to_response(entry) -> VerificationEntryResponse:
    """Convert entry model to response schema."""
    return VerificationEntryResponse(
        id=entry.id,
        schedule_id=entry.schedule_id,
        asset_id=entry.asset_id,
        asset_code=entry.asset.asset_code if entry.asset else None,
        asset_name=entry.asset.asset_name if entry.asset else None,
        category_name=(
            entry.asset.category.category_name if entry.asset and entry.asset.category else None
        ),
        expected_location_id=entry.expected_location_id,
        expected_department_id=entry.expected_department_id,
        verification_date=entry.verification_date,
        verified_by=entry.verified_by,
        verification_result=entry.verification_result,
        asset_condition=entry.asset_condition,
        actual_location_id=entry.actual_location_id,
        actual_department_id=entry.actual_department_id,
        book_value=entry.book_value,
        photo_urls=entry.photo_urls,
        barcode_scan=entry.barcode_scan,
        condition_notes=entry.condition_notes,
        remarks=entry.remarks,
        is_active=True,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        created_by=entry.created_by,
        updated_by=entry.updated_by,
    )


def _discrepancy_to_response(discrepancy) -> DiscrepancyResponse:
    """Convert discrepancy model to response schema."""
    return DiscrepancyResponse(
        id=discrepancy.id,
        entry_id=discrepancy.entry_id,
        asset_id=discrepancy.entry.asset_id if discrepancy.entry else None,
        asset_code=(
            discrepancy.entry.asset.asset_code
            if discrepancy.entry and discrepancy.entry.asset
            else None
        ),
        asset_name=(
            discrepancy.entry.asset.asset_name
            if discrepancy.entry and discrepancy.entry.asset
            else None
        ),
        discrepancy_type=discrepancy.discrepancy_type,
        description=discrepancy.description,
        value_impact=discrepancy.value_impact,
        status=discrepancy.status,
        investigated_by=discrepancy.investigated_by,
        investigation_notes=discrepancy.investigation_notes,
        resolution=discrepancy.resolution,
        resolved_by=discrepancy.resolved_by,
        resolved_at=discrepancy.resolved_at,
        remarks=discrepancy.remarks,
        is_active=True,
        created_at=discrepancy.created_at,
        updated_at=discrepancy.updated_at,
        created_by=discrepancy.created_by,
        updated_by=discrepancy.updated_by,
    )


# ============================================
# Schedule Endpoints
# ============================================


@router.get(
    "/schedules",
    response_model=OffsetPaginatedResponse[VerificationScheduleResponse],
    response_model_by_alias=True,
)
async def list_schedules(
    request: Request,
    financial_year: Optional[str] = Query(None, pattern=r"^\d{4}-\d{2}$"),
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_VIEW])),
):
    """List physical verification schedules."""
    service = PhysicalVerificationService(db)
    schedules, total = await service.list_schedules(
        current_user.organization_id, financial_year, status, skip, limit
    )

    return OffsetPaginatedResponse(
        items=[_schedule_to_response(s) for s in schedules],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/schedules/{schedule_id}",
    response_model=VerificationScheduleResponse,
    response_model_by_alias=True,
)
async def get_schedule(
    request: Request,
    schedule_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_VIEW])),
):
    """Get physical verification schedule by ID."""
    service = PhysicalVerificationService(db)
    schedule = await service.get_schedule(schedule_id)
    if not schedule:
        raise NotFoundException(detail="Schedule not found", error_code="SCHEDULE_NOT_FOUND")
    return _schedule_to_response(schedule)


@router.post(
    "/schedules",
    response_model=VerificationScheduleResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
async def create_schedule(
    request: Request,
    data: VerificationScheduleCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_UPDATE])),
):
    """Create a new physical verification schedule."""
    service = PhysicalVerificationService(db)
    try:
        schedule = await service.create_schedule(data, created_by=current_user.id)
        return _schedule_to_response(schedule)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.put(
    "/schedules/{schedule_id}",
    response_model=VerificationScheduleResponse,
    response_model_by_alias=True,
)
async def update_schedule(
    request: Request,
    schedule_id: UUID,
    data: VerificationScheduleUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_UPDATE])),
):
    """Update a physical verification schedule."""
    service = PhysicalVerificationService(db)
    try:
        schedule = await service.update_schedule(schedule_id, data, updated_by=current_user.id)
        if not schedule:
            raise NotFoundException(detail="Schedule not found", error_code="SCHEDULE_NOT_FOUND")
        return _schedule_to_response(schedule)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post(
    "/schedules/{schedule_id}/start",
    response_model=VerificationScheduleResponse,
    response_model_by_alias=True,
)
async def start_schedule(
    request: Request,
    schedule_id: UUID,
    data: Optional[StartVerificationRequest] = None,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_UPDATE])),
):
    """Start a physical verification schedule."""
    service = PhysicalVerificationService(db)
    try:
        schedule = await service.start_verification(schedule_id, started_by=current_user.id)
        return _schedule_to_response(schedule)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post(
    "/schedules/{schedule_id}/complete",
    response_model=VerificationScheduleResponse,
    response_model_by_alias=True,
)
async def complete_schedule(
    request: Request,
    schedule_id: UUID,
    data: Optional[CompleteVerificationRequest] = None,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_UPDATE])),
):
    """Complete a physical verification schedule."""
    service = PhysicalVerificationService(db)
    try:
        schedule = await service.complete_verification(schedule_id, completed_by=current_user.id)
        return _schedule_to_response(schedule)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post(
    "/schedules/{schedule_id}/approve",
    response_model=VerificationScheduleResponse,
    response_model_by_alias=True,
)
async def approve_schedule(
    request: Request,
    schedule_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_UPDATE])),
):
    """Approve a completed verification schedule."""
    service = PhysicalVerificationService(db)
    try:
        schedule = await service.approve_verification(schedule_id, approved_by=current_user.id)
        return _schedule_to_response(schedule)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


# ============================================
# Entry Endpoints
# ============================================


@router.get(
    "/schedules/{schedule_id}/entries",
    response_model=OffsetPaginatedResponse[VerificationEntryResponse],
    response_model_by_alias=True,
)
async def list_entries(
    request: Request,
    schedule_id: UUID,
    verification_result: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_VIEW])),
):
    """List verification entries for a schedule."""
    service = PhysicalVerificationService(db)
    entries, total = await service.list_entries(schedule_id, verification_result, skip, limit)

    return OffsetPaginatedResponse(
        items=[_entry_to_response(e) for e in entries],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/entries/{entry_id}", response_model=VerificationEntryResponse, response_model_by_alias=True
)
async def get_entry(
    request: Request,
    entry_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_VIEW])),
):
    """Get verification entry by ID."""
    service = PhysicalVerificationService(db)
    entry = await service.get_entry(entry_id)
    if not entry:
        raise NotFoundException(detail="Entry not found", error_code="ENTRY_NOT_FOUND")
    return _entry_to_response(entry)


@router.put(
    "/entries/{entry_id}/verify",
    response_model=VerificationEntryResponse,
    response_model_by_alias=True,
)
async def verify_entry(
    request: Request,
    entry_id: UUID,
    data: VerificationEntryCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_UPDATE])),
):
    """Record verification result for an entry."""
    service = PhysicalVerificationService(db)
    try:
        entry = await service.verify_entry(entry_id, data, verified_by=current_user.id)
        return _entry_to_response(entry)
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


@router.post(
    "/schedules/{schedule_id}/bulk-verify", response_model=dict, response_model_by_alias=True
)
async def bulk_verify(
    request: Request,
    schedule_id: UUID,
    data: BulkVerificationRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_UPDATE])),
):
    """Bulk update verification entries."""
    service = PhysicalVerificationService(db)
    try:
        updated_count = await service.bulk_verify(
            schedule_id,
            data.verification_date,
            data.entries,
            verified_by=current_user.id,
        )
        return {
            "message": f"Updated {updated_count} entries",
            "updated_count": updated_count,
        }
    except ValueError as e:
        raise BadRequestException(detail=str(e), error_code="BAD_REQUEST")


# ============================================
# Discrepancy Endpoints
# ============================================


@router.get(
    "/discrepancies",
    response_model=OffsetPaginatedResponse[DiscrepancyResponse],
    response_model_by_alias=True,
)
async def list_discrepancies(
    request: Request,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_VIEW])),
):
    """List verification discrepancies."""
    service = PhysicalVerificationService(db)
    discrepancies, total = await service.list_discrepancies(
        current_user.organization_id, status, skip, limit
    )

    return OffsetPaginatedResponse(
        items=[_discrepancy_to_response(d) for d in discrepancies],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/discrepancies/{discrepancy_id}",
    response_model=DiscrepancyResponse,
    response_model_by_alias=True,
)
async def get_discrepancy(
    request: Request,
    discrepancy_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_VIEW])),
):
    """Get discrepancy by ID."""
    service = PhysicalVerificationService(db)
    discrepancy = await service.get_discrepancy(discrepancy_id)
    if not discrepancy:
        raise NotFoundException(detail="Discrepancy not found", error_code="DISCREPANCY_NOT_FOUND")
    return _discrepancy_to_response(discrepancy)


@router.put(
    "/discrepancies/{discrepancy_id}",
    response_model=DiscrepancyResponse,
    response_model_by_alias=True,
)
async def update_discrepancy(
    request: Request,
    discrepancy_id: UUID,
    data: DiscrepancyUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_UPDATE])),
):
    """Update a discrepancy (investigate, resolve, write-off)."""
    service = PhysicalVerificationService(db)
    discrepancy = await service.update_discrepancy(discrepancy_id, data, updated_by=current_user.id)
    if not discrepancy:
        raise NotFoundException(detail="Discrepancy not found", error_code="DISCREPANCY_NOT_FOUND")
    return _discrepancy_to_response(discrepancy)


# ============================================
# Reports
# ============================================


@router.get("/summary", response_model=VerificationSummaryResponse, response_model_by_alias=True)
async def get_verification_summary(
    request: Request,
    financial_year: str = Query(..., pattern=r"^\d{4}-\d{2}$"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_REPORT_VIEW])),
):
    """Get physical verification summary for a financial year."""
    service = PhysicalVerificationService(db)
    return await service.get_verification_summary(current_user.organization_id, financial_year)
