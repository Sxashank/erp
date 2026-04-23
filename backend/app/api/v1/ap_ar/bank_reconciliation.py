"""Bank Statement and Reconciliation API endpoints."""

from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
# from app.core.permissions import RequirePermissions
from app.core.responses import PaginatedResponse
from app.models.auth.user import User
from app.models.ap_ar.bank_reconciliation import (
    ReconciliationStatus,
    StatementTransactionType,
    BankReconciliationStatus
)
from app.schemas.ap_ar.bank_reconciliation import (
    BankStatementImport,
    BankStatementImportRow,
    BankStatementResponse,
    BankStatementListResponse,
    BankStatementMatchCreate,
    BankStatementMatchResponse,
    BankReconciliationCreate,
    BankReconciliationUpdate,
    BankReconciliationResponse,
    BRSReportResponse,
    ReconciliationWorkspaceResponse
)
from app.services.ap_ar.bank_reconciliation_service import (
    BankStatementService,
    BankReconciliationService
)
from app.services.finance.account_service import AccountService

router = APIRouter(prefix="/bank-reconciliation", tags=["Bank Reconciliation"])


# ============ Bank Statement Endpoints ============


@router.post(
    "/statements/import",
    summary="Import bank statements",

)
async def import_bank_statements(
    data: BankStatementImport,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Import bank statements from parsed data."""
    service = BankStatementService(db)
    success, errors, messages = await service.import_statements(
        data=data,
        user_id=current_user.id,
    )
    return {
        "success_count": success,
        "error_count": errors,
        "messages": messages,
    }


@router.post(
    "/statements/parse-csv",
    summary="Parse CSV bank statement",

)
async def parse_csv_statement(
    file: UploadFile = File(...),
    date_column: str = Form("Date"),
    debit_column: str = Form("Withdrawal"),
    credit_column: str = Form("Deposit"),
    reference_column: str = Form("Reference"),
    description_column: str = Form("Description"),
    balance_column: str = Form("Balance"),
    cheque_column: str = Form("Cheque No"),
    utr_column: str = Form("UTR"),
    db: AsyncSession = Depends(get_db)
) -> list[dict]:
    """Parse a CSV file and return parsed rows for preview."""
    content = await file.read()
    csv_content = content.decode("utf-8")

    column_mapping = {
        "transaction_date": date_column,
        "debit_amount": debit_column,
        "credit_amount": credit_column,
        "reference_number": reference_column,
        "description": description_column,
        "running_balance": balance_column,
        "cheque_number": cheque_column,
        "utr_number": utr_column,
    }

    service = BankStatementService(db)
    rows = await service.parse_csv_statement(csv_content, column_mapping)
    return [row.model_dump() for row in rows]


@router.get(
    "/statements",
    response_model=PaginatedResponse[BankStatementListResponse],
    summary="List bank statements",

)
async def list_bank_statements(
    bank_account_id: UUID,
    organization_id: UUID,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    reconciliation_status: Optional[ReconciliationStatus] = None,
    transaction_type: Optional[StatementTransactionType] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[BankStatementListResponse]:
    """List bank statements with filters."""
    service = BankStatementService(db)
    statements, total = await service.list_statements(
        bank_account_id=bank_account_id,
        organization_id=organization_id,
        from_date=from_date,
        to_date=to_date,
        reconciliation_status=reconciliation_status,
        transaction_type=transaction_type,
        search=search,
        skip=skip,
        limit=limit,
    )
    # Convert skip/limit to page/page_size
    page = (skip // limit) + 1 if limit > 0 else 1
    return PaginatedResponse.create(
        items=[BankStatementListResponse.model_validate(s) for s in statements],
        total=total,
        page=page,
        page_size=limit,
    )


@router.get(
    "/statements/{statement_id}",
    response_model=BankStatementResponse,
    summary="Get bank statement",

)
async def get_bank_statement(
    statement_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> BankStatementResponse:
    """Get a bank statement by ID."""
    service = BankStatementService(db)
    statement = await service.get_statement(statement_id)
    if not statement:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Bank statement not found")
    return BankStatementResponse.model_validate(statement)


@router.delete(
    "/statements/{statement_id}",
    summary="Delete bank statement",

)
async def delete_bank_statement(
    statement_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """Delete a bank statement (soft delete)."""
    service = BankStatementService(db)
    await service.delete_statement(statement_id, current_user.id)
    return {"message": "Bank statement deleted successfully"}


# ============ Matching Endpoints ============


@router.post(
    "/match",
    response_model=BankStatementMatchResponse,
    summary="Match statement with voucher",

)
async def match_statement_with_voucher(
    data: BankStatementMatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> BankStatementMatchResponse:
    """Match a bank statement entry with a voucher."""
    service = BankReconciliationService(db)
    match = await service.match_statement_with_voucher(data, current_user.id)
    return BankStatementMatchResponse.model_validate(match)


@router.delete(
    "/match/{match_id}",
    summary="Unmatch statement",

)
async def unmatch_statement(
    match_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Remove a match between statement and voucher."""
    service = BankReconciliationService(db)
    await service.unmatch_statement(match_id)
    return {"message": "Match removed successfully"}


@router.post(
    "/auto-match",
    summary="Auto-match statements",

)
async def auto_match_statements(
    bank_account_id: UUID,
    from_date: date,
    to_date: date,
    date_tolerance: int = Query(7, ge=1, le=30, description="Max days difference for date matching"),
    match_by_reference: bool = Query(True, description="Match by reference number"),
    match_by_cheque: bool = Query(True, description="Match by cheque number"),
    match_by_utr: bool = Query(True, description="Match by UTR number"),
    match_by_amount_only: bool = Query(True, description="Fall back to amount-only matching"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Automatically match bank statements with vouchers using multiple strategies:
    1. Reference number match (highest priority)
    2. Cheque number match
    3. UTR number match
    4. Amount + date proximity match (fallback)
    """
    service = BankReconciliationService(db)
    matched, messages = await service.auto_match_statements(
        bank_account_id=bank_account_id,
        from_date=from_date,
        to_date=to_date,
        user_id=current_user.id,
        date_tolerance=date_tolerance,
        match_by_reference=match_by_reference,
        match_by_cheque=match_by_cheque,
        match_by_utr=match_by_utr,
        match_by_amount_only=match_by_amount_only,
    )
    return {
        "matched_count": matched,
        "messages": messages,
        "settings": {
            "date_tolerance": date_tolerance,
            "match_by_reference": match_by_reference,
            "match_by_cheque": match_by_cheque,
            "match_by_utr": match_by_utr,
            "match_by_amount_only": match_by_amount_only,
        }
    }


# ============ Reconciliation Workspace Endpoints ============


@router.get(
    "/workspace",
    response_model=ReconciliationWorkspaceResponse,
    summary="Get reconciliation workspace",

)
async def get_reconciliation_workspace(
    bank_account_id: UUID,
    from_date: date,
    to_date: date,
    db: AsyncSession = Depends(get_db)
) -> ReconciliationWorkspaceResponse:
    """Get all data needed for reconciliation workspace."""
    # Get bank account name
    account_service = AccountService(db)
    account = await account_service.get_account(bank_account_id)
    if not account:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Bank account not found")

    service = BankReconciliationService(db)
    return await service.get_reconciliation_workspace(
        bank_account_id=bank_account_id,
        from_date=from_date,
        to_date=to_date,
        bank_account_name=account.name,
    )


# ============ Reconciliation Session Endpoints ============


@router.get(
    "",
    response_model=PaginatedResponse[BankReconciliationResponse],
    summary="List reconciliations",

)
async def list_reconciliations(
    bank_account_id: UUID,
    organization_id: UUID,
    status: Optional[BankReconciliationStatus] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[BankReconciliationResponse]:
    """List bank reconciliations with filters."""
    service = BankReconciliationService(db)
    reconciliations, total = await service.list_reconciliations(
        bank_account_id=bank_account_id,
        organization_id=organization_id,
        status=status,
        from_date=from_date,
        to_date=to_date,
        skip=skip,
        limit=limit,
    )
    # Convert skip/limit to page/page_size
    page = (skip // limit) + 1 if limit > 0 else 1
    return PaginatedResponse.create(
        items=[BankReconciliationResponse.model_validate(r) for r in reconciliations],
        total=total,
        page=page,
        page_size=limit,
    )


@router.post(
    "",
    response_model=BankReconciliationResponse,
    summary="Create reconciliation",

)
async def create_reconciliation(
    data: BankReconciliationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> BankReconciliationResponse:
    """Create a new bank reconciliation session."""
    service = BankReconciliationService(db)
    recon = await service.create_reconciliation(data, current_user.id)
    return BankReconciliationResponse.model_validate(recon)


@router.get(
    "/{reconciliation_id}",
    response_model=BankReconciliationResponse,
    summary="Get reconciliation",

)
async def get_reconciliation(
    reconciliation_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> BankReconciliationResponse:
    """Get a reconciliation by ID."""
    service = BankReconciliationService(db)
    recon = await service.get_reconciliation(reconciliation_id)
    if not recon:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Reconciliation not found")
    return BankReconciliationResponse.model_validate(recon)


@router.get(
    "/latest/{bank_account_id}",
    response_model=Optional[BankReconciliationResponse],
    summary="Get latest reconciliation",

)
async def get_latest_reconciliation(
    bank_account_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> Optional[BankReconciliationResponse]:
    """Get the latest reconciliation for a bank account."""
    service = BankReconciliationService(db)
    recon = await service.get_latest_reconciliation(bank_account_id)
    if not recon:
        return None
    return BankReconciliationResponse.model_validate(recon)


@router.put(
    "/{reconciliation_id}",
    response_model=BankReconciliationResponse,
    summary="Update reconciliation",

)
async def update_reconciliation(
    reconciliation_id: UUID,
    data: BankReconciliationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> BankReconciliationResponse:
    """Update a bank reconciliation."""
    service = BankReconciliationService(db)
    recon = await service.update_reconciliation(reconciliation_id, data, current_user.id)
    return BankReconciliationResponse.model_validate(recon)


@router.post(
    "/{reconciliation_id}/complete",
    response_model=BankReconciliationResponse,
    summary="Complete reconciliation",

)
async def complete_reconciliation(
    reconciliation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> BankReconciliationResponse:
    """Complete a bank reconciliation."""
    service = BankReconciliationService(db)
    recon = await service.complete_reconciliation(reconciliation_id, current_user.id)
    return BankReconciliationResponse.model_validate(recon)


# ============ BRS Report Endpoints ============


@router.get(
    "/report/brs",
    response_model=BRSReportResponse,
    summary="Generate BRS report",

)
async def generate_brs_report(
    bank_account_id: UUID,
    reconciliation_date: date,
    from_date: date,
    to_date: date,
    statement_opening_balance: Decimal,
    statement_closing_balance: Decimal,
    book_opening_balance: Decimal,
    book_closing_balance: Decimal,
    db: AsyncSession = Depends(get_db)
) -> BRSReportResponse:
    """Generate Bank Reconciliation Statement report."""
    # Get bank account name
    account_service = AccountService(db)
    account = await account_service.get_account(bank_account_id)
    if not account:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Bank account not found")

    service = BankReconciliationService(db)
    return await service.generate_brs_report(
        bank_account_id=bank_account_id,
        bank_account_name=account.name,
        reconciliation_date=reconciliation_date,
        from_date=from_date,
        to_date=to_date,
        statement_opening_balance=statement_opening_balance,
        statement_closing_balance=statement_closing_balance,
        book_opening_balance=book_opening_balance,
        book_closing_balance=book_closing_balance,
    )
