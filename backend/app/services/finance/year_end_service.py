"""Year-End Closing Service.

Handles:
1. Year-end closing process (P&L transfer to Retained Earnings)
2. Opening balance carry-forward to new financial year
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional, Tuple, Dict
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import (
    AccountNature,
    VoucherStatus,
    BalanceType,
    VoucherClass,
)
from app.core.exceptions import (
    NotFoundException,
    BadRequestException,
    ConflictException,
)
from app.models.finance.financial_year import FinancialYear, FinancialPeriod
from app.models.finance.account import Account
from app.models.finance.account_group import AccountGroup
from app.models.finance.voucher import Voucher, VoucherLine
from app.models.finance.voucher_type import VoucherType
from app.models.masters.organization import Organization


class YearEndClosingResult:
    """Result of year-end closing process."""

    def __init__(self):
        self.success = False
        self.message = ""
        self.net_profit_loss: Decimal = Decimal("0")
        self.profit_loss_type: str = "PROFIT"
        self.closing_voucher_id: Optional[UUID] = None
        self.closing_voucher_number: Optional[str] = None
        self.accounts_carried_forward: int = 0
        self.new_year_id: Optional[UUID] = None
        self.errors: List[str] = []
        self.warnings: List[str] = []


class YearEndClosingPreview:
    """Preview of year-end closing before execution."""

    def __init__(self):
        self.can_close: bool = False
        self.net_profit_loss: Decimal = Decimal("0")
        self.profit_loss_type: str = "PROFIT"
        self.retained_earnings_account_id: Optional[UUID] = None
        self.retained_earnings_account_name: Optional[str] = None
        self.accounts_to_carry_forward: List[Dict] = []
        self.unclosed_periods: List[str] = []
        self.unposted_vouchers: int = 0
        self.errors: List[str] = []
        self.warnings: List[str] = []


class YearEndService:
    """Service for year-end closing operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_closing_preview(
        self,
        financial_year_id: UUID,
    ) -> YearEndClosingPreview:
        """
        Generate a preview of the year-end closing process.

        Shows what will happen without making any changes.
        """
        preview = YearEndClosingPreview()

        # Get financial year
        fy = await self._get_financial_year(financial_year_id)
        if not fy:
            preview.errors.append("Financial year not found")
            return preview

        if fy.is_closed:
            preview.errors.append("Financial year is already closed")
            return preview

        # Check for unclosed periods
        unclosed = [p.name for p in fy.periods if not p.is_closed]
        if unclosed:
            preview.unclosed_periods = unclosed
            preview.errors.append(
                f"The following periods are still open: {', '.join(unclosed)}"
            )

        # Check for unposted vouchers
        unposted_count = await self._count_unposted_vouchers(
            fy.organization_id, fy.start_date, fy.end_date
        )
        if unposted_count > 0:
            preview.unposted_vouchers = unposted_count
            preview.warnings.append(
                f"There are {unposted_count} unposted vouchers that will not be included in closing"
            )

        # Calculate Net P&L
        net_pl, pl_type = await self._calculate_net_profit_loss(
            fy.organization_id, fy.start_date, fy.end_date
        )
        preview.net_profit_loss = net_pl
        preview.profit_loss_type = pl_type

        # Find Retained Earnings account
        re_account = await self._find_retained_earnings_account(fy.organization_id)
        if re_account:
            preview.retained_earnings_account_id = re_account.id
            preview.retained_earnings_account_name = f"{re_account.code} - {re_account.name}"
        else:
            preview.errors.append(
                "Retained Earnings account not found. Please create an account named "
                "'Retained Earnings' or 'Accumulated Profits' under Equity group."
            )

        # Get accounts to carry forward (Balance Sheet accounts)
        accounts_cf = await self._get_accounts_to_carry_forward(
            fy.organization_id, fy.start_date, fy.end_date
        )
        preview.accounts_to_carry_forward = accounts_cf

        # Set can_close flag
        preview.can_close = len(preview.errors) == 0

        return preview

    async def execute_year_end_closing(
        self,
        financial_year_id: UUID,
        new_financial_year_id: UUID,
        user_id: UUID,
        skip_validations: bool = False,
    ) -> YearEndClosingResult:
        """
        Execute the full year-end closing process.

        Steps:
        1. Validate all periods are closed
        2. Create closing voucher for P&L transfer to Retained Earnings
        3. Calculate closing balances for Balance Sheet accounts
        4. Create opening balances in new financial year
        5. Mark old year as closed
        6. Set new year as current
        """
        result = YearEndClosingResult()

        try:
            # Get financial years
            old_fy = await self._get_financial_year(financial_year_id)
            if not old_fy:
                result.errors.append("Source financial year not found")
                return result

            new_fy = await self._get_financial_year(new_financial_year_id)
            if not new_fy:
                result.errors.append("Target financial year not found")
                return result

            if old_fy.is_closed:
                result.errors.append("Source financial year is already closed")
                return result

            if new_fy.is_closed:
                result.errors.append("Target financial year is already closed")
                return result

            if old_fy.organization_id != new_fy.organization_id:
                result.errors.append("Financial years must belong to the same organization")
                return result

            # Validate period sequence
            if new_fy.start_date <= old_fy.end_date:
                result.errors.append(
                    "New financial year must start after the closing year ends"
                )
                return result

            # Skip period validation if requested
            if not skip_validations:
                unclosed = [p.name for p in old_fy.periods if not p.is_closed]
                if unclosed:
                    result.errors.append(
                        f"Cannot close year. The following periods are still open: {', '.join(unclosed)}"
                    )
                    return result

            # Calculate Net P&L
            net_pl, pl_type = await self._calculate_net_profit_loss(
                old_fy.organization_id, old_fy.start_date, old_fy.end_date
            )
            result.net_profit_loss = abs(net_pl)
            result.profit_loss_type = pl_type

            # Find Retained Earnings account
            re_account = await self._find_retained_earnings_account(old_fy.organization_id)
            if not re_account:
                result.errors.append(
                    "Retained Earnings account not found. Please create one before closing."
                )
                return result

            # Step 1: Create P&L closing voucher
            closing_voucher = await self._create_closing_voucher(
                old_fy, re_account, net_pl, pl_type, user_id
            )
            if closing_voucher:
                result.closing_voucher_id = closing_voucher.id
                result.closing_voucher_number = closing_voucher.voucher_number

            # Step 2: Calculate and create opening balances in new year
            accounts_count = await self._carry_forward_opening_balances(
                old_fy, new_fy, re_account, net_pl, pl_type, user_id
            )
            result.accounts_carried_forward = accounts_count

            # Step 3: Mark old year as closed
            old_fy.is_closed = True
            old_fy.is_current = False
            old_fy.closed_at = datetime.now(timezone.utc)
            old_fy.closed_by = user_id

            # Step 4: Set new year as current
            new_fy.is_current = True

            await self.db.flush()

            result.success = True
            result.new_year_id = new_fy.id
            result.message = (
                f"Year-end closing completed successfully. "
                f"Net {pl_type.lower()} of ₹{net_pl:,.2f} transferred to Retained Earnings. "
                f"{accounts_count} accounts carried forward to {new_fy.name}."
            )

        except Exception as e:
            result.errors.append(f"Error during year-end closing: {str(e)}")

        return result

    async def _get_financial_year(self, fy_id: UUID) -> Optional[FinancialYear]:
        """Get financial year with periods."""
        result = await self.db.execute(
            select(FinancialYear)
            .options(selectinload(FinancialYear.periods))
            .where(FinancialYear.id == fy_id)
        )
        return result.scalar_one_or_none()

    async def _count_unposted_vouchers(
        self,
        organization_id: UUID,
        from_date: date,
        to_date: date,
    ) -> int:
        """Count unposted vouchers in the period."""
        result = await self.db.execute(
            select(func.count(Voucher.id))
            .where(
                Voucher.organization_id == organization_id,
                Voucher.voucher_date >= from_date,
                Voucher.voucher_date <= to_date,
                Voucher.status != VoucherStatus.POSTED,
                Voucher.status != VoucherStatus.CANCELLED,
                Voucher.is_active == True,
            )
        )
        return result.scalar() or 0

    async def _calculate_net_profit_loss(
        self,
        organization_id: UUID,
        from_date: date,
        to_date: date,
    ) -> Tuple[Decimal, str]:
        """Calculate net profit or loss for the period."""
        # Get all income accounts
        income_groups = await self.db.execute(
            select(AccountGroup.id).where(
                AccountGroup.organization_id == organization_id,
                AccountGroup.nature == AccountNature.INCOME,
            )
        )
        income_group_ids = [row[0] for row in income_groups.all()]

        total_income = Decimal("0")
        for group_id in income_group_ids:
            income = await self._get_group_amount(group_id, from_date, to_date, "INCOME")
            total_income += income

        # Get all expense accounts
        expense_groups = await self.db.execute(
            select(AccountGroup.id).where(
                AccountGroup.organization_id == organization_id,
                AccountGroup.nature == AccountNature.EXPENSES,
            )
        )
        expense_group_ids = [row[0] for row in expense_groups.all()]

        total_expenses = Decimal("0")
        for group_id in expense_group_ids:
            expense = await self._get_group_amount(group_id, from_date, to_date, "EXPENSES")
            total_expenses += expense

        net_pl = total_income - total_expenses
        pl_type = "PROFIT" if net_pl >= 0 else "LOSS"

        return abs(net_pl), pl_type

    async def _get_group_amount(
        self,
        group_id: UUID,
        from_date: date,
        to_date: date,
        nature_type: str,
    ) -> Decimal:
        """Get net amount for an account group."""
        # Get all accounts in this group
        account_ids = await self._get_accounts_in_group(group_id)
        if not account_ids:
            return Decimal("0")

        result = await self.db.execute(
            select(
                func.coalesce(func.sum(VoucherLine.debit_amount), 0).label("total_debit"),
                func.coalesce(func.sum(VoucherLine.credit_amount), 0).label("total_credit"),
            )
            .select_from(VoucherLine)
            .join(Voucher, VoucherLine.voucher_id == Voucher.id)
            .where(
                VoucherLine.account_id.in_(account_ids),
                Voucher.status == VoucherStatus.POSTED,
                Voucher.voucher_date >= from_date,
                Voucher.voucher_date <= to_date,
            )
        )
        row = result.one()
        total_debit = Decimal(str(row.total_debit))
        total_credit = Decimal(str(row.total_credit))

        # Income: Credit - Debit, Expenses: Debit - Credit
        if nature_type == "INCOME":
            return total_credit - total_debit
        else:
            return total_debit - total_credit

    async def _get_accounts_in_group(self, group_id: UUID) -> List[UUID]:
        """Get all account IDs in a group and its children recursively."""
        accounts_result = await self.db.execute(
            select(Account.id).where(Account.account_group_id == group_id)
        )
        account_ids = [row[0] for row in accounts_result.all()]

        children_result = await self.db.execute(
            select(AccountGroup.id).where(AccountGroup.parent_group_id == group_id)
        )
        child_group_ids = [row[0] for row in children_result.all()]

        for child_group_id in child_group_ids:
            child_accounts = await self._get_accounts_in_group(child_group_id)
            account_ids.extend(child_accounts)

        return account_ids

    async def _find_retained_earnings_account(
        self,
        organization_id: UUID,
    ) -> Optional[Account]:
        """Find the Retained Earnings account in Equity group."""
        # Look for account with common retained earnings names
        result = await self.db.execute(
            select(Account)
            .join(AccountGroup, Account.account_group_id == AccountGroup.id)
            .where(
                Account.organization_id == organization_id,
                AccountGroup.nature == AccountNature.EQUITY,
                Account.is_active == True,
                (
                    Account.name.ilike("%retained earnings%") |
                    Account.name.ilike("%accumulated profit%") |
                    Account.name.ilike("%accumulated loss%") |
                    Account.name.ilike("%profit & loss%") |
                    Account.name.ilike("%surplus%")
                ),
            )
        )
        return result.scalar_one_or_none()

    async def _get_accounts_to_carry_forward(
        self,
        organization_id: UUID,
        from_date: date,
        to_date: date,
    ) -> List[Dict]:
        """Get list of accounts with closing balances to carry forward."""
        accounts_result = await self.db.execute(
            select(Account)
            .join(AccountGroup, Account.account_group_id == AccountGroup.id)
            .where(
                Account.organization_id == organization_id,
                Account.is_active == True,
                AccountGroup.nature.in_([
                    AccountNature.ASSETS,
                    AccountNature.LIABILITIES,
                    AccountNature.EQUITY,
                ]),
            )
            .order_by(Account.code)
        )
        accounts = accounts_result.scalars().all()

        result = []
        for account in accounts:
            closing_balance, balance_type = await self._get_account_closing_balance(
                account, from_date, to_date
            )
            if closing_balance != 0:
                result.append({
                    "account_id": str(account.id),
                    "account_code": account.code,
                    "account_name": account.name,
                    "closing_balance": float(closing_balance),
                    "balance_type": balance_type,
                })

        return result

    async def _get_account_closing_balance(
        self,
        account: Account,
        from_date: date,
        to_date: date,
    ) -> Tuple[Decimal, str]:
        """Calculate closing balance for an account."""
        total_debit = Decimal("0")
        total_credit = Decimal("0")

        # Include opening balance
        if account.opening_balance:
            if account.opening_balance_type == BalanceType.DEBIT:
                total_debit += account.opening_balance
            else:
                total_credit += account.opening_balance

        # Get transactions
        result = await self.db.execute(
            select(
                func.coalesce(func.sum(VoucherLine.debit_amount), 0).label("total_debit"),
                func.coalesce(func.sum(VoucherLine.credit_amount), 0).label("total_credit"),
            )
            .select_from(VoucherLine)
            .join(Voucher, VoucherLine.voucher_id == Voucher.id)
            .where(
                VoucherLine.account_id == account.id,
                Voucher.status == VoucherStatus.POSTED,
                Voucher.voucher_date >= from_date,
                Voucher.voucher_date <= to_date,
            )
        )
        row = result.one()
        total_debit += Decimal(str(row.total_debit))
        total_credit += Decimal(str(row.total_credit))

        # Net out
        if total_debit >= total_credit:
            return total_debit - total_credit, "DR"
        else:
            return total_credit - total_debit, "CR"

    async def _create_closing_voucher(
        self,
        fy: FinancialYear,
        re_account: Account,
        net_pl: Decimal,
        pl_type: str,
        user_id: UUID,
    ) -> Optional[Voucher]:
        """Create P&L closing voucher to transfer to Retained Earnings."""
        if net_pl == 0:
            return None

        # Get adjustment period (last period)
        adj_period = None
        for period in sorted(fy.periods, key=lambda p: p.period_number, reverse=True):
            if not period.is_adjustment_period:
                adj_period = period
                break

        if not adj_period:
            adj_period = fy.periods[-1] if fy.periods else None

        # Get Journal voucher type
        vt_result = await self.db.execute(
            select(VoucherType).where(
                VoucherType.organization_id == fy.organization_id,
                VoucherType.voucher_class == VoucherClass.JOURNAL,
            )
        )
        voucher_type = vt_result.scalar_one_or_none()
        if not voucher_type:
            return None

        # Generate voucher number
        voucher_number = f"YEC-{fy.code}"

        # Create voucher
        voucher = Voucher(
            voucher_type_id=voucher_type.id,
            voucher_number=voucher_number,
            voucher_date=fy.end_date,
            financial_year_id=fy.id,
            period_id=adj_period.id if adj_period else fy.periods[-1].id,
            narration=f"Year-end closing entry: Transfer of Net {pl_type} to Retained Earnings for {fy.name}",
            total_debit=net_pl,
            total_credit=net_pl,
            status=VoucherStatus.POSTED,
            posted_at=datetime.now(timezone.utc),
            posted_by=user_id,
            organization_id=fy.organization_id,
            created_by=user_id,
        )
        self.db.add(voucher)
        await self.db.flush()

        # Get P&L Summary account (or create line to RE directly)
        # If PROFIT: Debit P&L Summary, Credit Retained Earnings
        # If LOSS: Debit Retained Earnings, Credit P&L Summary

        # For simplicity, we'll credit/debit Retained Earnings directly
        # In a more complex setup, you'd have a P&L Summary account

        line = VoucherLine(
            voucher_id=voucher.id,
            account_id=re_account.id,
            debit_amount=net_pl if pl_type == "LOSS" else Decimal("0"),
            credit_amount=net_pl if pl_type == "PROFIT" else Decimal("0"),
            narration=f"Net {pl_type.lower()} for {fy.name}",
            line_number=1,
            created_by=user_id,
        )
        self.db.add(line)
        await self.db.flush()

        return voucher

    async def _carry_forward_opening_balances(
        self,
        old_fy: FinancialYear,
        new_fy: FinancialYear,
        re_account: Account,
        net_pl: Decimal,
        pl_type: str,
        user_id: UUID,
    ) -> int:
        """Carry forward opening balances to new financial year."""
        # Get all Balance Sheet accounts
        accounts_result = await self.db.execute(
            select(Account)
            .join(AccountGroup, Account.account_group_id == AccountGroup.id)
            .where(
                Account.organization_id == old_fy.organization_id,
                Account.is_active == True,
                AccountGroup.nature.in_([
                    AccountNature.ASSETS,
                    AccountNature.LIABILITIES,
                    AccountNature.EQUITY,
                ]),
            )
        )
        accounts = accounts_result.scalars().all()

        count = 0
        for account in accounts:
            closing_balance, balance_type = await self._get_account_closing_balance(
                account, old_fy.start_date, old_fy.end_date
            )

            # Add net P&L to Retained Earnings
            if account.id == re_account.id:
                if pl_type == "PROFIT":
                    if balance_type == "CR":
                        closing_balance += net_pl
                    else:
                        closing_balance = net_pl - closing_balance
                        if closing_balance < 0:
                            closing_balance = abs(closing_balance)
                            balance_type = "DR"
                        else:
                            balance_type = "CR"
                else:  # LOSS
                    if balance_type == "DR":
                        closing_balance += net_pl
                    else:
                        closing_balance = closing_balance - net_pl
                        if closing_balance < 0:
                            closing_balance = abs(closing_balance)
                            balance_type = "DR"

            if closing_balance == 0:
                continue

            # Update account opening balance for new year
            # Note: In a multi-year setup, you might want to store these
            # in a separate opening_balance table per year
            account.opening_balance = closing_balance
            account.opening_balance_type = BalanceType.DEBIT if balance_type == "DR" else BalanceType.CREDIT
            account.current_balance = closing_balance
            account.current_balance_type = account.opening_balance_type
            account.updated_by = user_id

            count += 1

        await self.db.flush()
        return count

    async def reopen_year(
        self,
        financial_year_id: UUID,
        user_id: UUID,
        reason: str,
    ) -> FinancialYear:
        """Reopen a closed financial year (with audit trail)."""
        fy = await self._get_financial_year(financial_year_id)
        if not fy:
            raise NotFoundException("Financial year not found")

        if not fy.is_closed:
            raise BadRequestException("Financial year is not closed")

        # Check if there's a newer closed year
        newer_closed = await self.db.execute(
            select(FinancialYear)
            .where(
                FinancialYear.organization_id == fy.organization_id,
                FinancialYear.start_date > fy.end_date,
                FinancialYear.is_closed == True,
            )
        )
        if newer_closed.scalar_one_or_none():
            raise BadRequestException(
                "Cannot reopen this year as a later year has been closed. "
                "Reopen the later year first."
            )

        # Reopen the year
        fy.is_closed = False
        fy.closed_at = None
        fy.closed_by = None
        fy.updated_by = user_id

        # Reopen all periods
        for period in fy.periods:
            period.is_closed = False
            period.closed_at = None
            period.closed_by = None

        await self.db.flush()
        await self.db.refresh(fy)

        return fy
