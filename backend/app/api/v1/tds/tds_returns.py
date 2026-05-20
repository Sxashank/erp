"""TDS Return API endpoints."""

from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import RequirePermissions, get_db_with_tenant
from app.models.auth.user import User
from app.models.tds.tds_return import ReturnType, ReturnStatus, Quarter
from app.services.tds.tds_return_service import TDSReturnService
from app.schemas.tds.tds_return import (
    TDSReturnCreate,
    TDSReturnUpdate,
    TDSReturnResponse,
    TDSReturnListResponse,
    FilingDetailsUpdate,
    ReturnValidationResult,
    ReturnFileGenerationRequest,
    RevisionRequest,
)
from app.schemas.base import PaginatedResponse

router = APIRouter()


def _to_list_response(tds_return) -> TDSReturnListResponse:
    """Convert model to list response."""
    return TDSReturnListResponse(
        id=tds_return.id,
        organization_id=tds_return.organization_id,
        return_type=tds_return.return_type,
        financial_year=tds_return.financial_year,
        quarter=tds_return.quarter,
        period_from=tds_return.period_from,
        period_to=tds_return.period_to,
        status=tds_return.status,
        is_original=tds_return.is_original,
        revision_number=tds_return.revision_number,
        total_challans=tds_return.total_challans,
        total_deductees=tds_return.total_deductees,
        total_tds_deducted=tds_return.total_tds_deducted,
        total_tds_deposited=tds_return.total_tds_deposited,
        due_date=tds_return.due_date,
        is_late=tds_return.is_late,
        filed_date=tds_return.filed_date,
        acknowledgment_number=tds_return.acknowledgment_number,
        created_at=tds_return.created_at.date() if tds_return.created_at else date.today(),
    )


def _to_response(tds_return) -> TDSReturnResponse:
    """Convert model to response."""
    return TDSReturnResponse(
        id=tds_return.id,
        organization_id=tds_return.organization_id,
        return_type=tds_return.return_type,
        financial_year_id=tds_return.financial_year_id,
        financial_year=tds_return.financial_year,
        assessment_year=tds_return.assessment_year,
        quarter=tds_return.quarter,
        period_from=tds_return.period_from,
        period_to=tds_return.period_to,
        status=tds_return.status,
        is_original=tds_return.is_original,
        revision_number=tds_return.revision_number,
        original_return_id=tds_return.original_return_id,
        deductor_tan=tds_return.deductor_tan,
        deductor_name=tds_return.deductor_name,
        deductor_pan=tds_return.deductor_pan,
        deductor_type=tds_return.deductor_type,
        deductor_category=tds_return.deductor_category,
        deductor_address=tds_return.deductor_address,
        deductor_city=tds_return.deductor_city,
        deductor_state=tds_return.deductor_state,
        deductor_pincode=tds_return.deductor_pincode,
        deductor_email=tds_return.deductor_email,
        deductor_phone=tds_return.deductor_phone,
        responsible_person_name=tds_return.responsible_person_name,
        responsible_person_designation=tds_return.responsible_person_designation,
        responsible_person_address=tds_return.responsible_person_address,
        responsible_person_pan=tds_return.responsible_person_pan,
        total_challans=tds_return.total_challans,
        total_deductees=tds_return.total_deductees,
        total_amount_paid=tds_return.total_amount_paid,
        total_tds_deducted=tds_return.total_tds_deducted,
        total_tds_deposited=tds_return.total_tds_deposited,
        total_interest=tds_return.total_interest,
        total_late_fee=tds_return.total_late_fee,
        file_generated_at=tds_return.file_generated_at,
        file_name=tds_return.file_name,
        provisional_receipt_number=tds_return.provisional_receipt_number,
        token_number=tds_return.token_number,
        acknowledgment_number=tds_return.acknowledgment_number,
        filed_date=tds_return.filed_date,
        accepted_at=tds_return.accepted_at,
        due_date=tds_return.due_date,
        is_late=tds_return.is_late,
        days_late=tds_return.days_late,
        validation_errors=tds_return.validation_errors,
        validation_warnings=tds_return.validation_warnings,
        last_validated_at=tds_return.last_validated_at,
        remarks=tds_return.remarks,
        created_at=tds_return.created_at.date() if tds_return.created_at else date.today(),
        updated_at=tds_return.updated_at.date() if tds_return.updated_at else None,
        is_active=tds_return.is_active,
    )


@router.get("", response_model=PaginatedResponse[TDSReturnListResponse], response_model_by_alias=True)
async def list_returns(
    return_type: Optional[ReturnType] = Query(None),
    financial_year_id: Optional[UUID] = Query(None),
    quarter: Optional[Quarter] = Query(None),
    status: Optional[ReturnStatus] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100, alias="pageSize"),
    current_user: User = Depends(RequirePermissions("FIN_REPORT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get TDS returns for an organization."""
    service = TDSReturnService(db)
    skip = (page - 1) * page_size
    returns, total = await service.get_by_organization(
        current_user.organization_id,
        return_type,
        financial_year_id,
        quarter,
        status,
        skip,
        page_size,
    )
    items = [_to_list_response(r) for r in returns]
    return PaginatedResponse.create(items, total, page, page_size)


@router.get("/pending", response_model=List[TDSReturnListResponse], response_model_by_alias=True)
async def get_pending_returns(
    current_user: User = Depends(RequirePermissions("FIN_REPORT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get returns pending filing."""
    service = TDSReturnService(db)
    returns = await service.get_pending(current_user.organization_id)
    return [_to_list_response(r) for r in returns]


@router.get("/due", response_model=List[TDSReturnListResponse], response_model_by_alias=True)
async def get_due_returns(
    current_user: User = Depends(RequirePermissions("FIN_REPORT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get returns due for filing."""
    service = TDSReturnService(db)
    returns = await service.get_due(current_user.organization_id)
    return [_to_list_response(r) for r in returns]


@router.post("", response_model=TDSReturnResponse, response_model_by_alias=True)
async def create_return(
    data: TDSReturnCreate,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Create a new TDS return."""
    service = TDSReturnService(db)
    tds_return = await service.create(data, current_user.id)
    return _to_response(tds_return)


@router.get("/{return_id}", response_model=TDSReturnResponse, response_model_by_alias=True)
async def get_return(
    return_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_REPORT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get TDS return by ID."""
    service = TDSReturnService(db)
    tds_return = await service.get(return_id)
    return _to_response(tds_return)


@router.put("/{return_id}", response_model=TDSReturnResponse, response_model_by_alias=True)
async def update_return(
    return_id: UUID,
    data: TDSReturnUpdate,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Update a TDS return."""
    service = TDSReturnService(db)
    tds_return = await service.update(return_id, data, current_user.id)
    return _to_response(tds_return)


@router.post("/{return_id}/validate", response_model=ReturnValidationResult, response_model_by_alias=True)
async def validate_return(
    return_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_APPROVE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Validate a TDS return."""
    service = TDSReturnService(db)
    result = await service.validate(return_id, current_user.id)
    return result


@router.post("/{return_id}/generate-file")
async def generate_file(
    return_id: UUID,
    data: ReturnFileGenerationRequest = ReturnFileGenerationRequest(),
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_APPROVE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Generate return file in NSDL format."""
    service = TDSReturnService(db)
    file_name, file_content = await service.generate_file(
        return_id,
        current_user.id,
        data.include_nil_return,
    )
    return PlainTextResponse(
        content=file_content,
        media_type="text/plain",
        headers={
            "Content-Disposition": f'attachment; filename="{file_name}"',
        },
    )


@router.post("/{return_id}/filing-details", response_model=TDSReturnResponse, response_model_by_alias=True)
async def update_filing_details(
    return_id: UUID,
    data: FilingDetailsUpdate,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_APPROVE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Update filing details after submission."""
    service = TDSReturnService(db)
    tds_return = await service.update_filing_details(return_id, data, current_user.id)
    return _to_response(tds_return)


@router.post("/{return_id}/revise", response_model=TDSReturnResponse, response_model_by_alias=True)
async def create_revision(
    return_id: UUID,
    data: RevisionRequest,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Create a revision of a filed return."""
    service = TDSReturnService(db)
    revision = await service.create_revision(return_id, data.reason, current_user.id)
    return _to_response(revision)


@router.delete("/{return_id}")
async def delete_return(
    return_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_DELETE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Delete a TDS return."""
    service = TDSReturnService(db)
    await service.delete(return_id, current_user.id)
    return {"message": "TDS return deleted successfully"}
