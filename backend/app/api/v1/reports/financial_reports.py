"""Financial Report API endpoints."""

from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import RequirePermissions
from app.models.auth.user import User
from app.services.reports.financial_report_service import FinancialReportService
from app.schemas.reports.financial_reports import (
    TrialBalanceResponse,
    ProfitLossResponse,
    BalanceSheetResponse,
    AccountLedgerResponse,
    CashFlowStatementResponse,
    DayBookResponse,
)

router = APIRouter()


@router.get("/trial-balance", response_model=TrialBalanceResponse)
async def get_trial_balance(
    organization_id: UUID = Query(..., description="Organization ID"),
    financial_year_id: UUID = Query(..., description="Financial Year ID"),
    from_date: Optional[date] = Query(None, description="Start date (defaults to FY start)"),
    to_date: Optional[date] = Query(None, description="End date (defaults to FY end)"),
    include_zero_balance: bool = Query(False, description="Include accounts with zero balance"),
    current_user: User = Depends(RequirePermissions("FIN_REPORT_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate Trial Balance report.

    Shows debit and credit balances for all accounts as of a given date.
    Totals should be equal (debit = credit) if books are balanced.
    """
    service = FinancialReportService(db)
    return await service.get_trial_balance(
        organization_id, financial_year_id, from_date, to_date, include_zero_balance
    )


@router.get("/profit-loss", response_model=ProfitLossResponse)
async def get_profit_loss(
    organization_id: UUID = Query(..., description="Organization ID"),
    financial_year_id: UUID = Query(..., description="Financial Year ID"),
    from_date: Optional[date] = Query(None, description="Start date (defaults to FY start)"),
    to_date: Optional[date] = Query(None, description="End date (defaults to FY end)"),
    current_user: User = Depends(RequirePermissions("FIN_REPORT_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate Profit & Loss Statement.

    Shows income vs expenses for a period.
    Net Profit = Total Income - Total Expenses
    """
    service = FinancialReportService(db)
    return await service.get_profit_loss(
        organization_id, financial_year_id, from_date, to_date
    )


@router.get("/balance-sheet", response_model=BalanceSheetResponse)
async def get_balance_sheet(
    organization_id: UUID = Query(..., description="Organization ID"),
    financial_year_id: UUID = Query(..., description="Financial Year ID"),
    as_on_date: Optional[date] = Query(None, description="Balance sheet date (defaults to FY end)"),
    current_user: User = Depends(RequirePermissions("FIN_REPORT_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate Balance Sheet.

    Shows Assets, Liabilities, and Equity as of a given date.
    Assets = Liabilities + Equity + Net Profit/Loss
    """
    service = FinancialReportService(db)
    return await service.get_balance_sheet(
        organization_id, financial_year_id, as_on_date
    )


@router.get("/account-ledger/{account_id}", response_model=AccountLedgerResponse)
async def get_account_ledger(
    account_id: UUID,
    from_date: date = Query(..., description="Start date"),
    to_date: date = Query(..., description="End date"),
    current_user: User = Depends(RequirePermissions("FIN_REPORT_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate Account Ledger (detailed transactions).

    Shows all transactions for a specific account within a date range.
    Includes opening balance, all voucher entries, and closing balance.
    """
    service = FinancialReportService(db)
    return await service.get_account_ledger(account_id, from_date, to_date)


@router.get("/cash-flow-statement", response_model=CashFlowStatementResponse)
async def get_cash_flow_statement(
    organization_id: UUID = Query(..., description="Organization ID"),
    financial_year_id: UUID = Query(..., description="Financial Year ID"),
    from_date: Optional[date] = Query(None, description="Start date (defaults to FY start)"),
    to_date: Optional[date] = Query(None, description="End date (defaults to FY end)"),
    current_user: User = Depends(RequirePermissions("FIN_REPORT_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate Cash Flow Statement (Indirect Method).

    Shows cash flows from:
    - Operating Activities (Net Profit + adjustments)
    - Investing Activities (Fixed assets changes)
    - Financing Activities (Loans, capital changes)
    """
    service = FinancialReportService(db)
    return await service.get_cash_flow_statement(
        organization_id, financial_year_id, from_date, to_date
    )


@router.get("/day-book", response_model=DayBookResponse)
async def get_day_book(
    organization_id: UUID = Query(..., description="Organization ID"),
    from_date: date = Query(..., description="Start date"),
    to_date: date = Query(..., description="End date"),
    voucher_type_id: Optional[UUID] = Query(None, description="Filter by voucher type"),
    current_user: User = Depends(RequirePermissions("FIN_REPORT_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate Day Book / Journal Register.

    Shows all vouchers posted within a date range.
    Optionally filter by voucher type.
    """
    service = FinancialReportService(db)
    return await service.get_day_book(
        organization_id, from_date, to_date, voucher_type_id
    )
