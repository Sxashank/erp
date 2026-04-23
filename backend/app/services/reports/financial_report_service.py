"""Financial Report Service - Trial Balance, P&L, Balance Sheet."""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional, Dict, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import AccountNature, VoucherStatus, BalanceType
from app.core.exceptions import NotFoundException, ValidationException
from app.models.finance.account import Account
from app.models.finance.account_group import AccountGroup
from app.models.finance.voucher import Voucher, VoucherLine
from app.models.finance.financial_year import FinancialYear, FinancialPeriod
from app.models.masters.organization import Organization
from app.schemas.reports.financial_reports import (
    TrialBalanceItem,
    TrialBalanceResponse,
    ProfitLossItem,
    ProfitLossResponse,
    BalanceSheetItem,
    BalanceSheetSection,
    BalanceSheetResponse,
    AccountLedgerEntry,
    AccountLedgerResponse,
    CashFlowItem,
    CashFlowSection,
    CashFlowStatementResponse,
    DayBookEntry,
    DayBookResponse,
)


class FinancialReportService:
    """Service for generating financial reports."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_trial_balance(
        self,
        organization_id: UUID,
        financial_year_id: UUID,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        include_zero_balance: bool = False,
    ) -> TrialBalanceResponse:
        """Generate Trial Balance report."""
        # Get organization
        org_result = await self.db.execute(
            select(Organization).where(Organization.id == organization_id)
        )
        org = org_result.scalar_one_or_none()
        if not org:
            raise NotFoundException("Organization not found")

        # Get financial year
        fy_result = await self.db.execute(
            select(FinancialYear).where(FinancialYear.id == financial_year_id)
        )
        fy = fy_result.scalar_one_or_none()
        if not fy:
            raise NotFoundException("Financial year not found")

        # Default dates to financial year range
        if not from_date:
            from_date = fy.start_date
        if not to_date:
            to_date = fy.end_date

        # Get all accounts with their groups
        accounts_result = await self.db.execute(
            select(Account)
            .options(selectinload(Account.account_group))
            .where(
                Account.organization_id == organization_id,
                Account.is_active == True,
            )
            .order_by(Account.code)
        )
        accounts = accounts_result.scalars().all()

        # Calculate balances for each account
        items: List[TrialBalanceItem] = []
        total_opening_debit = Decimal("0")
        total_opening_credit = Decimal("0")
        total_period_debit = Decimal("0")
        total_period_credit = Decimal("0")
        total_closing_debit = Decimal("0")
        total_closing_credit = Decimal("0")

        for account in accounts:
            # Get opening balance (transactions before from_date + account's opening balance)
            opening_debit, opening_credit = await self._get_account_balance(
                account.id, fy.start_date, from_date, include_opening=True, account=account
            )

            # Get period transactions
            period_debit, period_credit = await self._get_period_transactions(
                account.id, from_date, to_date
            )

            # Calculate closing balance
            closing_debit = opening_debit + period_debit
            closing_credit = opening_credit + period_credit

            # Net out the balances
            if closing_debit >= closing_credit:
                closing_debit = closing_debit - closing_credit
                closing_credit = Decimal("0")
            else:
                closing_credit = closing_credit - closing_debit
                closing_debit = Decimal("0")

            # Similar netting for opening
            if opening_debit >= opening_credit:
                opening_debit = opening_debit - opening_credit
                opening_credit = Decimal("0")
            else:
                opening_credit = opening_credit - opening_debit
                opening_debit = Decimal("0")

            # Skip zero balance accounts if not included
            if not include_zero_balance and closing_debit == 0 and closing_credit == 0:
                continue

            items.append(
                TrialBalanceItem(
                    account_id=account.id,
                    account_code=account.code,
                    account_name=account.name,
                    account_group_name=account.account_group.name if account.account_group else "",
                    account_nature=account.account_group.nature.value if account.account_group else "",
                    opening_debit=opening_debit,
                    opening_credit=opening_credit,
                    period_debit=period_debit,
                    period_credit=period_credit,
                    closing_debit=closing_debit,
                    closing_credit=closing_credit,
                )
            )

            total_opening_debit += opening_debit
            total_opening_credit += opening_credit
            total_period_debit += period_debit
            total_period_credit += period_credit
            total_closing_debit += closing_debit
            total_closing_credit += closing_credit

        return TrialBalanceResponse(
            organization_id=org.id,
            organization_name=org.name,
            financial_year_id=fy.id,
            financial_year_name=fy.name,
            from_date=from_date,
            to_date=to_date,
            as_on_date=to_date,
            items=items,
            total_opening_debit=total_opening_debit,
            total_opening_credit=total_opening_credit,
            total_period_debit=total_period_debit,
            total_period_credit=total_period_credit,
            total_closing_debit=total_closing_debit,
            total_closing_credit=total_closing_credit,
            generated_at=datetime.now(timezone.utc),
        )

    async def get_profit_loss(
        self,
        organization_id: UUID,
        financial_year_id: UUID,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> ProfitLossResponse:
        """Generate Profit & Loss statement."""
        # Get organization
        org_result = await self.db.execute(
            select(Organization).where(Organization.id == organization_id)
        )
        org = org_result.scalar_one_or_none()
        if not org:
            raise NotFoundException("Organization not found")

        # Get financial year
        fy_result = await self.db.execute(
            select(FinancialYear).where(FinancialYear.id == financial_year_id)
        )
        fy = fy_result.scalar_one_or_none()
        if not fy:
            raise NotFoundException("Financial year not found")

        # Default dates
        if not from_date:
            from_date = fy.start_date
        if not to_date:
            to_date = fy.end_date

        # Get income groups and amounts
        income_items = await self._get_pl_section(
            organization_id, AccountNature.INCOME, from_date, to_date
        )
        total_income = sum(item.amount for item in income_items)

        # Get expense groups and amounts
        expense_items = await self._get_pl_section(
            organization_id, AccountNature.EXPENSES, from_date, to_date
        )
        total_expenses = sum(item.amount for item in expense_items)

        # Calculate net profit/loss
        net_profit_loss = total_income - total_expenses
        profit_loss_type = "PROFIT" if net_profit_loss >= 0 else "LOSS"

        return ProfitLossResponse(
            organization_id=org.id,
            organization_name=org.name,
            financial_year_id=fy.id,
            financial_year_name=fy.name,
            from_date=from_date,
            to_date=to_date,
            income_items=income_items,
            expense_items=expense_items,
            total_income=total_income,
            total_expenses=total_expenses,
            net_profit_loss=abs(net_profit_loss),
            profit_loss_type=profit_loss_type,
            generated_at=datetime.now(timezone.utc),
        )

    async def get_balance_sheet(
        self,
        organization_id: UUID,
        financial_year_id: UUID,
        as_on_date: Optional[date] = None,
    ) -> BalanceSheetResponse:
        """Generate Balance Sheet."""
        # Get organization
        org_result = await self.db.execute(
            select(Organization).where(Organization.id == organization_id)
        )
        org = org_result.scalar_one_or_none()
        if not org:
            raise NotFoundException("Organization not found")

        # Get financial year
        fy_result = await self.db.execute(
            select(FinancialYear).where(FinancialYear.id == financial_year_id)
        )
        fy = fy_result.scalar_one_or_none()
        if not fy:
            raise NotFoundException("Financial year not found")

        # Default date
        if not as_on_date:
            as_on_date = fy.end_date

        # Get assets
        asset_items = await self._get_bs_section(
            organization_id, AccountNature.ASSETS, fy.start_date, as_on_date
        )
        total_assets = sum(item.amount for item in asset_items)

        # Get liabilities
        liability_items = await self._get_bs_section(
            organization_id, AccountNature.LIABILITIES, fy.start_date, as_on_date
        )
        total_liabilities = sum(item.amount for item in liability_items)

        # Get equity
        equity_items = await self._get_bs_section(
            organization_id, AccountNature.EQUITY, fy.start_date, as_on_date
        )
        total_equity = sum(item.amount for item in equity_items)

        # Calculate net profit/loss for the period
        net_profit_loss = await self._calculate_net_profit_loss(
            organization_id, fy.start_date, as_on_date
        )

        # Total liabilities + equity + net profit
        total_liabilities_equity = total_liabilities + total_equity + net_profit_loss

        assets_section = BalanceSheetSection(
            section_name="Assets",
            items=asset_items,
            total=total_assets,
        )

        liabilities_section = BalanceSheetSection(
            section_name="Liabilities",
            items=liability_items,
            total=total_liabilities,
        )

        equity_section = BalanceSheetSection(
            section_name="Equity",
            items=equity_items,
            total=total_equity,
        )

        return BalanceSheetResponse(
            organization_id=org.id,
            organization_name=org.name,
            financial_year_id=fy.id,
            financial_year_name=fy.name,
            as_on_date=as_on_date,
            assets=assets_section,
            liabilities=liabilities_section,
            equity=equity_section,
            net_profit_loss=net_profit_loss,
            total_liabilities_equity=total_liabilities_equity,
            is_balanced=abs(total_assets - total_liabilities_equity) < Decimal("0.01"),
            generated_at=datetime.now(timezone.utc),
        )

    async def get_account_ledger(
        self,
        account_id: UUID,
        from_date: date,
        to_date: date,
    ) -> AccountLedgerResponse:
        """Generate account ledger (detailed transactions)."""
        # Get account with organization
        account_result = await self.db.execute(
            select(Account)
            .options(selectinload(Account.account_group))
            .where(Account.id == account_id)
        )
        account = account_result.scalar_one_or_none()
        if not account:
            raise NotFoundException("Account not found")

        # Get organization
        org_result = await self.db.execute(
            select(Organization).where(Organization.id == account.organization_id)
        )
        org = org_result.scalar_one_or_none()

        # Get opening balance
        opening_debit, opening_credit = await self._get_account_balance(
            account_id, None, from_date, include_opening=True, account=account
        )
        if opening_debit >= opening_credit:
            opening_balance = opening_debit - opening_credit
            opening_balance_type = "DR"
        else:
            opening_balance = opening_credit - opening_debit
            opening_balance_type = "CR"

        # Get transactions in the period
        entries_result = await self.db.execute(
            select(VoucherLine, Voucher)
            .join(Voucher, VoucherLine.voucher_id == Voucher.id)
            .where(
                VoucherLine.account_id == account_id,
                Voucher.status == VoucherStatus.POSTED,
                Voucher.voucher_date >= from_date,
                Voucher.voucher_date <= to_date,
            )
            .order_by(Voucher.voucher_date, Voucher.voucher_number)
        )
        rows = entries_result.all()

        # Build entries with running balance
        entries: List[AccountLedgerEntry] = []
        running_balance = opening_balance
        running_type = opening_balance_type
        total_debit = Decimal("0")
        total_credit = Decimal("0")

        for line, voucher in rows:
            total_debit += line.debit_amount or Decimal("0")
            total_credit += line.credit_amount or Decimal("0")

            # Update running balance
            if running_type == "DR":
                running_balance = running_balance + (line.debit_amount or Decimal("0")) - (line.credit_amount or Decimal("0"))
            else:
                running_balance = running_balance - (line.debit_amount or Decimal("0")) + (line.credit_amount or Decimal("0"))

            if running_balance < 0:
                running_balance = abs(running_balance)
                running_type = "CR" if running_type == "DR" else "DR"

            entries.append(
                AccountLedgerEntry(
                    voucher_id=voucher.id,
                    voucher_number=voucher.voucher_number,
                    voucher_date=voucher.voucher_date,
                    voucher_type=voucher.voucher_type.code if voucher.voucher_type else "",
                    narration=line.narration or voucher.narration,
                    debit_amount=line.debit_amount or Decimal("0"),
                    credit_amount=line.credit_amount or Decimal("0"),
                    running_balance=running_balance,
                    balance_type=running_type,
                )
            )

        # Closing balance
        closing_balance = running_balance
        closing_balance_type = running_type

        return AccountLedgerResponse(
            account_id=account.id,
            account_code=account.code,
            account_name=account.name,
            account_group_name=account.account_group.name if account.account_group else "",
            organization_id=org.id if org else account.organization_id,
            organization_name=org.name if org else "",
            from_date=from_date,
            to_date=to_date,
            opening_balance=opening_balance,
            opening_balance_type=opening_balance_type,
            entries=entries,
            total_debit=total_debit,
            total_credit=total_credit,
            closing_balance=closing_balance,
            closing_balance_type=closing_balance_type,
            generated_at=datetime.now(timezone.utc),
        )

    async def _get_account_balance(
        self,
        account_id: UUID,
        fy_start_date: Optional[date],
        as_of_date: date,
        include_opening: bool = False,
        account: Optional[Account] = None,
    ) -> Tuple[Decimal, Decimal]:
        """Get account balance as of a date."""
        total_debit = Decimal("0")
        total_credit = Decimal("0")

        # Include opening balance from account master
        if include_opening and account:
            if account.opening_balance:
                if account.opening_balance_type == BalanceType.DEBIT:
                    total_debit += account.opening_balance
                else:
                    total_credit += account.opening_balance

        # Get transactions up to (but not including) as_of_date
        query = (
            select(
                func.coalesce(func.sum(VoucherLine.debit_amount), 0).label("total_debit"),
                func.coalesce(func.sum(VoucherLine.credit_amount), 0).label("total_credit"),
            )
            .select_from(VoucherLine)
            .join(Voucher, VoucherLine.voucher_id == Voucher.id)
            .where(
                VoucherLine.account_id == account_id,
                Voucher.status == VoucherStatus.POSTED,
                Voucher.voucher_date < as_of_date,
            )
        )

        if fy_start_date:
            query = query.where(Voucher.voucher_date >= fy_start_date)

        result = await self.db.execute(query)
        row = result.one()

        total_debit += Decimal(str(row.total_debit))
        total_credit += Decimal(str(row.total_credit))

        return total_debit, total_credit

    async def _get_period_transactions(
        self,
        account_id: UUID,
        from_date: date,
        to_date: date,
    ) -> Tuple[Decimal, Decimal]:
        """Get total debits and credits for an account in a period."""
        result = await self.db.execute(
            select(
                func.coalesce(func.sum(VoucherLine.debit_amount), 0).label("total_debit"),
                func.coalesce(func.sum(VoucherLine.credit_amount), 0).label("total_credit"),
            )
            .select_from(VoucherLine)
            .join(Voucher, VoucherLine.voucher_id == Voucher.id)
            .where(
                VoucherLine.account_id == account_id,
                Voucher.status == VoucherStatus.POSTED,
                Voucher.voucher_date >= from_date,
                Voucher.voucher_date <= to_date,
            )
        )
        row = result.one()
        return Decimal(str(row.total_debit)), Decimal(str(row.total_credit))

    async def _get_pl_section(
        self,
        organization_id: UUID,
        nature: AccountNature,
        from_date: date,
        to_date: date,
    ) -> List[ProfitLossItem]:
        """Get P&L section items (income or expenses)."""
        # Get account groups with this nature
        groups_result = await self.db.execute(
            select(AccountGroup)
            .where(
                AccountGroup.organization_id == organization_id,
                AccountGroup.nature == nature,
                AccountGroup.level == 1,  # Top level under nature
                AccountGroup.is_active == True,
            )
            .order_by(AccountGroup.sequence)
        )
        groups = groups_result.scalars().all()

        items: List[ProfitLossItem] = []
        for group in groups:
            amount = await self._get_group_amount(group.id, from_date, to_date, nature)
            if amount != 0:
                items.append(
                    ProfitLossItem(
                        account_group_code=group.code,
                        account_group_name=group.name,
                        level=group.level,
                        amount=abs(amount),
                    )
                )

        return items

    async def _get_bs_section(
        self,
        organization_id: UUID,
        nature: AccountNature,
        from_date: date,
        to_date: date,
    ) -> List[BalanceSheetItem]:
        """Get Balance Sheet section items."""
        # Get account groups with this nature
        groups_result = await self.db.execute(
            select(AccountGroup)
            .where(
                AccountGroup.organization_id == organization_id,
                AccountGroup.nature == nature,
                AccountGroup.level == 1,  # Top level under nature
                AccountGroup.is_active == True,
            )
            .order_by(AccountGroup.sequence)
        )
        groups = groups_result.scalars().all()

        items: List[BalanceSheetItem] = []
        for group in groups:
            amount = await self._get_group_balance(group.id, from_date, to_date, nature)
            if amount != 0:
                items.append(
                    BalanceSheetItem(
                        account_group_code=group.code,
                        account_group_name=group.name,
                        level=group.level,
                        amount=abs(amount),
                    )
                )

        return items

    async def _get_group_amount(
        self,
        group_id: UUID,
        from_date: date,
        to_date: date,
        nature: AccountNature,
    ) -> Decimal:
        """Get net amount for an account group (for P&L)."""
        # Get all accounts in this group and its children
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

        # For Income: Credit - Debit
        # For Expenses: Debit - Credit
        if nature == AccountNature.INCOME:
            return total_credit - total_debit
        else:
            return total_debit - total_credit

    async def _get_group_balance(
        self,
        group_id: UUID,
        from_date: date,
        to_date: date,
        nature: AccountNature,
    ) -> Decimal:
        """Get closing balance for an account group (for Balance Sheet)."""
        # Get all accounts in this group and its children
        account_ids = await self._get_accounts_in_group(group_id)

        if not account_ids:
            return Decimal("0")

        # Get opening balances
        accounts_result = await self.db.execute(
            select(Account).where(Account.id.in_(account_ids))
        )
        accounts = accounts_result.scalars().all()

        total_opening = Decimal("0")
        for acc in accounts:
            if acc.opening_balance:
                if acc.opening_balance_type == BalanceType.DEBIT:
                    if nature == AccountNature.ASSETS:
                        total_opening += acc.opening_balance
                    else:
                        total_opening -= acc.opening_balance
                else:
                    if nature == AccountNature.ASSETS:
                        total_opening -= acc.opening_balance
                    else:
                        total_opening += acc.opening_balance

        # Get transactions
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

        # For Assets: Opening + Debit - Credit
        # For Liabilities/Equity: Opening + Credit - Debit
        if nature == AccountNature.ASSETS:
            return total_opening + total_debit - total_credit
        else:
            return total_opening + total_credit - total_debit

    async def _get_accounts_in_group(self, group_id: UUID) -> List[UUID]:
        """Get all account IDs in a group and its children recursively."""
        # Get direct accounts
        accounts_result = await self.db.execute(
            select(Account.id).where(Account.account_group_id == group_id)
        )
        account_ids = [row[0] for row in accounts_result.all()]

        # Get child groups
        children_result = await self.db.execute(
            select(AccountGroup.id).where(AccountGroup.parent_group_id == group_id)
        )
        child_group_ids = [row[0] for row in children_result.all()]

        # Recursively get accounts from child groups
        for child_group_id in child_group_ids:
            child_accounts = await self._get_accounts_in_group(child_group_id)
            account_ids.extend(child_accounts)

        return account_ids

    async def _calculate_net_profit_loss(
        self,
        organization_id: UUID,
        from_date: date,
        to_date: date,
    ) -> Decimal:
        """Calculate net profit/loss for the period."""
        # Get all income accounts
        income_groups_result = await self.db.execute(
            select(AccountGroup.id).where(
                AccountGroup.organization_id == organization_id,
                AccountGroup.nature == AccountNature.INCOME,
            )
        )
        income_group_ids = [row[0] for row in income_groups_result.all()]

        total_income = Decimal("0")
        for group_id in income_group_ids:
            total_income += await self._get_group_amount(
                group_id, from_date, to_date, AccountNature.INCOME
            )

        # Get all expense accounts
        expense_groups_result = await self.db.execute(
            select(AccountGroup.id).where(
                AccountGroup.organization_id == organization_id,
                AccountGroup.nature == AccountNature.EXPENSES,
            )
        )
        expense_group_ids = [row[0] for row in expense_groups_result.all()]

        total_expenses = Decimal("0")
        for group_id in expense_group_ids:
            total_expenses += await self._get_group_amount(
                group_id, from_date, to_date, AccountNature.EXPENSES
            )

        return total_income - total_expenses

    async def get_cash_flow_statement(
        self,
        organization_id: UUID,
        financial_year_id: UUID,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> CashFlowStatementResponse:
        """
        Generate Cash Flow Statement using Indirect Method.

        Structure:
        - Operating Activities: Net Profit + Non-cash adjustments + Working capital changes
        - Investing Activities: Changes in fixed assets, investments
        - Financing Activities: Changes in loans, capital, dividends
        """
        # Get organization
        org_result = await self.db.execute(
            select(Organization).where(Organization.id == organization_id)
        )
        org = org_result.scalar_one_or_none()
        if not org:
            raise NotFoundException("Organization not found")

        # Get financial year
        fy_result = await self.db.execute(
            select(FinancialYear).where(FinancialYear.id == financial_year_id)
        )
        fy = fy_result.scalar_one_or_none()
        if not fy:
            raise NotFoundException("Financial year not found")

        # Default dates
        if not from_date:
            from_date = fy.start_date
        if not to_date:
            to_date = fy.end_date

        # Get Net Profit/Loss
        net_profit_loss = await self._calculate_net_profit_loss(
            organization_id, from_date, to_date
        )
        profit_loss_type = "PROFIT" if net_profit_loss >= 0 else "LOSS"

        # === OPERATING ACTIVITIES (Indirect Method) ===
        operating_items: List[CashFlowItem] = []

        # 1. Start with Net Profit/Loss
        operating_items.append(CashFlowItem(
            label="Net Profit/(Loss) for the period",
            amount=net_profit_loss,
            is_subtotal=False,
        ))

        # 2. Adjustments for non-cash items
        # Get Depreciation (typically under Expenses with names containing "depreciation")
        depreciation = await self._get_depreciation_amount(organization_id, from_date, to_date)
        if depreciation != 0:
            operating_items.append(CashFlowItem(
                label="Add: Depreciation and Amortization",
                amount=depreciation,
                is_subtotal=False,
            ))

        # Operating profit before working capital changes
        operating_profit = net_profit_loss + depreciation
        operating_items.append(CashFlowItem(
            label="Operating Profit before Working Capital Changes",
            amount=operating_profit,
            is_subtotal=True,
        ))

        # 3. Working Capital Changes
        working_capital_changes = await self._get_working_capital_changes(
            organization_id, from_date, to_date
        )

        for wc_item in working_capital_changes:
            operating_items.append(wc_item)

        total_working_capital = sum(item.amount for item in working_capital_changes)

        # Cash generated from operations
        cash_from_operations = operating_profit + total_working_capital
        operating_items.append(CashFlowItem(
            label="Cash Generated from Operations",
            amount=cash_from_operations,
            is_subtotal=True,
        ))

        operating_section = CashFlowSection(
            section_name="Cash Flow from Operating Activities",
            items=operating_items,
            net_cash_flow=cash_from_operations,
        )

        # === INVESTING ACTIVITIES ===
        investing_items, investing_total = await self._get_investing_activities(
            organization_id, from_date, to_date
        )
        investing_section = CashFlowSection(
            section_name="Cash Flow from Investing Activities",
            items=investing_items,
            net_cash_flow=investing_total,
        )

        # === FINANCING ACTIVITIES ===
        financing_items, financing_total = await self._get_financing_activities(
            organization_id, from_date, to_date
        )
        financing_section = CashFlowSection(
            section_name="Cash Flow from Financing Activities",
            items=financing_items,
            net_cash_flow=financing_total,
        )

        # === SUMMARY ===
        net_increase_in_cash = cash_from_operations + investing_total + financing_total

        # Get opening and closing cash balances
        opening_cash = await self._get_cash_balance(organization_id, from_date, is_opening=True)
        closing_cash = opening_cash + net_increase_in_cash

        return CashFlowStatementResponse(
            organization_id=org.id,
            organization_name=org.name,
            financial_year_id=fy.id,
            financial_year_name=fy.name,
            from_date=from_date,
            to_date=to_date,
            net_profit_loss=abs(net_profit_loss),
            profit_loss_type=profit_loss_type,
            operating_activities=operating_section,
            investing_activities=investing_section,
            financing_activities=financing_section,
            net_increase_in_cash=net_increase_in_cash,
            opening_cash_balance=opening_cash,
            closing_cash_balance=closing_cash,
            generated_at=datetime.now(timezone.utc),
        )

    async def _get_depreciation_amount(
        self,
        organization_id: UUID,
        from_date: date,
        to_date: date,
    ) -> Decimal:
        """Get total depreciation expense for the period."""
        # Find accounts with "depreciation" or "amortization" in name
        accounts_result = await self.db.execute(
            select(Account.id)
            .join(AccountGroup, Account.account_group_id == AccountGroup.id)
            .where(
                Account.organization_id == organization_id,
                AccountGroup.nature == AccountNature.EXPENSES,
                Account.name.ilike("%depreciation%") | Account.name.ilike("%amortization%"),
            )
        )
        depreciation_account_ids = [row[0] for row in accounts_result.all()]

        if not depreciation_account_ids:
            return Decimal("0")

        result = await self.db.execute(
            select(
                func.coalesce(func.sum(VoucherLine.debit_amount), 0).label("total"),
            )
            .select_from(VoucherLine)
            .join(Voucher, VoucherLine.voucher_id == Voucher.id)
            .where(
                VoucherLine.account_id.in_(depreciation_account_ids),
                Voucher.status == VoucherStatus.POSTED,
                Voucher.voucher_date >= from_date,
                Voucher.voucher_date <= to_date,
            )
        )
        row = result.one()
        return Decimal(str(row.total))

    async def _get_working_capital_changes(
        self,
        organization_id: UUID,
        from_date: date,
        to_date: date,
    ) -> List[CashFlowItem]:
        """Calculate working capital changes for Cash Flow Statement."""
        items: List[CashFlowItem] = []

        # Current Assets (excluding Cash and Bank)
        # Increase in current assets = Cash outflow (negative)
        current_asset_groups = await self.db.execute(
            select(AccountGroup)
            .where(
                AccountGroup.organization_id == organization_id,
                AccountGroup.nature == AccountNature.ASSETS,
                AccountGroup.code.ilike("%CURRENT%") | AccountGroup.name.ilike("%Current Asset%"),
            )
        )
        ca_groups = current_asset_groups.scalars().all()

        for group in ca_groups:
            # Get accounts excluding cash and bank
            accounts_result = await self.db.execute(
                select(Account)
                .where(
                    Account.account_group_id == group.id,
                    Account.is_bank_account == False,
                    Account.is_cash_account == False,
                )
            )
            accounts = accounts_result.scalars().all()

            for account in accounts:
                change = await self._get_account_period_change(account, from_date, to_date)
                if change != 0:
                    # Positive change in asset = negative cash flow
                    label = f"(Increase)/Decrease in {account.name}"
                    items.append(CashFlowItem(
                        label=label,
                        amount=-change,  # Negate: asset increase = cash decrease
                        is_subtotal=False,
                    ))

        # Current Liabilities
        # Increase in current liabilities = Cash inflow (positive)
        current_liability_groups = await self.db.execute(
            select(AccountGroup)
            .where(
                AccountGroup.organization_id == organization_id,
                AccountGroup.nature == AccountNature.LIABILITIES,
                AccountGroup.code.ilike("%CURRENT%") | AccountGroup.name.ilike("%Current Liabilit%"),
            )
        )
        cl_groups = current_liability_groups.scalars().all()

        for group in cl_groups:
            accounts_result = await self.db.execute(
                select(Account).where(Account.account_group_id == group.id)
            )
            accounts = accounts_result.scalars().all()

            for account in accounts:
                change = await self._get_account_period_change(account, from_date, to_date)
                if change != 0:
                    label = f"Increase/(Decrease) in {account.name}"
                    items.append(CashFlowItem(
                        label=label,
                        amount=change,  # Liability increase = cash increase
                        is_subtotal=False,
                    ))

        return items

    async def _get_account_period_change(
        self,
        account: Account,
        from_date: date,
        to_date: date,
    ) -> Decimal:
        """Get the net change in an account balance during a period."""
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
        total_debit = Decimal(str(row.total_debit))
        total_credit = Decimal(str(row.total_credit))

        # For Assets: Debit increases, Credit decreases (return net debit)
        # For Liabilities: Credit increases, Debit decreases (return net credit)
        group_result = await self.db.execute(
            select(AccountGroup.nature).where(AccountGroup.id == account.account_group_id)
        )
        nature = group_result.scalar_one_or_none()

        if nature == AccountNature.ASSETS:
            return total_debit - total_credit
        else:
            return total_credit - total_debit

    async def _get_investing_activities(
        self,
        organization_id: UUID,
        from_date: date,
        to_date: date,
    ) -> Tuple[List[CashFlowItem], Decimal]:
        """Get investing activities for Cash Flow Statement."""
        items: List[CashFlowItem] = []
        total = Decimal("0")

        # Fixed Assets / Non-Current Assets
        # Purchase of asset = Cash outflow (negative)
        # Sale of asset = Cash inflow (positive)
        fixed_asset_groups = await self.db.execute(
            select(AccountGroup)
            .where(
                AccountGroup.organization_id == organization_id,
                AccountGroup.nature == AccountNature.ASSETS,
                (AccountGroup.code.ilike("%FIXED%") |
                 AccountGroup.name.ilike("%Fixed Asset%") |
                 AccountGroup.name.ilike("%Property%") |
                 AccountGroup.name.ilike("%Plant%") |
                 AccountGroup.name.ilike("%Equipment%") |
                 AccountGroup.name.ilike("%Investment%")),
            )
        )
        fa_groups = fixed_asset_groups.scalars().all()

        for group in fa_groups:
            account_ids = await self._get_accounts_in_group(group.id)
            if not account_ids:
                continue

            result = await self.db.execute(
                select(
                    func.coalesce(func.sum(VoucherLine.debit_amount), 0).label("purchases"),
                    func.coalesce(func.sum(VoucherLine.credit_amount), 0).label("sales"),
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
            purchases = Decimal(str(row.purchases))
            sales = Decimal(str(row.sales))

            if purchases > 0:
                items.append(CashFlowItem(
                    label=f"Purchase of {group.name}",
                    amount=-purchases,  # Outflow is negative
                    is_subtotal=False,
                ))
                total -= purchases

            if sales > 0:
                items.append(CashFlowItem(
                    label=f"Sale of {group.name}",
                    amount=sales,  # Inflow is positive
                    is_subtotal=False,
                ))
                total += sales

        if not items:
            items.append(CashFlowItem(
                label="No investing activities",
                amount=Decimal("0"),
                is_subtotal=False,
            ))

        return items, total

    async def _get_financing_activities(
        self,
        organization_id: UUID,
        from_date: date,
        to_date: date,
    ) -> Tuple[List[CashFlowItem], Decimal]:
        """Get financing activities for Cash Flow Statement."""
        items: List[CashFlowItem] = []
        total = Decimal("0")

        # Loans / Borrowings (Liabilities)
        # Loan received = Cash inflow (positive)
        # Loan repaid = Cash outflow (negative)
        loan_groups = await self.db.execute(
            select(AccountGroup)
            .where(
                AccountGroup.organization_id == organization_id,
                AccountGroup.nature == AccountNature.LIABILITIES,
                (AccountGroup.code.ilike("%LOAN%") |
                 AccountGroup.name.ilike("%Loan%") |
                 AccountGroup.name.ilike("%Borrowing%") |
                 AccountGroup.name.ilike("%Secured%") |
                 AccountGroup.name.ilike("%Unsecured%")),
            )
        )
        loan_groups_list = loan_groups.scalars().all()

        for group in loan_groups_list:
            account_ids = await self._get_accounts_in_group(group.id)
            if not account_ids:
                continue

            result = await self.db.execute(
                select(
                    func.coalesce(func.sum(VoucherLine.credit_amount), 0).label("received"),
                    func.coalesce(func.sum(VoucherLine.debit_amount), 0).label("repaid"),
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
            received = Decimal(str(row.received))
            repaid = Decimal(str(row.repaid))

            net_loan = received - repaid
            if net_loan != 0:
                label = f"Proceeds/(Repayment) of {group.name}"
                items.append(CashFlowItem(
                    label=label,
                    amount=net_loan,
                    is_subtotal=False,
                ))
                total += net_loan

        # Capital / Equity
        equity_groups = await self.db.execute(
            select(AccountGroup)
            .where(
                AccountGroup.organization_id == organization_id,
                AccountGroup.nature == AccountNature.EQUITY,
            )
        )
        equity_groups_list = equity_groups.scalars().all()

        for group in equity_groups_list:
            account_ids = await self._get_accounts_in_group(group.id)
            if not account_ids:
                continue

            result = await self.db.execute(
                select(
                    func.coalesce(func.sum(VoucherLine.credit_amount), 0).label("infusion"),
                    func.coalesce(func.sum(VoucherLine.debit_amount), 0).label("withdrawal"),
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
            infusion = Decimal(str(row.infusion))
            withdrawal = Decimal(str(row.withdrawal))

            net_equity = infusion - withdrawal
            if net_equity != 0:
                label = f"Capital Introduced/(Withdrawn) - {group.name}"
                items.append(CashFlowItem(
                    label=label,
                    amount=net_equity,
                    is_subtotal=False,
                ))
                total += net_equity

        if not items:
            items.append(CashFlowItem(
                label="No financing activities",
                amount=Decimal("0"),
                is_subtotal=False,
            ))

        return items, total

    async def _get_cash_balance(
        self,
        organization_id: UUID,
        as_of_date: date,
        is_opening: bool = True,
    ) -> Decimal:
        """Get cash and bank balance as of a date."""
        # Get all cash and bank accounts
        accounts_result = await self.db.execute(
            select(Account)
            .where(
                Account.organization_id == organization_id,
                (Account.is_cash_account == True) | (Account.is_bank_account == True),
            )
        )
        accounts = accounts_result.scalars().all()

        total_balance = Decimal("0")
        for account in accounts:
            # Opening balance from account master
            if account.opening_balance:
                if account.opening_balance_type == BalanceType.DEBIT:
                    total_balance += account.opening_balance
                else:
                    total_balance -= account.opening_balance

            # Transactions up to (but not including) as_of_date for opening
            # Or up to and including as_of_date for closing
            if is_opening:
                date_condition = Voucher.voucher_date < as_of_date
            else:
                date_condition = Voucher.voucher_date <= as_of_date

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
                    date_condition,
                )
            )
            row = result.one()
            total_balance += Decimal(str(row.total_debit)) - Decimal(str(row.total_credit))

        return total_balance

    async def get_day_book(
        self,
        organization_id: UUID,
        from_date: date,
        to_date: date,
        voucher_type_id: Optional[UUID] = None,
    ) -> DayBookResponse:
        """
        Generate Day Book / Journal Register.

        Shows all vouchers for a date range with summary.
        """
        # Get organization
        org_result = await self.db.execute(
            select(Organization).where(Organization.id == organization_id)
        )
        org = org_result.scalar_one_or_none()
        if not org:
            raise NotFoundException("Organization not found")

        # Build query
        query = (
            select(Voucher)
            .options(selectinload(Voucher.voucher_type))
            .where(
                Voucher.organization_id == organization_id,
                Voucher.voucher_date >= from_date,
                Voucher.voucher_date <= to_date,
                Voucher.status == VoucherStatus.POSTED,
            )
            .order_by(Voucher.voucher_date, Voucher.voucher_number)
        )

        if voucher_type_id:
            query = query.where(Voucher.voucher_type_id == voucher_type_id)

        vouchers_result = await self.db.execute(query)
        vouchers = vouchers_result.scalars().all()

        entries: List[DayBookEntry] = []
        total_debit = Decimal("0")
        total_credit = Decimal("0")

        for voucher in vouchers:
            # Get voucher line totals
            line_result = await self.db.execute(
                select(
                    func.coalesce(func.sum(VoucherLine.debit_amount), 0).label("debit"),
                    func.coalesce(func.sum(VoucherLine.credit_amount), 0).label("credit"),
                    func.count(VoucherLine.id).label("line_count"),
                )
                .where(VoucherLine.voucher_id == voucher.id)
            )
            line_row = line_result.one()

            voucher_debit = Decimal(str(line_row.debit))
            voucher_credit = Decimal(str(line_row.credit))

            entries.append(DayBookEntry(
                voucher_id=voucher.id,
                voucher_number=voucher.voucher_number,
                voucher_date=voucher.voucher_date,
                voucher_type=voucher.voucher_type.code if voucher.voucher_type else "",
                voucher_type_name=voucher.voucher_type.name if voucher.voucher_type else "",
                narration=voucher.narration,
                total_debit=voucher_debit,
                total_credit=voucher_credit,
                line_count=int(line_row.line_count),
                status=voucher.status.value,
            ))

            total_debit += voucher_debit
            total_credit += voucher_credit

        return DayBookResponse(
            organization_id=org.id,
            organization_name=org.name,
            from_date=from_date,
            to_date=to_date,
            entries=entries,
            total_vouchers=len(entries),
            total_debit=total_debit,
            total_credit=total_credit,
            generated_at=datetime.now(timezone.utc),
        )
