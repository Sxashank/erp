"""Year-End Closing API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import RequirePermissions, get_current_user
from app.models.auth.user import User
from app.services.finance.year_end_service import YearEndService
from app.schemas.finance.year_end import (
    YearEndClosingPreviewResponse,
    YearEndClosingPreviewItem,
    YearEndClosingRequest,
    YearEndClosingResponse,
    ReopenYearRequest,
    ReopenYearResponse,
)

router = APIRouter()


@router.get(
    "/preview/{financial_year_id}",
    response_model=YearEndClosingPreviewResponse,
)
async def get_year_end_preview(
    financial_year_id: UUID,
    current_user: User = Depends(RequirePermissions("FIN_YEAR_CLOSE")),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a preview of the year-end closing process.

    Shows:
    - Net Profit/Loss calculation
    - Retained Earnings account
    - Accounts to carry forward with closing balances
    - Any validation errors or warnings
    """
    service = YearEndService(db)
    preview = await service.get_closing_preview(financial_year_id)

    return YearEndClosingPreviewResponse(
        can_close=preview.can_close,
        net_profit_loss=preview.net_profit_loss,
        profit_loss_type=preview.profit_loss_type,
        retained_earnings_account_id=str(preview.retained_earnings_account_id) if preview.retained_earnings_account_id else None,
        retained_earnings_account_name=preview.retained_earnings_account_name,
        accounts_to_carry_forward=[
            YearEndClosingPreviewItem(**item)
            for item in preview.accounts_to_carry_forward
        ],
        total_accounts=len(preview.accounts_to_carry_forward),
        unclosed_periods=preview.unclosed_periods,
        unposted_vouchers=preview.unposted_vouchers,
        errors=preview.errors,
        warnings=preview.warnings,
    )


@router.post(
    "/execute",
    response_model=YearEndClosingResponse,
)
async def execute_year_end_closing(
    request: YearEndClosingRequest,
    current_user: User = Depends(RequirePermissions("FIN_YEAR_CLOSE")),
    db: AsyncSession = Depends(get_db),
):
    """
    Execute the year-end closing process.

    This will:
    1. Create a closing voucher to transfer P&L to Retained Earnings
    2. Calculate closing balances for all Balance Sheet accounts
    3. Update opening balances in the new financial year
    4. Mark the old financial year as closed
    5. Set the new financial year as current
    """
    service = YearEndService(db)
    result = await service.execute_year_end_closing(
        financial_year_id=request.source_financial_year_id,
        new_financial_year_id=request.target_financial_year_id,
        user_id=current_user.id,
        skip_validations=request.skip_validations,
    )

    if result.success:
        await db.commit()
    else:
        await db.rollback()

    return YearEndClosingResponse(
        success=result.success,
        message=result.message,
        net_profit_loss=result.net_profit_loss,
        profit_loss_type=result.profit_loss_type,
        closing_voucher_id=str(result.closing_voucher_id) if result.closing_voucher_id else None,
        closing_voucher_number=result.closing_voucher_number,
        accounts_carried_forward=result.accounts_carried_forward,
        new_year_id=str(result.new_year_id) if result.new_year_id else None,
        errors=result.errors,
        warnings=result.warnings,
    )


@router.post(
    "/reopen/{financial_year_id}",
    response_model=ReopenYearResponse,
)
async def reopen_financial_year(
    financial_year_id: UUID,
    request: ReopenYearRequest,
    current_user: User = Depends(RequirePermissions("FIN_YEAR_CLOSE")),
    db: AsyncSession = Depends(get_db),
):
    """
    Reopen a closed financial year.

    This is an administrative action that should be used with caution.
    Requires a valid reason for audit trail.
    """
    service = YearEndService(db)
    fy = await service.reopen_year(
        financial_year_id=financial_year_id,
        user_id=current_user.id,
        reason=request.reason,
    )

    await db.commit()

    return ReopenYearResponse(
        success=True,
        message=f"Financial year '{fy.name}' has been reopened successfully.",
        financial_year_id=str(fy.id),
        financial_year_name=fy.name,
    )
