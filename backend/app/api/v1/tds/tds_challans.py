"""TDS Challan API endpoints."""

from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_active_organization_id, get_db_with_tenant
from app.models.auth.user import User
from app.models.tds.tds_challan import ChallanStatus
from app.services.tds.tds_challan_service import TDSChallanService
from app.schemas.tds.tds_challan import (
    TDSChallanCreate,
    TDSChallanUpdate,
    TDSChallanResponse,
    TDSChallanListResponse,
    TDSChallanPaymentUpdate,
    TDSChallanOLTASUpdate,
    AddEntriesToChallanRequest,
    RemoveEntriesFromChallanRequest,
    ChallanAggregationRequest,
    ChallanSummary,
    TDSEntryBrief,
)
from app.schemas.base import PaginatedResponse

router = APIRouter()


def _to_list_response(challan) -> TDSChallanListResponse:
    """Convert model to list response."""
    return TDSChallanListResponse(
        id=challan.id,
        challan_number=challan.challan_number,
        bsr_code=challan.bsr_code,
        organization_id=challan.organization_id,
        tds_section_code=challan.tds_section.section_code if challan.tds_section else None,
        tds_section_name=challan.tds_section.section_name if challan.tds_section else None,
        assessment_year=challan.assessment_year,
        period_from=challan.period_from,
        period_to=challan.period_to,
        total_amount=challan.total_amount,
        entry_count=challan.entry_count,
        status=challan.status,
        payment_date=challan.payment_date,
        is_late=challan.is_late,
        is_included_in_return=challan.is_included_in_return,
        return_quarter=challan.return_quarter,
        created_at=challan.created_at.date() if challan.created_at else date.today(),
    )


def _to_response(challan, include_entries: bool = False) -> TDSChallanResponse:
    """Convert model to response."""
    entries = None
    if include_entries and challan.entries:
        entries = [
            TDSEntryBrief(
                id=e.id,
                deductee_name=e.deductee_name,
                deductee_pan=e.deductee_pan,
                base_amount=e.base_amount,
                tds_amount=e.tds_amount,
                surcharge=e.surcharge,
                cess=e.cess,
                total_tds=e.total_tds,
                deduction_date=e.deduction_date,
            )
            for e in challan.entries
        ]

    return TDSChallanResponse(
        id=challan.id,
        challan_number=challan.challan_number,
        bsr_code=challan.bsr_code,
        serial_number=challan.serial_number,
        organization_id=challan.organization_id,
        tds_section_id=challan.tds_section_id,
        tds_section_code=challan.tds_section.section_code if challan.tds_section else None,
        tds_section_name=challan.tds_section.section_name if challan.tds_section else None,
        financial_year_id=challan.financial_year_id,
        assessment_year=challan.assessment_year,
        period_from=challan.period_from,
        period_to=challan.period_to,
        total_base_amount=challan.total_base_amount,
        total_tds_amount=challan.total_tds_amount,
        total_surcharge=challan.total_surcharge,
        total_cess=challan.total_cess,
        interest_amount=challan.interest_amount,
        penalty_amount=challan.penalty_amount,
        other_amount=challan.other_amount,
        total_amount=challan.total_amount,
        entry_count=challan.entry_count,
        status=challan.status,
        payment_date=challan.payment_date,
        payment_mode=challan.payment_mode,
        bank_name=challan.bank_name,
        bank_branch=challan.bank_branch,
        bank_account_number=challan.bank_account_number,
        cheque_dd_number=challan.cheque_dd_number,
        cheque_dd_date=challan.cheque_dd_date,
        oltas_acknowledgment=challan.oltas_acknowledgment,
        oltas_status=challan.oltas_status,
        oltas_verified_at=challan.oltas_verified_at,
        challan_type=challan.challan_type,
        minor_head=challan.minor_head,
        deductor_tan=challan.deductor_tan,
        deductor_name=challan.deductor_name,
        deductor_address=challan.deductor_address,
        return_quarter=challan.return_quarter,
        is_included_in_return=challan.is_included_in_return,
        return_id=challan.return_id,
        is_late=challan.is_late,
        remarks=challan.remarks,
        created_at=challan.created_at.date() if challan.created_at else date.today(),
        updated_at=challan.updated_at.date() if challan.updated_at else None,
        is_active=challan.is_active,
        entries=entries,
    )


class CancelRequest(BaseModel):
    """Request to cancel a challan."""

    reason: str


@router.get(
    "", response_model=PaginatedResponse[TDSChallanListResponse], response_model_by_alias=True
)
async def list_challans(
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    status: Optional[ChallanStatus] = Query(None),
    tds_section_id: Optional[UUID] = Query(None),
    financial_year_id: Optional[UUID] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100, alias="pageSize"),
    active_organization_id: UUID = Depends(get_active_organization_id),
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get TDS challans for an organization."""
    service = TDSChallanService(db)
    skip = (page - 1) * page_size
    challans, total = await service.get_by_organization(
        active_organization_id,
        from_date,
        to_date,
        status,
        tds_section_id,
        financial_year_id,
        skip,
        page_size,
    )
    items = [_to_list_response(c) for c in challans]
    return PaginatedResponse.create(items, total, page, page_size)


@router.get("/summary", response_model=ChallanSummary, response_model_by_alias=True)
async def get_summary(
    financial_year_id: Optional[UUID] = Query(None),
    active_organization_id: UUID = Depends(get_active_organization_id),
    current_user: User = Depends(RequirePermissions("FIN_REPORT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get challan summary statistics."""
    service = TDSChallanService(db)
    return await service.get_summary(active_organization_id, financial_year_id)


@router.get("/due", response_model=List[TDSChallanListResponse], response_model_by_alias=True)
async def get_due_challans(
    active_organization_id: UUID = Depends(get_active_organization_id),
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get challans due for payment."""
    service = TDSChallanService(db)
    challans = await service.get_due_for_payment(active_organization_id)
    return [_to_list_response(c) for c in challans]


@router.post("", response_model=TDSChallanResponse, response_model_by_alias=True)
async def create_challan(
    data: TDSChallanCreate,
    active_organization_id: UUID = Depends(get_active_organization_id),
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Create a new TDS challan."""
    service = TDSChallanService(db)
    challan = await service.create(
        data.model_copy(update={"organization_id": active_organization_id}),
        current_user.id,
    )
    return _to_response(challan)


@router.post("/generate", response_model=List[TDSChallanResponse], response_model_by_alias=True)
async def generate_challans(
    data: ChallanAggregationRequest,
    active_organization_id: UUID = Depends(get_active_organization_id),
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Auto-generate challans for a period.

    Groups unlinked TDS entries by section and creates challans.
    """
    service = TDSChallanService(db)
    challans = await service.generate_challans(
        data.model_copy(update={"organization_id": active_organization_id}),
        current_user.id,
    )
    return [_to_response(c) for c in challans]


@router.get("/{challan_id}", response_model=TDSChallanResponse, response_model_by_alias=True)
async def get_challan(
    challan_id: UUID,
    include_entries: bool = Query(False),
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get TDS challan by ID."""
    service = TDSChallanService(db)
    if include_entries:
        challan = await service.get_with_entries(challan_id)
    else:
        challan = await service.get(challan_id)
    return _to_response(challan, include_entries)


@router.put("/{challan_id}", response_model=TDSChallanResponse, response_model_by_alias=True)
async def update_challan(
    challan_id: UUID,
    data: TDSChallanUpdate,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Update a TDS challan."""
    service = TDSChallanService(db)
    challan = await service.update(challan_id, data, current_user.id)
    return _to_response(challan)


@router.post(
    "/{challan_id}/entries", response_model=TDSChallanResponse, response_model_by_alias=True
)
async def add_entries(
    challan_id: UUID,
    data: AddEntriesToChallanRequest,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Add TDS entries to a challan."""
    service = TDSChallanService(db)
    challan = await service.add_entries(challan_id, data.entry_ids, current_user.id)
    return _to_response(challan, include_entries=True)


@router.delete(
    "/{challan_id}/entries", response_model=TDSChallanResponse, response_model_by_alias=True
)
async def remove_entries(
    challan_id: UUID,
    data: RemoveEntriesFromChallanRequest,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Remove TDS entries from a challan."""
    service = TDSChallanService(db)
    challan = await service.remove_entries(challan_id, data.entry_ids, current_user.id)
    return _to_response(challan, include_entries=True)


@router.post(
    "/{challan_id}/finalize", response_model=TDSChallanResponse, response_model_by_alias=True
)
async def finalize_challan(
    challan_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_APPROVE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Finalize a challan (move from DRAFT to PENDING)."""
    service = TDSChallanService(db)
    challan = await service.finalize(challan_id, current_user.id)
    return _to_response(challan)


@router.post(
    "/{challan_id}/payment", response_model=TDSChallanResponse, response_model_by_alias=True
)
async def record_payment(
    challan_id: UUID,
    data: TDSChallanPaymentUpdate,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_APPROVE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Record payment details for a challan."""
    service = TDSChallanService(db)
    challan = await service.record_payment(challan_id, data, current_user.id)
    return _to_response(challan)


@router.post(
    "/{challan_id}/verify-oltas", response_model=TDSChallanResponse, response_model_by_alias=True
)
async def verify_oltas(
    challan_id: UUID,
    data: TDSChallanOLTASUpdate,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_APPROVE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Update OLTAS verification status."""
    service = TDSChallanService(db)
    challan = await service.verify_oltas(challan_id, data, current_user.id)
    return _to_response(challan)


@router.post(
    "/{challan_id}/cancel", response_model=TDSChallanResponse, response_model_by_alias=True
)
async def cancel_challan(
    challan_id: UUID,
    data: CancelRequest,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_DELETE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Cancel a challan."""
    service = TDSChallanService(db)
    challan = await service.cancel(challan_id, data.reason, current_user.id)
    return _to_response(challan)


@router.delete("/{challan_id}")
async def delete_challan(
    challan_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_DELETE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Delete a TDS challan."""
    service = TDSChallanService(db)
    await service.delete(challan_id, current_user.id)
    return {"message": "TDS challan deleted successfully"}
