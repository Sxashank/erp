"""Service for managing recurring vouchers."""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID
import calendar
from dateutil.relativedelta import relativedelta

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.finance.recurring_voucher import RecurringVoucher, RecurringVoucherLog
from app.models.finance.voucher import Voucher, VoucherLine
from app.models.finance.voucher_type import VoucherType
from app.models.finance.financial_year import FinancialYear, FinancialPeriod
from app.models.finance.account import Account
from app.core.constants import (
    RecurrenceFrequency,
    RecurringVoucherStatus,
    VoucherStatus,
)
from app.schemas.finance.recurring_voucher import (
    RecurringVoucherCreate,
    RecurringVoucherUpdate,
    RecurringVoucherResponse,
    RecurringVoucherListItem,
    RecurringVoucherListResponse,
    RecurringVoucherLineResponse,
    RecurringVoucherLogResponse,
    RecurringVoucherLogListResponse,
    GenerateVoucherResponse,
    UpcomingRecurringVoucher,
    RecurringVoucherStats,
)


class RecurringVoucherService:
    """Service for managing recurring voucher templates."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _calculate_next_run_date(
        self,
        frequency: RecurrenceFrequency,
        from_date: date,
        day_of_month: Optional[int] = None,
        day_of_week: Optional[int] = None,
    ) -> date:
        """Calculate the next run date based on frequency."""
        if frequency == RecurrenceFrequency.DAILY:
            return from_date + timedelta(days=1)

        elif frequency == RecurrenceFrequency.WEEKLY:
            # If day_of_week specified, find next occurrence
            if day_of_week is not None:
                days_ahead = day_of_week - from_date.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                return from_date + timedelta(days=days_ahead)
            return from_date + timedelta(weeks=1)

        elif frequency == RecurrenceFrequency.MONTHLY:
            next_month = from_date + relativedelta(months=1)
            if day_of_month:
                # Handle months with fewer days
                last_day = calendar.monthrange(next_month.year, next_month.month)[1]
                target_day = min(day_of_month, last_day)
                return next_month.replace(day=target_day)
            return next_month

        elif frequency == RecurrenceFrequency.QUARTERLY:
            next_quarter = from_date + relativedelta(months=3)
            if day_of_month:
                last_day = calendar.monthrange(next_quarter.year, next_quarter.month)[1]
                target_day = min(day_of_month, last_day)
                return next_quarter.replace(day=target_day)
            return next_quarter

        elif frequency == RecurrenceFrequency.HALF_YEARLY:
            next_half = from_date + relativedelta(months=6)
            if day_of_month:
                last_day = calendar.monthrange(next_half.year, next_half.month)[1]
                target_day = min(day_of_month, last_day)
                return next_half.replace(day=target_day)
            return next_half

        elif frequency == RecurrenceFrequency.YEARLY:
            next_year = from_date + relativedelta(years=1)
            if day_of_month:
                last_day = calendar.monthrange(next_year.year, next_year.month)[1]
                target_day = min(day_of_month, last_day)
                return next_year.replace(day=target_day)
            return next_year

        return from_date + timedelta(days=1)

    def _calculate_initial_next_run_date(
        self,
        frequency: RecurrenceFrequency,
        start_date: date,
        day_of_month: Optional[int] = None,
        day_of_week: Optional[int] = None,
    ) -> date:
        """Calculate the initial next run date based on start date."""
        today = date.today()

        if start_date > today:
            # Start date is in the future
            if frequency == RecurrenceFrequency.MONTHLY and day_of_month:
                last_day = calendar.monthrange(start_date.year, start_date.month)[1]
                target_day = min(day_of_month, last_day)
                if target_day >= start_date.day:
                    return start_date.replace(day=target_day)
                else:
                    next_month = start_date + relativedelta(months=1)
                    last_day = calendar.monthrange(next_month.year, next_month.month)[1]
                    return next_month.replace(day=min(day_of_month, last_day))
            elif frequency == RecurrenceFrequency.WEEKLY and day_of_week is not None:
                days_ahead = day_of_week - start_date.weekday()
                if days_ahead < 0:
                    days_ahead += 7
                return start_date + timedelta(days=days_ahead)
            return start_date
        else:
            # Start date is today or in the past
            return self._calculate_next_run_date(
                frequency, today, day_of_month, day_of_week
            )

    async def create(
        self,
        data: RecurringVoucherCreate,
        user_id: UUID,
    ) -> RecurringVoucher:
        """Create a new recurring voucher template."""
        # Calculate total amount
        total_amount = sum(line.debit_amount for line in data.lines)

        # Prepare template data
        template_data = [
            {
                "account_id": str(line.account_id),
                "debit_amount": str(line.debit_amount),
                "credit_amount": str(line.credit_amount),
                "narration": line.narration,
                "cost_center_id": str(line.cost_center_id) if line.cost_center_id else None,
            }
            for line in data.lines
        ]

        # Calculate initial next run date
        next_run = self._calculate_initial_next_run_date(
            data.frequency,
            data.start_date,
            data.day_of_month,
            data.day_of_week,
        )

        recurring = RecurringVoucher(
            organization_id=data.organization_id,
            voucher_type_id=data.voucher_type_id,
            template_name=data.template_name,
            description=data.description,
            frequency=data.frequency,
            day_of_month=data.day_of_month,
            day_of_week=data.day_of_week,
            start_date=data.start_date,
            end_date=data.end_date,
            next_run_date=next_run,
            total_occurrences=data.total_occurrences,
            auto_post=data.auto_post,
            auto_approve=data.auto_approve,
            narration_template=data.narration_template,
            total_amount=total_amount,
            template_data=template_data,
            notify_on_generation=data.notify_on_generation,
            notify_days_before=data.notify_days_before,
            created_by=user_id,
        )

        self.db.add(recurring)
        await self.db.flush()
        await self.db.refresh(recurring)

        return recurring

    async def update(
        self,
        recurring_id: UUID,
        data: RecurringVoucherUpdate,
        user_id: UUID,
    ) -> RecurringVoucher:
        """Update an existing recurring voucher template."""
        stmt = select(RecurringVoucher).where(RecurringVoucher.id == recurring_id)
        result = await self.db.execute(stmt)
        recurring = result.scalar_one_or_none()

        if not recurring:
            raise ValueError(f"Recurring voucher {recurring_id} not found")

        if recurring.status not in [RecurringVoucherStatus.ACTIVE, RecurringVoucherStatus.PAUSED]:
            raise ValueError("Cannot update a completed or cancelled recurring voucher")

        update_data = data.model_dump(exclude_unset=True)

        if "lines" in update_data and update_data["lines"]:
            lines = data.lines
            total_amount = sum(line.debit_amount for line in lines)
            template_data = [
                {
                    "account_id": str(line.account_id),
                    "debit_amount": str(line.debit_amount),
                    "credit_amount": str(line.credit_amount),
                    "narration": line.narration,
                    "cost_center_id": str(line.cost_center_id) if line.cost_center_id else None,
                }
                for line in lines
            ]
            recurring.total_amount = total_amount
            recurring.template_data = template_data
            del update_data["lines"]

        for key, value in update_data.items():
            setattr(recurring, key, value)

        # Recalculate next run date if frequency changed
        if "frequency" in update_data or "day_of_month" in update_data or "day_of_week" in update_data:
            recurring.next_run_date = self._calculate_next_run_date(
                recurring.frequency,
                recurring.last_run_date or date.today(),
                recurring.day_of_month,
                recurring.day_of_week,
            )

        recurring.modified_by = user_id

        await self.db.flush()
        await self.db.refresh(recurring)

        return recurring

    async def get(self, recurring_id: UUID) -> Optional[RecurringVoucher]:
        """Get a recurring voucher by ID."""
        stmt = select(RecurringVoucher).where(RecurringVoucher.id == recurring_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        organization_id: UUID,
        status: Optional[RecurringVoucherStatus] = None,
        frequency: Optional[RecurrenceFrequency] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> RecurringVoucherListResponse:
        """List recurring vouchers with pagination."""
        stmt = (
            select(RecurringVoucher)
            .where(RecurringVoucher.organization_id == organization_id)
            .where(RecurringVoucher.is_deleted == False)
        )

        if status:
            stmt = stmt.where(RecurringVoucher.status == status)
        if frequency:
            stmt = stmt.where(RecurringVoucher.frequency == frequency)

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar() or 0

        # Get paginated results
        stmt = stmt.order_by(RecurringVoucher.next_run_date.asc().nullslast())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(stmt)
        items = result.scalars().all()

        return RecurringVoucherListResponse(
            items=[
                RecurringVoucherListItem(
                    id=str(rv.id),
                    template_name=rv.template_name,
                    voucher_type_name=rv.voucher_type.name if rv.voucher_type else "",
                    frequency=rv.frequency,
                    total_amount=rv.total_amount,
                    next_run_date=rv.next_run_date,
                    last_run_date=rv.last_run_date,
                    completed_occurrences=rv.completed_occurrences,
                    total_occurrences=rv.total_occurrences,
                    status=rv.status,
                    auto_post=rv.auto_post,
                )
                for rv in items
            ],
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size,
        )

    async def get_with_lines(self, recurring_id: UUID) -> Optional[RecurringVoucherResponse]:
        """Get recurring voucher with full line details."""
        recurring = await self.get(recurring_id)
        if not recurring:
            return None

        # Get account details for lines
        account_ids = [UUID(line["account_id"]) for line in recurring.template_data]
        stmt = select(Account).where(Account.id.in_(account_ids))
        result = await self.db.execute(stmt)
        accounts = {str(a.id): a for a in result.scalars().all()}

        lines = []
        for line_data in recurring.template_data:
            account = accounts.get(line_data["account_id"])
            lines.append(
                RecurringVoucherLineResponse(
                    account_id=line_data["account_id"],
                    account_code=account.code if account else "",
                    account_name=account.name if account else "",
                    debit_amount=Decimal(line_data["debit_amount"]),
                    credit_amount=Decimal(line_data["credit_amount"]),
                    narration=line_data.get("narration"),
                    cost_center_id=line_data.get("cost_center_id"),
                )
            )

        return RecurringVoucherResponse(
            id=str(recurring.id),
            organization_id=str(recurring.organization_id),
            organization_name=recurring.organization.name if recurring.organization else "",
            voucher_type_id=str(recurring.voucher_type_id),
            voucher_type_name=recurring.voucher_type.name if recurring.voucher_type else "",
            template_name=recurring.template_name,
            description=recurring.description,
            frequency=recurring.frequency,
            day_of_month=recurring.day_of_month,
            day_of_week=recurring.day_of_week,
            start_date=recurring.start_date,
            end_date=recurring.end_date,
            next_run_date=recurring.next_run_date,
            last_run_date=recurring.last_run_date,
            total_occurrences=recurring.total_occurrences,
            completed_occurrences=recurring.completed_occurrences,
            status=recurring.status,
            auto_post=recurring.auto_post,
            auto_approve=recurring.auto_approve,
            narration_template=recurring.narration_template,
            total_amount=recurring.total_amount,
            lines=lines,
            notify_on_generation=recurring.notify_on_generation,
            notify_days_before=recurring.notify_days_before,
            created_at=recurring.created_at,
            updated_at=recurring.modified_at,
        )

    async def pause(
        self,
        recurring_id: UUID,
        user_id: UUID,
        reason: Optional[str] = None,
    ) -> RecurringVoucher:
        """Pause a recurring voucher."""
        recurring = await self.get(recurring_id)
        if not recurring:
            raise ValueError(f"Recurring voucher {recurring_id} not found")

        if recurring.status != RecurringVoucherStatus.ACTIVE:
            raise ValueError("Can only pause active recurring vouchers")

        recurring.status = RecurringVoucherStatus.PAUSED
        recurring.modified_by = user_id

        await self.db.flush()
        return recurring

    async def resume(
        self,
        recurring_id: UUID,
        user_id: UUID,
    ) -> RecurringVoucher:
        """Resume a paused recurring voucher."""
        recurring = await self.get(recurring_id)
        if not recurring:
            raise ValueError(f"Recurring voucher {recurring_id} not found")

        if recurring.status != RecurringVoucherStatus.PAUSED:
            raise ValueError("Can only resume paused recurring vouchers")

        recurring.status = RecurringVoucherStatus.ACTIVE

        # Recalculate next run date
        if recurring.next_run_date and recurring.next_run_date < date.today():
            recurring.next_run_date = self._calculate_next_run_date(
                recurring.frequency,
                date.today(),
                recurring.day_of_month,
                recurring.day_of_week,
            )

        recurring.modified_by = user_id

        await self.db.flush()
        return recurring

    async def cancel(
        self,
        recurring_id: UUID,
        user_id: UUID,
        reason: Optional[str] = None,
    ) -> RecurringVoucher:
        """Cancel a recurring voucher (cannot be undone)."""
        recurring = await self.get(recurring_id)
        if not recurring:
            raise ValueError(f"Recurring voucher {recurring_id} not found")

        if recurring.status in [RecurringVoucherStatus.COMPLETED, RecurringVoucherStatus.CANCELLED]:
            raise ValueError("Cannot cancel a completed or already cancelled recurring voucher")

        recurring.status = RecurringVoucherStatus.CANCELLED
        recurring.next_run_date = None
        recurring.modified_by = user_id

        await self.db.flush()
        return recurring

    async def generate_voucher(
        self,
        recurring_id: UUID,
        user_id: UUID,
        voucher_date: Optional[date] = None,
        narration_override: Optional[str] = None,
    ) -> GenerateVoucherResponse:
        """Generate a voucher from recurring template."""
        recurring = await self.get(recurring_id)
        if not recurring:
            return GenerateVoucherResponse(
                success=False,
                message=f"Recurring voucher {recurring_id} not found",
            )

        if recurring.status not in [RecurringVoucherStatus.ACTIVE, RecurringVoucherStatus.PAUSED]:
            return GenerateVoucherResponse(
                success=False,
                message="Cannot generate voucher from completed or cancelled template",
            )

        # Use provided date or today
        target_date = voucher_date or date.today()

        # Get active financial year and period
        fy_stmt = select(FinancialYear).where(
            and_(
                FinancialYear.organization_id == recurring.organization_id,
                FinancialYear.start_date <= target_date,
                FinancialYear.end_date >= target_date,
                FinancialYear.is_closed == False,
            )
        )
        fy_result = await self.db.execute(fy_stmt)
        financial_year = fy_result.scalar_one_or_none()

        if not financial_year:
            return GenerateVoucherResponse(
                success=False,
                message=f"No active financial year found for date {target_date}",
            )

        # Get period
        period_stmt = select(FinancialPeriod).where(
            and_(
                FinancialPeriod.financial_year_id == financial_year.id,
                FinancialPeriod.start_date <= target_date,
                FinancialPeriod.end_date >= target_date,
                FinancialPeriod.is_locked == False,
            )
        )
        period_result = await self.db.execute(period_stmt)
        period = period_result.scalar_one_or_none()

        if not period:
            return GenerateVoucherResponse(
                success=False,
                message=f"No open period found for date {target_date}",
            )

        # Generate voucher number
        voucher_type = recurring.voucher_type
        prefix = voucher_type.prefix or "V"
        count_stmt = select(func.count()).where(
            and_(
                Voucher.voucher_type_id == recurring.voucher_type_id,
                Voucher.financial_year_id == financial_year.id,
            )
        )
        count = (await self.db.execute(count_stmt)).scalar() or 0
        voucher_number = f"{prefix}/{financial_year.code}/{count + 1:06d}"

        # Build narration
        narration = narration_override
        if not narration and recurring.narration_template:
            narration = recurring.narration_template.format(
                month=target_date.strftime("%B"),
                year=str(target_date.year),
                date=target_date.strftime("%d/%m/%Y"),
            )

        # Create voucher
        voucher = Voucher(
            voucher_type_id=recurring.voucher_type_id,
            voucher_number=voucher_number,
            voucher_date=target_date,
            financial_year_id=financial_year.id,
            period_id=period.id,
            narration=narration,
            total_debit=recurring.total_amount,
            total_credit=recurring.total_amount,
            status=VoucherStatus.DRAFT,
            organization_id=recurring.organization_id,
            created_by=user_id,
        )

        self.db.add(voucher)
        await self.db.flush()

        # Create voucher lines
        for i, line_data in enumerate(recurring.template_data, start=1):
            voucher_line = VoucherLine(
                voucher_id=voucher.id,
                line_number=i,
                account_id=UUID(line_data["account_id"]),
                debit_amount=Decimal(line_data["debit_amount"]),
                credit_amount=Decimal(line_data["credit_amount"]),
                narration=line_data.get("narration"),
                cost_center_id=UUID(line_data["cost_center_id"]) if line_data.get("cost_center_id") else None,
            )
            self.db.add(voucher_line)

        # Update recurring voucher
        recurring.last_run_date = target_date
        recurring.completed_occurrences += 1
        recurring.next_run_date = self._calculate_next_run_date(
            recurring.frequency,
            target_date,
            recurring.day_of_month,
            recurring.day_of_week,
        )

        # Check if completed
        if recurring.end_date and recurring.next_run_date > recurring.end_date:
            recurring.status = RecurringVoucherStatus.COMPLETED
            recurring.next_run_date = None
        elif recurring.total_occurrences and recurring.completed_occurrences >= recurring.total_occurrences:
            recurring.status = RecurringVoucherStatus.COMPLETED
            recurring.next_run_date = None

        # Create log entry
        log_entry = RecurringVoucherLog(
            recurring_voucher_id=recurring.id,
            voucher_id=voucher.id,
            scheduled_date=target_date,
            generated_at=datetime.utcnow(),
            occurrence_number=recurring.completed_occurrences,
            status="GENERATED",
        )
        self.db.add(log_entry)

        await self.db.flush()

        # Auto-post if configured
        if recurring.auto_post:
            voucher.status = VoucherStatus.APPROVED
            voucher.approved_at = datetime.utcnow()
            voucher.approved_by = user_id
            if recurring.auto_approve:
                voucher.status = VoucherStatus.POSTED
                voucher.posted_at = datetime.utcnow()
                voucher.posted_by = user_id

        await self.db.flush()
        await self.db.refresh(voucher)

        return GenerateVoucherResponse(
            success=True,
            message=f"Voucher {voucher.voucher_number} generated successfully",
            voucher_id=str(voucher.id),
            voucher_number=voucher.voucher_number,
        )

    async def get_due_vouchers(
        self,
        organization_id: UUID,
        as_of_date: Optional[date] = None,
    ) -> List[RecurringVoucher]:
        """Get recurring vouchers due for generation."""
        target_date = as_of_date or date.today()

        stmt = select(RecurringVoucher).where(
            and_(
                RecurringVoucher.organization_id == organization_id,
                RecurringVoucher.status == RecurringVoucherStatus.ACTIVE,
                RecurringVoucher.next_run_date <= target_date,
                RecurringVoucher.is_deleted == False,
            )
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def process_due_vouchers(
        self,
        organization_id: UUID,
        user_id: UUID,
    ) -> List[GenerateVoucherResponse]:
        """Process all due recurring vouchers."""
        due_vouchers = await self.get_due_vouchers(organization_id)
        results = []

        for rv in due_vouchers:
            result = await self.generate_voucher(rv.id, user_id)
            results.append(result)

        return results

    async def get_upcoming(
        self,
        organization_id: UUID,
        days_ahead: int = 7,
    ) -> List[UpcomingRecurringVoucher]:
        """Get upcoming recurring vouchers."""
        today = date.today()
        end_date = today + timedelta(days=days_ahead)

        stmt = select(RecurringVoucher).where(
            and_(
                RecurringVoucher.organization_id == organization_id,
                RecurringVoucher.status == RecurringVoucherStatus.ACTIVE,
                RecurringVoucher.next_run_date.isnot(None),
                RecurringVoucher.next_run_date <= end_date,
                RecurringVoucher.is_deleted == False,
            )
        ).order_by(RecurringVoucher.next_run_date.asc())

        result = await self.db.execute(stmt)
        items = result.scalars().all()

        return [
            UpcomingRecurringVoucher(
                id=str(rv.id),
                template_name=rv.template_name,
                voucher_type_name=rv.voucher_type.name if rv.voucher_type else "",
                next_run_date=rv.next_run_date,
                total_amount=rv.total_amount,
                days_until_due=(rv.next_run_date - today).days,
            )
            for rv in items
            if rv.next_run_date
        ]

    async def get_stats(self, organization_id: UUID) -> RecurringVoucherStats:
        """Get statistics for recurring vouchers."""
        today = date.today()
        week_end = today + timedelta(days=7)
        month_start = today.replace(day=1)

        # Count active
        active_stmt = select(func.count()).where(
            and_(
                RecurringVoucher.organization_id == organization_id,
                RecurringVoucher.status == RecurringVoucherStatus.ACTIVE,
                RecurringVoucher.is_deleted == False,
            )
        )
        total_active = (await self.db.execute(active_stmt)).scalar() or 0

        # Count paused
        paused_stmt = select(func.count()).where(
            and_(
                RecurringVoucher.organization_id == organization_id,
                RecurringVoucher.status == RecurringVoucherStatus.PAUSED,
                RecurringVoucher.is_deleted == False,
            )
        )
        total_paused = (await self.db.execute(paused_stmt)).scalar() or 0

        # Due today
        due_today_stmt = select(func.count()).where(
            and_(
                RecurringVoucher.organization_id == organization_id,
                RecurringVoucher.status == RecurringVoucherStatus.ACTIVE,
                RecurringVoucher.next_run_date == today,
                RecurringVoucher.is_deleted == False,
            )
        )
        due_today = (await self.db.execute(due_today_stmt)).scalar() or 0

        # Due this week
        due_week_stmt = select(func.count()).where(
            and_(
                RecurringVoucher.organization_id == organization_id,
                RecurringVoucher.status == RecurringVoucherStatus.ACTIVE,
                RecurringVoucher.next_run_date <= week_end,
                RecurringVoucher.is_deleted == False,
            )
        )
        due_this_week = (await self.db.execute(due_week_stmt)).scalar() or 0

        # Generated this month
        log_count_stmt = select(func.count()).select_from(RecurringVoucherLog).join(
            RecurringVoucher
        ).where(
            and_(
                RecurringVoucher.organization_id == organization_id,
                RecurringVoucherLog.generated_at >= month_start,
                RecurringVoucherLog.status == "GENERATED",
            )
        )
        total_generated = (await self.db.execute(log_count_stmt)).scalar() or 0

        # Total amount this month
        amount_stmt = select(func.sum(RecurringVoucher.total_amount)).select_from(
            RecurringVoucherLog
        ).join(RecurringVoucher).where(
            and_(
                RecurringVoucher.organization_id == organization_id,
                RecurringVoucherLog.generated_at >= month_start,
                RecurringVoucherLog.status == "GENERATED",
            )
        )
        total_amount = (await self.db.execute(amount_stmt)).scalar() or Decimal("0.00")

        return RecurringVoucherStats(
            total_active=total_active,
            total_paused=total_paused,
            due_today=due_today,
            due_this_week=due_this_week,
            total_generated_this_month=total_generated,
            total_amount_this_month=total_amount,
        )

    async def get_logs(
        self,
        recurring_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> RecurringVoucherLogListResponse:
        """Get generation logs for a recurring voucher."""
        stmt = (
            select(RecurringVoucherLog)
            .where(RecurringVoucherLog.recurring_voucher_id == recurring_id)
            .order_by(RecurringVoucherLog.scheduled_date.desc())
        )

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar() or 0

        # Get paginated results
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(stmt)
        items = result.scalars().all()

        return RecurringVoucherLogListResponse(
            items=[
                RecurringVoucherLogResponse(
                    id=str(log.id),
                    recurring_voucher_id=str(log.recurring_voucher_id),
                    recurring_voucher_name=log.recurring_voucher.template_name if log.recurring_voucher else "",
                    voucher_id=str(log.voucher_id) if log.voucher_id else None,
                    voucher_number=None,  # Would need to join with Voucher
                    scheduled_date=log.scheduled_date,
                    generated_at=log.generated_at,
                    occurrence_number=log.occurrence_number,
                    status=log.status,
                    error_message=log.error_message,
                )
                for log in items
            ],
            total=total,
            page=page,
            page_size=page_size,
            pages=(total + page_size - 1) // page_size,
        )

    async def delete(self, recurring_id: UUID, user_id: UUID) -> bool:
        """Soft delete a recurring voucher."""
        recurring = await self.get(recurring_id)
        if not recurring:
            return False

        recurring.is_deleted = True
        recurring.status = RecurringVoucherStatus.CANCELLED
        recurring.next_run_date = None
        recurring.modified_by = user_id

        await self.db.flush()
        return True
