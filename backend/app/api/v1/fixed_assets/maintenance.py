"""Maintenance and AMC API endpoints."""

from typing import List, Optional
from uuid import UUID
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.auth.user import User
from app.core.constants import Permissions
from app.core.permissions import PermissionChecker
from app.models.fixed_assets.maintenance import (
    AMCStatus,
    MaintenanceStatus,
    MaintenanceType,
    MaintenancePriority,
)
from app.schemas.fixed_assets.maintenance import (
    AMCContractCreate,
    AMCContractUpdate,
    AMCContractRenew,
    AMCContractResponse,
    MaintenanceRequestCreate,
    MaintenanceRequestUpdate,
    MaintenanceRequestComplete,
    MaintenanceRequestResponse,
    MaintenanceScheduleCreate,
    MaintenanceScheduleUpdate,
    MaintenanceScheduleResponse,
    AssetWarrantyCreate,
    AssetWarrantyUpdate,
    AssetWarrantyResponse,
    MaintenanceSummaryResponse,
    AssetMaintenanceHistoryResponse,
    AMCExpiryAlertResponse,
    WarrantyExpiryAlertResponse,
)
from app.schemas.base import MessageResponse
from app.services.fixed_assets.maintenance_service import MaintenanceService

router = APIRouter()


def _amc_to_response(contract) -> AMCContractResponse:
    """Convert AMC contract model to response."""
    return AMCContractResponse(
        id=contract.id,
        organization_id=contract.organization_id,
        contract_number=contract.contract_number,
        contract_name=contract.contract_name,
        amc_type=contract.amc_type,
        status=contract.status,
        vendor_id=contract.vendor_id,
        vendor_name=contract.vendor.name if contract.vendor else None,
        vendor_contact_person=contract.vendor_contact_person,
        vendor_contact_phone=contract.vendor_contact_phone,
        vendor_contact_email=contract.vendor_contact_email,
        start_date=contract.start_date,
        end_date=contract.end_date,
        days_until_expiry=contract.days_until_expiry,
        is_expiring_soon=contract.is_expiring_soon,
        contract_value=contract.contract_value,
        gst_rate=contract.gst_rate,
        gst_amount=contract.gst_amount,
        total_value=contract.total_value,
        payment_frequency=contract.payment_frequency,
        next_payment_date=contract.next_payment_date,
        coverage_details=contract.coverage_details,
        exclusions=contract.exclusions,
        response_time_hours=contract.response_time_hours,
        resolution_time_hours=contract.resolution_time_hours,
        preventive_maintenance_frequency=contract.preventive_maintenance_frequency,
        visits_per_year=contract.visits_per_year,
        visits_completed=contract.visits_completed,
        asset_ids=contract.asset_ids,
        asset_count=len(contract.asset_ids) if contract.asset_ids else 0,
        is_renewable=contract.is_renewable,
        renewal_reminder_days=contract.renewal_reminder_days,
        auto_renewal=contract.auto_renewal,
        is_active=True,
        created_at=contract.created_at,
        updated_at=contract.updated_at,
        created_by=contract.created_by,
        updated_by=contract.updated_by,
    )


def _request_to_response(request) -> MaintenanceRequestResponse:
    """Convert maintenance request model to response."""
    return MaintenanceRequestResponse(
        id=request.id,
        organization_id=request.organization_id,
        request_number=request.request_number,
        asset_id=request.asset_id,
        asset_code=request.asset.asset_code if request.asset else None,
        asset_name=request.asset.asset_name if request.asset else None,
        amc_contract_id=request.amc_contract_id,
        amc_contract_number=request.amc_contract.contract_number if request.amc_contract else None,
        maintenance_type=request.maintenance_type,
        status=request.status,
        priority=request.priority,
        title=request.title,
        description=request.description,
        reported_by=request.reported_by,
        reported_date=request.reported_date,
        scheduled_date=request.scheduled_date,
        scheduled_time=request.scheduled_time,
        assigned_to_vendor_id=request.assigned_to_vendor_id,
        assigned_vendor_name=request.assigned_vendor.name if request.assigned_vendor else None,
        assigned_technician=request.assigned_technician,
        actual_start_date=request.actual_start_date,
        actual_completion_date=request.actual_completion_date,
        downtime_hours=request.downtime_hours,
        work_performed=request.work_performed,
        parts_replaced=request.parts_replaced,
        findings=request.findings,
        recommendations=request.recommendations,
        labor_cost=request.labor_cost,
        parts_cost=request.parts_cost,
        other_cost=request.other_cost,
        total_cost=request.total_cost,
        is_covered_under_amc=request.is_covered_under_amc,
        invoice_number=request.invoice_number,
        invoice_date=request.invoice_date,
        customer_signoff_by=request.customer_signoff_by,
        customer_signoff_date=request.customer_signoff_date,
        customer_feedback=request.customer_feedback,
        satisfaction_rating=request.satisfaction_rating,
        next_maintenance_date=request.next_maintenance_date,
        is_active=True,
        created_at=request.created_at,
        updated_at=request.updated_at,
        created_by=request.created_by,
        updated_by=request.updated_by,
    )


def _schedule_to_response(schedule) -> MaintenanceScheduleResponse:
    """Convert maintenance schedule model to response."""
    return MaintenanceScheduleResponse(
        id=schedule.id,
        organization_id=schedule.organization_id,
        schedule_name=schedule.schedule_name,
        asset_id=schedule.asset_id,
        asset_code=schedule.asset.asset_code if schedule.asset else None,
        asset_name=schedule.asset.asset_name if schedule.asset else None,
        category_id=schedule.category_id,
        category_name=None,  # Would need join
        maintenance_type=schedule.maintenance_type,
        description=schedule.description,
        checklist=schedule.checklist,
        frequency=schedule.frequency,
        frequency_value=schedule.frequency_value,
        preferred_day_of_week=schedule.preferred_day_of_week,
        preferred_day_of_month=schedule.preferred_day_of_month,
        is_active=schedule.is_active,
        last_executed_date=schedule.last_executed_date,
        next_due_date=schedule.next_due_date,
        estimated_duration_hours=schedule.estimated_duration_hours,
        estimated_cost=schedule.estimated_cost,
        default_vendor_id=schedule.default_vendor_id,
        default_vendor_name=None,  # Would need join
        created_at=schedule.created_at,
        updated_at=schedule.updated_at,
        created_by=schedule.created_by,
        updated_by=schedule.updated_by,
    )


def _warranty_to_response(warranty) -> AssetWarrantyResponse:
    """Convert warranty model to response."""
    return AssetWarrantyResponse(
        id=warranty.id,
        organization_id=warranty.organization_id,
        asset_id=warranty.asset_id,
        asset_code=warranty.asset.asset_code if warranty.asset else None,
        asset_name=warranty.asset.asset_name if warranty.asset else None,
        warranty_type=warranty.warranty_type,
        warranty_provider=warranty.warranty_provider,
        warranty_number=warranty.warranty_number,
        start_date=warranty.start_date,
        end_date=warranty.end_date,
        days_until_expiry=warranty.days_until_expiry,
        is_expired=warranty.is_expired,
        coverage_details=warranty.coverage_details,
        exclusions=warranty.exclusions,
        contact_phone=warranty.contact_phone,
        contact_email=warranty.contact_email,
        claims_count=warranty.claims_count,
        last_claim_date=warranty.last_claim_date,
        is_active=warranty.is_active,
        created_at=warranty.created_at,
        updated_at=warranty.updated_at,
        created_by=warranty.created_by,
        updated_by=warranty.updated_by,
    )


# ============================================
# AMC Contract Endpoints
# ============================================

@router.get("/amc", response_model=dict)
async def list_amc_contracts(
    request: Request,
    organization_id: UUID,
    status: Optional[AMCStatus] = None,
    vendor_id: Optional[UUID] = None,
    expiring_within_days: Optional[int] = Query(None, ge=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_VIEW])),
):
    """List AMC contracts with filters."""
    service = MaintenanceService(db)
    contracts, total = await service.list_amc_contracts(
        organization_id, status, vendor_id, expiring_within_days, skip, limit
    )

    return {
        "items": [_amc_to_response(c) for c in contracts],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/amc/{contract_id}", response_model=AMCContractResponse)
async def get_amc_contract(
    request: Request,
    contract_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_VIEW])),
):
    """Get AMC contract by ID."""
    service = MaintenanceService(db)
    contract = await service.get_amc_contract(contract_id)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found",
        )
    return _amc_to_response(contract)


@router.post("/amc", response_model=AMCContractResponse, status_code=status.HTTP_201_CREATED)
async def create_amc_contract(
    request: Request,
    data: AMCContractCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_CREATE])),
):
    """Create a new AMC contract."""
    service = MaintenanceService(db)
    try:
        contract = await service.create_amc_contract(data, created_by=current_user.id)
        return _amc_to_response(contract)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put("/amc/{contract_id}", response_model=AMCContractResponse)
async def update_amc_contract(
    request: Request,
    contract_id: UUID,
    data: AMCContractUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_UPDATE])),
):
    """Update AMC contract."""
    service = MaintenanceService(db)
    contract = await service.update_amc_contract(contract_id, data, updated_by=current_user.id)
    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contract not found",
        )
    return _amc_to_response(contract)


@router.post("/amc/{contract_id}/activate", response_model=AMCContractResponse)
async def activate_amc_contract(
    request: Request,
    contract_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_UPDATE])),
):
    """Activate an AMC contract."""
    service = MaintenanceService(db)
    try:
        contract = await service.activate_amc_contract(contract_id, activated_by=current_user.id)
        return _amc_to_response(contract)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/amc/{contract_id}/renew", response_model=AMCContractResponse)
async def renew_amc_contract(
    request: Request,
    contract_id: UUID,
    data: AMCContractRenew,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_CREATE])),
):
    """Renew an AMC contract."""
    service = MaintenanceService(db)
    try:
        contract = await service.renew_amc_contract(contract_id, data, renewed_by=current_user.id)
        return _amc_to_response(contract)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================
# Maintenance Request Endpoints
# ============================================

@router.get("/requests", response_model=dict)
async def list_maintenance_requests(
    request: Request,
    organization_id: UUID,
    asset_id: Optional[UUID] = None,
    status: Optional[MaintenanceStatus] = None,
    maintenance_type: Optional[MaintenanceType] = None,
    priority: Optional[MaintenancePriority] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_VIEW])),
):
    """List maintenance requests with filters."""
    service = MaintenanceService(db)
    requests, total = await service.list_maintenance_requests(
        organization_id, asset_id, status, maintenance_type, priority,
        from_date, to_date, skip, limit
    )

    return {
        "items": [_request_to_response(r) for r in requests],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/requests/{request_id}", response_model=MaintenanceRequestResponse)
async def get_maintenance_request(
    request: Request,
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_VIEW])),
):
    """Get maintenance request by ID."""
    service = MaintenanceService(db)
    maint_request = await service.get_maintenance_request(request_id)
    if not maint_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found",
        )
    return _request_to_response(maint_request)


@router.post("/requests", response_model=MaintenanceRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_maintenance_request(
    request: Request,
    data: MaintenanceRequestCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_CREATE])),
):
    """Create a new maintenance request."""
    service = MaintenanceService(db)
    try:
        maint_request = await service.create_maintenance_request(data, created_by=current_user.id)
        return _request_to_response(maint_request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put("/requests/{request_id}", response_model=MaintenanceRequestResponse)
async def update_maintenance_request(
    request: Request,
    request_id: UUID,
    data: MaintenanceRequestUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_UPDATE])),
):
    """Update maintenance request."""
    service = MaintenanceService(db)
    maint_request = await service.update_maintenance_request(request_id, data, updated_by=current_user.id)
    if not maint_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found",
        )
    return _request_to_response(maint_request)


@router.post("/requests/{request_id}/start", response_model=MaintenanceRequestResponse)
async def start_maintenance_request(
    request: Request,
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_UPDATE])),
):
    """Start a maintenance request."""
    service = MaintenanceService(db)
    try:
        maint_request = await service.start_maintenance_request(request_id, started_by=current_user.id)
        return _request_to_response(maint_request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/requests/{request_id}/complete", response_model=MaintenanceRequestResponse)
async def complete_maintenance_request(
    request: Request,
    request_id: UUID,
    data: MaintenanceRequestComplete,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_UPDATE])),
):
    """Complete a maintenance request."""
    service = MaintenanceService(db)
    try:
        maint_request = await service.complete_maintenance_request(
            request_id, data, completed_by=current_user.id
        )
        return _request_to_response(maint_request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================
# Maintenance Schedule Endpoints
# ============================================

@router.get("/schedules", response_model=dict)
async def list_maintenance_schedules(
    request: Request,
    organization_id: UUID,
    asset_id: Optional[UUID] = None,
    is_active: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_VIEW])),
):
    """List maintenance schedules."""
    service = MaintenanceService(db)
    schedules, total = await service.list_maintenance_schedules(
        organization_id, asset_id, is_active, skip, limit
    )

    return {
        "items": [_schedule_to_response(s) for s in schedules],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post("/schedules", response_model=MaintenanceScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_maintenance_schedule(
    request: Request,
    data: MaintenanceScheduleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_CREATE])),
):
    """Create a preventive maintenance schedule."""
    service = MaintenanceService(db)
    try:
        schedule = await service.create_maintenance_schedule(data, created_by=current_user.id)
        return _schedule_to_response(schedule)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/schedules/execute", response_model=dict)
async def execute_scheduled_maintenance(
    request: Request,
    organization_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_CREATE])),
):
    """Execute all due maintenance schedules.

    Creates maintenance requests for all schedules that are due.
    """
    service = MaintenanceService(db)
    requests = await service.execute_scheduled_maintenance(organization_id, executed_by=current_user.id)

    return {
        "message": f"Created {len(requests)} maintenance requests",
        "requests_created": len(requests),
    }


# ============================================
# Warranty Endpoints
# ============================================

@router.get("/warranties", response_model=dict)
async def list_warranties(
    request: Request,
    organization_id: UUID,
    asset_id: Optional[UUID] = None,
    expiring_within_days: Optional[int] = Query(None, ge=1),
    is_active: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_VIEW])),
):
    """List asset warranties."""
    service = MaintenanceService(db)
    warranties, total = await service.list_warranties(
        organization_id, asset_id, expiring_within_days, is_active, skip, limit
    )

    return {
        "items": [_warranty_to_response(w) for w in warranties],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post("/warranties", response_model=AssetWarrantyResponse, status_code=status.HTTP_201_CREATED)
async def create_warranty(
    request: Request,
    data: AssetWarrantyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_CREATE])),
):
    """Create an asset warranty record."""
    service = MaintenanceService(db)
    try:
        warranty = await service.create_warranty(data, created_by=current_user.id)
        return _warranty_to_response(warranty)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ============================================
# Analytics and Alerts Endpoints
# ============================================

@router.get("/summary", response_model=MaintenanceSummaryResponse)
async def get_maintenance_summary(
    request: Request,
    organization_id: UUID,
    as_on_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_REPORT_VIEW])),
):
    """Get comprehensive maintenance summary.

    Provides:
    - AMC contract status and value
    - Warranty status
    - Open and overdue maintenance requests
    - Cost analysis (YTD, AMC vs non-AMC)
    - Breakdown by maintenance type
    """
    service = MaintenanceService(db)
    return await service.get_maintenance_summary(organization_id, as_on_date)


@router.get("/asset/{asset_id}/history", response_model=AssetMaintenanceHistoryResponse)
async def get_asset_maintenance_history(
    request: Request,
    asset_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_VIEW])),
):
    """Get complete maintenance history for an asset.

    Includes warranties, AMC coverage, service history, and scheduled maintenance.
    """
    service = MaintenanceService(db)
    try:
        return await service.get_asset_maintenance_history(asset_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/alerts/amc-expiry", response_model=AMCExpiryAlertResponse)
async def get_amc_expiry_alerts(
    request: Request,
    organization_id: UUID,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_VIEW])),
):
    """Get AMC contracts expiring within specified days."""
    service = MaintenanceService(db)
    contracts = await service.get_expiring_amc_alerts(organization_id, days)

    total_value = sum(c.total_value for c in contracts)

    return AMCExpiryAlertResponse(
        contracts_expiring=[_amc_to_response(c) for c in contracts],
        total_count=len(contracts),
        total_value_at_risk=total_value,
    )


@router.get("/alerts/warranty-expiry", response_model=WarrantyExpiryAlertResponse)
async def get_warranty_expiry_alerts(
    request: Request,
    organization_id: UUID,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(PermissionChecker([Permissions.FA_ASSET_VIEW])),
):
    """Get warranties expiring within specified days."""
    service = MaintenanceService(db)
    warranties = await service.get_expiring_warranty_alerts(organization_id, days)

    return WarrantyExpiryAlertResponse(
        warranties_expiring=[_warranty_to_response(w) for w in warranties],
        total_count=len(warranties),
    )
