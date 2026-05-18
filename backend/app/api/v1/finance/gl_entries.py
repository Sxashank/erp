"""GL Entry API endpoints for audit trail and reporting."""

from datetime import date
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import RequirePermissions, get_db_with_tenant
from app.models.auth.user import User
from app.services.finance.gl_posting_service import GLPostingService
from app.schemas.finance.gl_entry import (
    GLEntryResponse,
    GLEntryDetailResponse,
    GLAccountStatement,
    GLPartyStatement,
    GLTrialBalanceResponse,
    GLDayBookResponse,
    GLCostCenterSummary,
    GLSourceSummary,
    GLEntryFilter,
)
from app.schemas.base import PaginatedResponse
from app.core.constants import PartyType, GLEntryType, GLEntrySourceType
from app.core.exceptions import NotFoundException

router = APIRouter()


# =============================================================================
# GL Entry Queries
# =============================================================================


@router.get("", response_model=PaginatedResponse[GLEntryResponse], response_model_by_alias=True)
async def list_gl_entries(
    account_id: Optional[UUID] = Query(None, description="Filter by account"),
    voucher_id: Optional[UUID] = Query(None, description="Filter by voucher"),
    voucher_number: Optional[str] = Query(None, description="Filter by voucher number (partial match)"),
    date_from: Optional[date] = Query(None, description="Start date"),
    date_to: Optional[date] = Query(None, description="End date"),
    entry_type: Optional[GLEntryType] = Query(None, description="Filter by entry type"),
    source_type: Optional[GLEntrySourceType] = Query(None, description="Filter by source type"),
    party_type: Optional[PartyType] = Query(None, description="Filter by party type"),
    party_id: Optional[UUID] = Query(None, description="Filter by party"),
    cost_center_id: Optional[UUID] = Query(None, description="Filter by cost center"),
    financial_year_id: Optional[UUID] = Query(None, description="Filter by financial year"),
    period_id: Optional[UUID] = Query(None, description="Filter by period"),
    include_reversed: bool = Query(False, description="Include reversed entries"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get paginated list of GL entries with filters.
    Requires FIN_VOUCHER_VIEW permission.
    """
    service = GLPostingService(db)
    skip = (page - 1) * page_size

    filters = {
        "account_id": account_id,
        "voucher_id": voucher_id,
        "voucher_number": voucher_number,
        "date_from": date_from,
        "date_to": date_to,
        "entry_type": entry_type,
        "source_type": source_type,
        "party_type": party_type,
        "party_id": party_id,
        "cost_center_id": cost_center_id,
        "financial_year_id": financial_year_id,
        "period_id": period_id,
        "include_reversed": include_reversed,
    }

    # Remove None values
    filters = {k: v for k, v in filters.items() if v is not None}

    entries, total = await service.search_entries(
        organization_id=current_user.organization_id,
        filters=filters,
        skip=skip,
        limit=page_size,
    )

    items = [_entry_to_response(e) for e in entries]
    return PaginatedResponse.create(items, total, page, page_size)


@router.get("/{entry_id}", response_model=GLEntryDetailResponse, response_model_by_alias=True)
async def get_gl_entry(
    entry_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get a single GL entry by ID.
    Requires FIN_VOUCHER_VIEW permission.
    """
    service = GLPostingService(db)
    entry = await service.get_entry(entry_id)

    if not entry:
        raise NotFoundException(detail="GL entry not found", error_code="GL_ENTRY_NOT_FOUND")

    return _entry_to_detail_response(entry)


@router.get("/voucher/{voucher_id}", response_model=List[GLEntryResponse], response_model_by_alias=True)
async def get_entries_by_voucher(
    voucher_id: UUID,
    include_reversed: bool = Query(False),
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get all GL entries for a voucher.
    Requires FIN_VOUCHER_VIEW permission.
    """
    service = GLPostingService(db)
    entries = await service.get_entries_by_voucher(voucher_id, include_reversed)
    return [_entry_to_response(e) for e in entries]


@router.get("/source/{source_type}/{source_id}", response_model=List[GLEntryResponse], response_model_by_alias=True)
async def get_entries_by_source(
    source_type: GLEntrySourceType,
    source_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_VOUCHER_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get GL entries by source document (purchase bill, sales invoice, etc.).
    Requires FIN_VOUCHER_VIEW permission.
    """
    service = GLPostingService(db)
    entries = await service.get_entries_by_source(source_type, source_id)
    return [_entry_to_response(e) for e in entries]


# =============================================================================
# Reports
# =============================================================================


@router.get("/reports/account-statement", response_model=GLAccountStatement, response_model_by_alias=True)
async def get_account_statement(
    account_id: UUID = Query(..., description="Account ID"),
    date_from: date = Query(..., description="Start date"),
    date_to: date = Query(..., description="End date"),
    include_reversed: bool = Query(False),
    include_opening_balance: bool = Query(True),
    current_user: User = Depends(RequirePermissions("FIN_REPORT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Generate account statement with running balance.
    Requires FIN_REPORT_VIEW permission.
    """
    service = GLPostingService(db)
    return await service.get_account_statement(
        account_id=account_id,
        date_from=date_from,
        date_to=date_to,
        include_reversed=include_reversed,
        include_opening_balance=include_opening_balance,
    )


@router.get("/reports/party-statement", response_model=GLPartyStatement, response_model_by_alias=True)
async def get_party_statement(
    party_type: PartyType = Query(..., description="Party type"),
    party_id: UUID = Query(..., description="Party ID"),
    date_from: date = Query(..., description="Start date"),
    date_to: date = Query(..., description="End date"),
    include_reversed: bool = Query(False),
    include_opening_balance: bool = Query(True),
    current_user: User = Depends(RequirePermissions("FIN_REPORT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Generate party (sub-ledger) statement.
    Requires FIN_REPORT_VIEW permission.
    """
    service = GLPostingService(db)
    return await service.get_party_statement(
        party_type=party_type,
        party_id=party_id,
        date_from=date_from,
        date_to=date_to,
        include_reversed=include_reversed,
        include_opening_balance=include_opening_balance,
    )


@router.get("/reports/trial-balance", response_model=GLTrialBalanceResponse, response_model_by_alias=True)
async def get_trial_balance(
    financial_year_id: UUID = Query(..., description="Financial year ID"),
    period_id: Optional[UUID] = Query(None, description="Period ID (optional)"),
    as_of_date: Optional[date] = Query(None, description="As of date (optional)"),
    include_zero_balance: bool = Query(False, description="Include accounts with zero balance"),
    current_user: User = Depends(RequirePermissions("FIN_REPORT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Generate trial balance report.
    Requires FIN_REPORT_VIEW permission.
    """
    service = GLPostingService(db)
    return await service.get_trial_balance(
        organization_id=current_user.organization_id,
        financial_year_id=financial_year_id,
        period_id=period_id,
        as_of_date=as_of_date,
        include_zero_balance=include_zero_balance,
    )


@router.get("/reports/day-book", response_model=GLDayBookResponse, response_model_by_alias=True)
async def get_day_book(
    for_date: date = Query(..., description="Date for day book"),
    include_reversed: bool = Query(False),
    current_user: User = Depends(RequirePermissions("FIN_REPORT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Generate day book (daily transaction summary).
    Requires FIN_REPORT_VIEW permission.
    """
    service = GLPostingService(db)
    return await service.get_day_book(
        organization_id=current_user.organization_id,
        for_date=for_date,
        include_reversed=include_reversed,
    )


@router.get("/reports/cost-center-summary", response_model=List[GLCostCenterSummary], response_model_by_alias=True)
async def get_cost_center_summary(
    date_from: Optional[date] = Query(None, description="Start date"),
    date_to: Optional[date] = Query(None, description="End date"),
    include_reversed: bool = Query(False),
    current_user: User = Depends(RequirePermissions("FIN_REPORT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get summary by cost center.
    Requires FIN_REPORT_VIEW permission.
    """
    service = GLPostingService(db)
    return await service.get_cost_center_summary(
        organization_id=current_user.organization_id,
        date_from=date_from,
        date_to=date_to,
        include_reversed=include_reversed,
    )


@router.get("/reports/source-summary", response_model=List[GLSourceSummary], response_model_by_alias=True)
async def get_source_summary(
    date_from: Optional[date] = Query(None, description="Start date"),
    date_to: Optional[date] = Query(None, description="End date"),
    include_reversed: bool = Query(False),
    current_user: User = Depends(RequirePermissions("FIN_REPORT_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """
    Get summary by source type.
    Requires FIN_REPORT_VIEW permission.
    """
    service = GLPostingService(db)
    return await service.get_source_summary(
        organization_id=current_user.organization_id,
        date_from=date_from,
        date_to=date_to,
        include_reversed=include_reversed,
    )


# =============================================================================
# Helper Functions
# =============================================================================


def _entry_to_response(entry) -> GLEntryResponse:
    """Convert GLEntry model to response schema."""
    return GLEntryResponse(
        id=entry.id,
        voucher_id=entry.voucher_id,
        voucher_number=entry.voucher_number,
        voucher_date=entry.voucher_date,
        entry_type=entry.entry_type,
        source_type=entry.source_type,
        source_reference=entry.source_reference,
        account_id=entry.account_id,
        account_code=entry.account_code,
        account_name=entry.account_name,
        debit_amount=entry.debit_amount,
        credit_amount=entry.credit_amount,
        balance_type=entry.balance_type,
        currency_code=entry.currency_code,
        party_type=entry.party_type,
        party_id=entry.party_id,
        party_name=entry.party_name,
        cost_center_id=entry.cost_center_id,
        cost_center_code=entry.cost_center_code,
        narration=entry.narration,
        reference_number=entry.reference_number,
        posting_date=entry.posting_date,
        is_reversed=entry.is_reversed,
        organization_id=entry.organization_id,
    )


def _entry_to_detail_response(entry) -> GLEntryDetailResponse:
    """Convert GLEntry model to detail response schema."""
    return GLEntryDetailResponse(
        id=entry.id,
        voucher_id=entry.voucher_id,
        voucher_line_id=entry.voucher_line_id,
        voucher_number=entry.voucher_number,
        voucher_date=entry.voucher_date,
        entry_type=entry.entry_type,
        source_type=entry.source_type,
        source_reference=entry.source_reference,
        source_id=entry.source_id,
        account_id=entry.account_id,
        account_code=entry.account_code,
        account_name=entry.account_name,
        debit_amount=entry.debit_amount,
        credit_amount=entry.credit_amount,
        balance_type=entry.balance_type,
        currency_code=entry.currency_code,
        exchange_rate=entry.exchange_rate,
        base_debit_amount=entry.base_debit_amount,
        base_credit_amount=entry.base_credit_amount,
        party_type=entry.party_type,
        party_id=entry.party_id,
        party_name=entry.party_name,
        cost_center_id=entry.cost_center_id,
        cost_center_code=entry.cost_center_code,
        financial_year_id=entry.financial_year_id,
        period_id=entry.period_id,
        narration=entry.narration,
        reference_number=entry.reference_number,
        reference_date=entry.reference_date,
        reversal_entry_id=entry.reversal_entry_id,
        original_entry_id=entry.original_entry_id,
        reversal_date=entry.reversal_date,
        posting_date=entry.posting_date,
        posted_by=entry.posted_by,
        running_balance=entry.running_balance,
        running_balance_type=entry.running_balance_type,
        sequence_number=entry.sequence_number,
        is_reversed=entry.is_reversed,
        organization_id=entry.organization_id,
        unit_id=entry.unit_id,
        created_at=entry.created_at,
        metadata=entry.metadata,
    )
