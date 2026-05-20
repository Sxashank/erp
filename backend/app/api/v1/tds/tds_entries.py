"""TDS Entry API endpoints."""

from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import RequirePermissions, get_db_with_tenant
from app.models.auth.user import User
from app.services.tds.tds_entry_service import TDSEntryService
from app.schemas.tds.tds_entry import (
    TDSEntryCreate,
    TDSEntryUpdate,
    TDSEntryResponse,
    ThresholdValidationRequest,
    ThresholdValidationResponse,
)
from app.schemas.base import PaginatedResponse
from app.core.constants import TDSChallanStatus

router = APIRouter()


def _to_response(entry) -> TDSEntryResponse:
    """Convert model to response."""
    return TDSEntryResponse(
        id=entry.id,
        tds_section_id=entry.tds_section_id,
        tds_section_code=entry.tds_section.section_code if entry.tds_section else None,
        tds_section_name=entry.tds_section.section_name if entry.tds_section else None,
        voucher_id=entry.voucher_id,
        voucher_number=entry.voucher.voucher_number if entry.voucher else None,
        organization_id=entry.organization_id,
        vendor_id=entry.vendor_id,
        financial_year_id=entry.financial_year_id,
        deductee_name=entry.deductee_name,
        deductee_pan=entry.deductee_pan,
        deductee_type=entry.deductee_type,
        deductee_address=entry.deductee_address,
        deduction_date=entry.deduction_date,
        base_amount=entry.base_amount,
        tds_rate=entry.tds_rate,
        tds_amount=entry.tds_amount,
        surcharge=entry.surcharge,
        cess=entry.cess,
        total_tds=entry.total_tds,
        lower_deduction_cert_no=entry.lower_deduction_cert_no,
        is_threshold_crossed=entry.is_threshold_crossed,
        aggregate_amount_ytd=entry.aggregate_amount_ytd,
        threshold_reason=entry.threshold_reason,
        challan_status=entry.challan_status,
        challan_number=entry.challan_number,
        challan_date=entry.challan_date,
        bank_name=entry.bank_name,
        bsr_code=entry.bsr_code,
        certificate_number=entry.certificate_number,
        certificate_date=entry.certificate_date,
        return_quarter=entry.return_quarter,
        return_filed=entry.return_filed,
        acknowledgment_number=entry.acknowledgment_number,
        remarks=entry.remarks,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        is_active=entry.is_active,
    )


class ChallanUpdateRequest(BaseModel):
    """Request for updating challan details."""

    challan_number: str
    challan_date: date
    bank_name: str
    bsr_code: str


@router.get("", response_model=PaginatedResponse[TDSEntryResponse], response_model_by_alias=True)
async def list_tds_entries(
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    challan_status: Optional[TDSChallanStatus] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100, alias="pageSize"),
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get TDS entries for an organization."""
    service = TDSEntryService(db)
    skip = (page - 1) * page_size
    entries, total = await service.get_by_organization(
        current_user.organization_id, from_date, to_date, challan_status, skip, page_size
    )
    items = [_to_response(e) for e in entries]
    return PaginatedResponse.create(items, total, page, page_size)


@router.get("/pending-challans", response_model=PaginatedResponse[TDSEntryResponse], response_model_by_alias=True)
async def list_pending_challans(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100, alias="pageSize"),
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get TDS entries with pending challan payments."""
    service = TDSEntryService(db)
    skip = (page - 1) * page_size
    entries, total = await service.get_pending_challans(current_user.organization_id, skip, page_size)
    items = [_to_response(e) for e in entries]
    return PaginatedResponse.create(items, total, page, page_size)


@router.get("/quarter/{financial_year}/{quarter}", response_model=List[TDSEntryResponse], response_model_by_alias=True)
async def list_by_quarter(
    financial_year: str = "2024-25",
    quarter: str = "Q1",
    current_user: User = Depends(RequirePermissions("FIN_REPORT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get TDS entries for a specific quarter (for return filing)."""
    service = TDSEntryService(db)
    entries = await service.get_by_quarter(current_user.organization_id, financial_year, quarter)
    return [_to_response(e) for e in entries]


@router.post("/validate-threshold", response_model=ThresholdValidationResponse, response_model_by_alias=True)
async def validate_threshold(
    data: ThresholdValidationRequest,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Validate TDS threshold for a transaction.

    Returns whether TDS is applicable based on:
    - Single transaction threshold (e.g., ₹30,000 for 194C)
    - Annual aggregate threshold per vendor (e.g., ₹1,00,000 for 194C)

    This endpoint can be used to check TDS applicability before creating entries.
    """
    service = TDSEntryService(db)
    result = await service.validate_threshold(
        organization_id=data.organization_id,
        vendor_id=data.vendor_id,
        tds_section_id=data.tds_section_id,
        base_amount=data.base_amount,
        deduction_date=data.deduction_date,
        deductee_type=data.deductee_type,
        has_pan=bool(data.deductee_pan),
    )
    return ThresholdValidationResponse(
        tds_applicable=result.tds_applicable,
        reason=result.reason,
        single_threshold=result.single_threshold,
        annual_threshold=result.annual_threshold,
        current_aggregate=result.current_aggregate,
        new_aggregate=result.new_aggregate,
        tds_rate=result.tds_rate,
        estimated_tds=result.estimated_tds,
        estimated_surcharge=result.estimated_surcharge,
        estimated_cess=result.estimated_cess,
        estimated_total_tds=result.estimated_total_tds,
    )


@router.post("", response_model=TDSEntryResponse, response_model_by_alias=True)
async def create_tds_entry(
    data: TDSEntryCreate,
    skip_threshold_check: bool = Query(False, description="Skip threshold validation for manual entries"),
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Create a new TDS entry.

    By default, validates that the transaction meets single or aggregate thresholds.
    Set skip_threshold_check=true to bypass validation for manual entries.
    """
    service = TDSEntryService(db)
    entry = await service.create(data, current_user.id, skip_threshold_check=skip_threshold_check)
    return _to_response(entry)


@router.get("/{entry_id}", response_model=TDSEntryResponse, response_model_by_alias=True)
async def get_tds_entry(
    entry_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get TDS entry by ID."""
    service = TDSEntryService(db)
    entry = await service.get(entry_id)
    return _to_response(entry)


@router.put("/{entry_id}", response_model=TDSEntryResponse, response_model_by_alias=True)
async def update_tds_entry(
    entry_id: UUID,
    data: TDSEntryUpdate,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Update a TDS entry."""
    service = TDSEntryService(db)
    entry = await service.update(entry_id, data, current_user.id)
    return _to_response(entry)


@router.post("/{entry_id}/challan", response_model=TDSEntryResponse, response_model_by_alias=True)
async def update_challan(
    entry_id: UUID,
    data: ChallanUpdateRequest,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Update challan details for a TDS entry."""
    service = TDSEntryService(db)
    entry = await service.update_challan(
        entry_id,
        data.challan_number,
        data.challan_date,
        data.bank_name,
        data.bsr_code,
        current_user.id,
    )
    return _to_response(entry)


@router.delete("/{entry_id}")
async def delete_tds_entry(
    entry_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_DELETE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Delete a TDS entry."""
    service = TDSEntryService(db)
    await service.delete(entry_id, current_user.id)
    return {"message": "TDS entry deleted successfully"}
