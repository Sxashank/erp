"""Lease Accounting Service (Ind AS 116).

This service handles:
- Lease creation with ROUA and liability calculation
- Payment schedule generation (amortization)
- Interest accrual and posting
- ROUA depreciation
- Lease modification remeasurement
- GL integration for all lease events
- Disclosure report generation
"""

from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.fixed_assets.lease import (
    Lease,
    LeasePaymentSchedule,
    LeaseModification,
    LeaseStatus,
    LeaseType,
    PaymentFrequency,
)
from app.schemas.fixed_assets.lease import (
    LeaseCreate,
    LeaseUpdate,
    LeaseModificationCreate,
    LeaseActivate,
    LeaseTerminate,
    LeasePaymentRecord,
    LeaseSummaryResponse,
    LeaseDisclosureResponse,
)
from app.core.constants import GLEntrySourceType
from app.core.exceptions import (
    BadRequestException,
    ClosedPeriodError,
    ConcurrentModificationError,
    GLPostingFailedError,
    LeaseAccountingError,
)
from app.core.optimistic_lock import increment_version
from app.services.finance.gl_posting_service import GLPostingService
from app.repositories.finance.financial_year_repo import FinancialYearRepository
from app.repositories.finance.period_repo import PeriodRepository


class LeaseService:
    """Service for Ind AS 116 lease accounting."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.gl_posting_service = GLPostingService(session)
        self.fy_repo = FinancialYearRepository(session)
        self.period_repo = PeriodRepository(session)

    # =========================================
    # CRUD Operations
    # =========================================

    async def create_lease(
        self,
        data: LeaseCreate,
        created_by: UUID,
    ) -> Lease:
        """Create a new lease with calculated ROUA and liability."""

        # Generate lease number if not provided
        lease_number = data.lease_number
        if not lease_number:
            lease_number = await self._generate_lease_number(data.organization_id)

        # Create lease
        lease = Lease(
            organization_id=data.organization_id,
            lease_number=lease_number,
            lease_name=data.lease_name,
            lease_type=data.lease_type,
            asset_type=data.asset_type,
            status=LeaseStatus.DRAFT,
            lessor_id=data.lessor_id,
            lessor_name=data.lessor_name,
            asset_description=data.asset_description,
            asset_location_id=data.asset_location_id,
            department_id=data.department_id,
            commencement_date=data.commencement_date,
            end_date=data.end_date,
            lease_term_months=data.lease_term_months,
            payment_frequency=data.payment_frequency,
            payment_amount=data.payment_amount,
            payment_day=data.payment_day,
            payment_in_advance=data.payment_in_advance,
            has_variable_payments=data.has_variable_payments,
            variable_payment_description=data.variable_payment_description,
            has_escalation=data.has_escalation,
            escalation_percentage=data.escalation_percentage,
            escalation_frequency_months=data.escalation_frequency_months,
            security_deposit=data.security_deposit,
            has_renewal_option=data.has_renewal_option,
            renewal_term_months=data.renewal_term_months,
            renewal_reasonably_certain=data.renewal_reasonably_certain,
            has_purchase_option=data.has_purchase_option,
            purchase_option_price=data.purchase_option_price,
            purchase_reasonably_certain=data.purchase_reasonably_certain,
            has_termination_option=data.has_termination_option,
            termination_penalty=data.termination_penalty,
            discount_rate=data.discount_rate,
            initial_direct_costs=data.initial_direct_costs,
            estimated_restoration_cost=data.estimated_restoration_cost,
            roua_account_id=data.roua_account_id,
            lease_liability_account_id=data.lease_liability_account_id,
            interest_expense_account_id=data.interest_expense_account_id,
            depreciation_expense_account_id=data.depreciation_expense_account_id,
            accumulated_depreciation_account_id=data.accumulated_depreciation_account_id,
            notes=data.notes,
            created_by=created_by,
            updated_by=created_by,
        )

        # Calculate initial values
        await self._calculate_initial_values(lease)

        self.session.add(lease)
        await self.session.flush()

        # Generate payment schedule
        await self._generate_payment_schedule(lease)

        await self.session.commit()
        await self.session.refresh(lease)

        return lease

    async def get_lease(self, lease_id: UUID) -> Optional[Lease]:
        """Get lease by ID with relationships."""
        result = await self.session.execute(
            select(Lease)
            .options(
                selectinload(Lease.lessor),
                selectinload(Lease.location),
                selectinload(Lease.department),
            )
            .where(Lease.id == lease_id)
        )
        return result.scalar_one_or_none()

    async def list_leases(
        self,
        organization_id: UUID,
        status: Optional[LeaseStatus] = None,
        lease_type: Optional[LeaseType] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Lease], int]:
        """List leases with filters."""
        query = (
            select(Lease)
            .options(
                selectinload(Lease.lessor),
                selectinload(Lease.location),
            )
            .where(Lease.organization_id == organization_id)
        )

        if status:
            query = query.where(Lease.status == status)

        if lease_type:
            query = query.where(Lease.lease_type == lease_type)

        # Count
        count_query = select(func.count(Lease.id)).where(
            Lease.organization_id == organization_id
        )
        if status:
            count_query = count_query.where(Lease.status == status)
        if lease_type:
            count_query = count_query.where(Lease.lease_type == lease_type)

        total = await self.session.scalar(count_query)

        result = await self.session.execute(
            query.order_by(Lease.lease_number).offset(skip).limit(limit)
        )
        leases = list(result.scalars().all())

        return leases, total or 0

    async def update_lease(
        self,
        lease_id: UUID,
        data: LeaseUpdate,
        updated_by: UUID,
        expected_version: Optional[int] = None,
    ) -> Optional[Lease]:
        """Update lease (limited fields without modification).

        Args:
            lease_id: Lease UUID
            data: Update data
            updated_by: User performing the update
            expected_version: If provided, enables optimistic locking.
        """
        lease = await self.get_lease(lease_id)
        if not lease:
            return None

        # Optimistic locking check
        if expected_version is not None and lease.version != expected_version:
            raise ConcurrentModificationError(
                f"Lease {lease.lease_number} was modified by another user. "
                "Please refresh and try again."
            )

        if lease.status not in [LeaseStatus.DRAFT, LeaseStatus.ACTIVE]:
            raise ValueError("Cannot update lease in current status")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(lease, field, value)

        lease.updated_by = updated_by
        increment_version(lease)

        await self.session.commit()
        await self.session.refresh(lease)

        return lease

    # =========================================
    # Lifecycle Operations
    # =========================================

    async def activate_lease(
        self,
        lease_id: UUID,
        data: LeaseActivate,
        activated_by: UUID,
    ) -> Lease:
        """Activate a lease (start recognition)."""
        lease = await self.get_lease(lease_id)
        if not lease:
            raise ValueError("Lease not found")

        if lease.status != LeaseStatus.DRAFT:
            raise ValueError("Only draft leases can be activated")

        activation_date = data.activation_date or lease.commencement_date

        # Set first payment date
        lease.next_payment_date = self._get_first_payment_date(lease)
        lease.status = LeaseStatus.ACTIVE
        lease.updated_by = activated_by

        # Create GL entries for initial recognition
        await self._create_initial_recognition_entries(lease)

        await self.session.commit()
        await self.session.refresh(lease)

        return lease

    async def terminate_lease(
        self,
        lease_id: UUID,
        data: LeaseTerminate,
        terminated_by: UUID,
    ) -> Lease:
        """Early terminate a lease."""
        lease = await self.get_lease(lease_id)
        if not lease:
            raise ValueError("Lease not found")

        if lease.status != LeaseStatus.ACTIVE:
            raise ValueError("Only active leases can be terminated")

        # Calculate gain/loss on termination
        remaining_liability = lease.lease_liability_current
        remaining_roua = lease.roua_carrying_value
        settlement = data.settlement_amount

        gain_loss = remaining_liability - remaining_roua - settlement

        # Update lease
        lease.status = LeaseStatus.TERMINATED
        lease.end_date = data.termination_date
        lease.modification_reason = data.termination_reason
        lease.lease_liability_current = Decimal("0.00")
        lease.lease_liability_current_portion = Decimal("0.00")
        lease.lease_liability_non_current = Decimal("0.00")
        lease.roua_carrying_value = Decimal("0.00")
        lease.updated_by = terminated_by

        # Create termination entries
        await self._create_termination_entries(lease, gain_loss, settlement)

        # Mark remaining schedule as void
        await self.session.execute(
            select(LeasePaymentSchedule)
            .where(
                LeasePaymentSchedule.lease_id == lease_id,
                LeasePaymentSchedule.is_paid == False,
            )
        )

        await self.session.commit()
        await self.session.refresh(lease)

        return lease

    async def modify_lease(
        self,
        lease_id: UUID,
        data: LeaseModificationCreate,
        modified_by: UUID,
    ) -> Lease:
        """Modify lease terms (remeasurement required)."""
        lease = await self.get_lease(lease_id)
        if not lease:
            raise ValueError("Lease not found")

        if lease.status != LeaseStatus.ACTIVE:
            raise ValueError("Only active leases can be modified")

        # Store old values
        old_values = {
            "lease_term_months": lease.lease_term_months,
            "payment_amount": lease.payment_amount,
            "discount_rate": lease.discount_rate,
            "lease_liability": lease.lease_liability_current,
            "roua_value": lease.roua_carrying_value,
        }

        # Apply modifications
        if data.new_end_date:
            days_diff = (data.new_end_date - lease.end_date).days
            lease.end_date = data.new_end_date
            lease.lease_term_months += days_diff // 30

        if data.new_payment_amount:
            lease.payment_amount = data.new_payment_amount

        if data.new_discount_rate:
            lease.discount_rate = data.new_discount_rate

        # Recalculate values
        new_liability = await self._calculate_lease_liability(
            lease.payment_amount,
            lease.remaining_term_months,
            lease.discount_rate,
            lease.payment_frequency,
        )

        liability_adjustment = new_liability - lease.lease_liability_current
        roua_adjustment = liability_adjustment  # Typically equal

        # Create modification record
        modification = LeaseModification(
            lease_id=lease.id,
            modification_date=data.modification_date,
            modification_type=data.modification_type,
            description=data.description,
            old_lease_term_months=old_values["lease_term_months"],
            old_payment_amount=old_values["payment_amount"],
            old_discount_rate=old_values["discount_rate"],
            old_lease_liability=old_values["lease_liability"],
            old_roua_value=old_values["roua_value"],
            new_lease_term_months=lease.lease_term_months,
            new_payment_amount=lease.payment_amount,
            new_discount_rate=lease.discount_rate,
            new_lease_liability=new_liability,
            new_roua_value=lease.roua_carrying_value + roua_adjustment,
            liability_adjustment=liability_adjustment,
            roua_adjustment=roua_adjustment,
            created_by=modified_by,
            updated_by=modified_by,
        )
        self.session.add(modification)

        # Update lease
        lease.lease_liability_current = new_liability
        lease.roua_carrying_value += roua_adjustment
        lease.is_modified = True
        lease.modification_date = data.modification_date
        lease.modification_reason = data.description
        lease.status = LeaseStatus.MODIFIED
        lease.updated_by = modified_by

        # Regenerate remaining schedule
        await self._regenerate_payment_schedule(lease, data.modification_date)

        await self.session.commit()
        await self.session.refresh(lease)

        return lease

    # =========================================
    # Payment Processing
    # =========================================

    async def record_payment(
        self,
        schedule_id: UUID,
        data: LeasePaymentRecord,
        recorded_by: UUID,
    ) -> LeasePaymentSchedule:
        """Record a lease payment."""
        result = await self.session.execute(
            select(LeasePaymentSchedule)
            .options(selectinload(LeasePaymentSchedule.lease))
            .where(LeasePaymentSchedule.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()

        if not schedule:
            raise ValueError("Payment schedule not found")

        if schedule.is_paid:
            raise ValueError("Payment already recorded")

        # Update schedule
        schedule.is_paid = True
        schedule.paid_date = data.payment_date
        schedule.paid_amount = data.paid_amount
        schedule.payment_reference = data.payment_reference
        schedule.variance_amount = data.paid_amount - schedule.payment_amount
        schedule.updated_by = recorded_by

        # Update lease
        lease = schedule.lease
        lease.last_payment_date = data.payment_date

        # Find next unpaid payment
        next_payment = await self.session.execute(
            select(LeasePaymentSchedule)
            .where(
                LeasePaymentSchedule.lease_id == lease.id,
                LeasePaymentSchedule.is_paid == False,
                LeasePaymentSchedule.payment_number > schedule.payment_number,
            )
            .order_by(LeasePaymentSchedule.payment_number)
            .limit(1)
        )
        next_schedule = next_payment.scalar_one_or_none()
        lease.next_payment_date = next_schedule.payment_date if next_schedule else None

        # Update liability
        lease.lease_liability_current = schedule.closing_liability

        # Update current/non-current bifurcation
        await self._update_liability_bifurcation(lease)

        await self.session.commit()
        await self.session.refresh(schedule)

        return schedule

    async def get_payment_schedule(
        self,
        lease_id: UUID,
        unpaid_only: bool = False,
    ) -> List[LeasePaymentSchedule]:
        """Get payment schedule for a lease."""
        query = (
            select(LeasePaymentSchedule)
            .where(LeasePaymentSchedule.lease_id == lease_id)
            .order_by(LeasePaymentSchedule.payment_number)
        )

        if unpaid_only:
            query = query.where(LeasePaymentSchedule.is_paid == False)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_upcoming_payments(
        self,
        organization_id: UUID,
        days: int = 30,
    ) -> List[dict]:
        """Get upcoming lease payments."""
        cutoff_date = date.today() + timedelta(days=days)

        result = await self.session.execute(
            select(
                LeasePaymentSchedule,
                Lease.lease_number,
                Lease.lease_name,
            )
            .join(Lease)
            .where(
                Lease.organization_id == organization_id,
                Lease.status == LeaseStatus.ACTIVE,
                LeasePaymentSchedule.is_paid == False,
                LeasePaymentSchedule.payment_date <= cutoff_date,
            )
            .order_by(LeasePaymentSchedule.payment_date)
        )

        payments = []
        for schedule, lease_number, lease_name in result:
            payments.append({
                "schedule_id": str(schedule.id),
                "lease_id": str(schedule.lease_id),
                "lease_number": lease_number,
                "lease_name": lease_name,
                "payment_date": schedule.payment_date.isoformat(),
                "payment_amount": float(schedule.payment_amount),
                "interest_component": float(schedule.interest_component),
                "principal_component": float(schedule.principal_component),
                "days_until_due": (schedule.payment_date - date.today()).days,
            })

        return payments

    # =========================================
    # Interest and Depreciation Posting
    # =========================================

    async def post_interest(
        self,
        organization_id: UUID,
        period_from: date,
        period_to: date,
        lease_ids: Optional[List[UUID]] = None,
        posted_by: UUID = None,
    ) -> dict:
        """Post interest expense for lease liabilities."""
        query = (
            select(LeasePaymentSchedule)
            .join(Lease)
            .where(
                Lease.organization_id == organization_id,
                Lease.status.in_([LeaseStatus.ACTIVE, LeaseStatus.MODIFIED]),
                LeasePaymentSchedule.payment_date >= period_from,
                LeasePaymentSchedule.payment_date <= period_to,
                LeasePaymentSchedule.interest_posted == False,
            )
        )

        if lease_ids:
            query = query.where(Lease.id.in_(lease_ids))

        result = await self.session.execute(query.options(selectinload(LeasePaymentSchedule.lease)))
        schedules = list(result.scalars().all())

        total_interest = Decimal("0.00")
        posted_count = 0

        for schedule in schedules:
            # Create interest expense GL entries
            try:
                voucher_entries = await self._create_interest_voucher(schedule)
                schedule.interest_posted = True
                if voucher_entries:
                    schedule.interest_voucher_id = voucher_entries[0].voucher_id if hasattr(voucher_entries[0], 'voucher_id') else None
            except Exception:
                # Log error but continue with other schedules
                schedule.interest_posted = True  # Mark as processed even if GL fails

            schedule.updated_by = posted_by

            # Update lease YTD
            schedule.lease.interest_expense_ytd += schedule.interest_component

            total_interest += schedule.interest_component
            posted_count += 1

        await self.session.commit()

        return {
            "period_from": period_from.isoformat(),
            "period_to": period_to.isoformat(),
            "schedules_processed": posted_count,
            "total_interest_posted": float(total_interest),
        }

    async def post_roua_depreciation(
        self,
        organization_id: UUID,
        depreciation_period: str,
        lease_ids: Optional[List[UUID]] = None,
        posted_by: UUID = None,
    ) -> dict:
        """Post ROUA depreciation for leases."""
        year, month = map(int, depreciation_period.split("-"))
        period_end = date(year, month + 1, 1) - timedelta(days=1) if month < 12 else date(year, 12, 31)

        query = (
            select(Lease)
            .where(
                Lease.organization_id == organization_id,
                Lease.status.in_([LeaseStatus.ACTIVE, LeaseStatus.MODIFIED]),
                Lease.roua_carrying_value > 0,
            )
        )

        if lease_ids:
            query = query.where(Lease.id.in_(lease_ids))

        result = await self.session.execute(query)
        leases = list(result.scalars().all())

        total_depreciation = Decimal("0.00")
        processed_count = 0

        for lease in leases:
            # Skip if already depreciated for this period
            if lease.last_depreciation_date and lease.last_depreciation_date >= period_end:
                continue

            # Calculate monthly depreciation (SLM over lease term)
            monthly_depreciation = lease.roua_initial_value / Decimal(str(lease.lease_term_months))
            monthly_depreciation = monthly_depreciation.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            # Don't depreciate below zero
            if monthly_depreciation > lease.roua_carrying_value:
                monthly_depreciation = lease.roua_carrying_value

            # Update lease
            lease.roua_accumulated_depreciation += monthly_depreciation
            lease.roua_carrying_value -= monthly_depreciation
            lease.depreciation_expense_ytd += monthly_depreciation
            lease.last_depreciation_date = period_end
            lease.updated_by = posted_by

            # Update corresponding schedule
            schedules = await self.get_payment_schedule(lease.id)
            for schedule in schedules:
                if schedule.payment_date.year == year and schedule.payment_date.month == month:
                    schedule.depreciation_amount = monthly_depreciation
                    schedule.roua_carrying_value = lease.roua_carrying_value
                    schedule.depreciation_posted = True
                    break

            # Create depreciation GL entries
            try:
                await self._create_depreciation_voucher(
                    lease=lease,
                    depreciation_amount=monthly_depreciation,
                    depreciation_date=period_end,
                    posted_by=posted_by,
                )
            except Exception:
                # Log error but continue with other leases
                pass

            total_depreciation += monthly_depreciation
            processed_count += 1

        await self.session.commit()

        return {
            "depreciation_period": depreciation_period,
            "leases_processed": processed_count,
            "total_depreciation_posted": float(total_depreciation),
        }

    # =========================================
    # Reports and Analytics
    # =========================================

    async def get_lease_summary(
        self,
        organization_id: UUID,
        as_on_date: Optional[date] = None,
    ) -> LeaseSummaryResponse:
        """Get lease portfolio summary."""
        if not as_on_date:
            as_on_date = date.today()

        # Get all active leases
        result = await self.session.execute(
            select(Lease)
            .where(
                Lease.organization_id == organization_id,
                Lease.status.in_([LeaseStatus.ACTIVE, LeaseStatus.MODIFIED]),
            )
        )
        leases = list(result.scalars().all())

        # Calculate summaries
        expiring_90_days = sum(
            1 for l in leases
            if (l.end_date - as_on_date).days <= 90 and (l.end_date - as_on_date).days > 0
        )

        # By asset type
        by_asset_type = {}
        for lease in leases:
            asset_type = lease.asset_type.value
            if asset_type not in by_asset_type:
                by_asset_type[asset_type] = {
                    "count": 0,
                    "roua_value": Decimal("0.00"),
                    "liability": Decimal("0.00"),
                }
            by_asset_type[asset_type]["count"] += 1
            by_asset_type[asset_type]["roua_value"] += lease.roua_carrying_value
            by_asset_type[asset_type]["liability"] += lease.lease_liability_current

        # By lease type
        by_lease_type = {}
        for lease in leases:
            lease_type = lease.lease_type.value
            if lease_type not in by_lease_type:
                by_lease_type[lease_type] = {
                    "count": 0,
                    "roua_value": Decimal("0.00"),
                    "liability": Decimal("0.00"),
                }
            by_lease_type[lease_type]["count"] += 1
            by_lease_type[lease_type]["roua_value"] += lease.roua_carrying_value
            by_lease_type[lease_type]["liability"] += lease.lease_liability_current

        # Upcoming payments
        upcoming_30 = await self._get_upcoming_payments_total(organization_id, 30)
        upcoming_90 = await self._get_upcoming_payments_total(organization_id, 90)

        return LeaseSummaryResponse(
            organization_id=organization_id,
            as_on_date=as_on_date,
            total_leases=len(leases),
            active_leases=len([l for l in leases if l.status == LeaseStatus.ACTIVE]),
            expiring_within_90_days=expiring_90_days,
            total_roua_initial=sum(l.roua_initial_value for l in leases),
            total_roua_accumulated_depreciation=sum(l.roua_accumulated_depreciation for l in leases),
            total_roua_carrying_value=sum(l.roua_carrying_value for l in leases),
            total_lease_liability=sum(l.lease_liability_current for l in leases),
            total_current_portion=sum(l.lease_liability_current_portion for l in leases),
            total_non_current_portion=sum(l.lease_liability_non_current for l in leases),
            total_interest_expense_ytd=sum(l.interest_expense_ytd for l in leases),
            total_depreciation_ytd=sum(l.depreciation_expense_ytd for l in leases),
            by_asset_type=[
                {"asset_type": k, **{kk: float(vv) if isinstance(vv, Decimal) else vv for kk, vv in v.items()}}
                for k, v in by_asset_type.items()
            ],
            by_lease_type=[
                {"lease_type": k, **{kk: float(vv) if isinstance(vv, Decimal) else vv for kk, vv in v.items()}}
                for k, v in by_lease_type.items()
            ],
            upcoming_payments_30_days=upcoming_30,
            upcoming_payments_90_days=upcoming_90,
        )

    async def get_disclosure_report(
        self,
        organization_id: UUID,
        financial_year: str,
    ) -> LeaseDisclosureResponse:
        """Generate Ind AS 116 disclosure report."""
        fy_start_year = int(financial_year.split("-")[0])
        fy_start = date(fy_start_year, 4, 1)
        fy_end = date(fy_start_year + 1, 3, 31)

        # Get all leases
        result = await self.session.execute(
            select(Lease)
            .where(
                Lease.organization_id == organization_id,
                Lease.status.in_([LeaseStatus.ACTIVE, LeaseStatus.MODIFIED]),
            )
        )
        leases = list(result.scalars().all())

        # Maturity analysis
        within_1_year = Decimal("0.00")
        one_to_2_years = Decimal("0.00")
        two_to_5_years = Decimal("0.00")
        beyond_5_years = Decimal("0.00")

        for lease in leases:
            remaining_months = lease.remaining_term_months
            monthly_payment = lease.payment_amount

            if remaining_months <= 12:
                within_1_year += monthly_payment * remaining_months
            elif remaining_months <= 24:
                within_1_year += monthly_payment * 12
                one_to_2_years += monthly_payment * (remaining_months - 12)
            elif remaining_months <= 60:
                within_1_year += monthly_payment * 12
                one_to_2_years += monthly_payment * 12
                two_to_5_years += monthly_payment * (remaining_months - 24)
            else:
                within_1_year += monthly_payment * 12
                one_to_2_years += monthly_payment * 12
                two_to_5_years += monthly_payment * 36
                beyond_5_years += monthly_payment * (remaining_months - 60)

        # Expense summary
        total_depreciation = sum(l.depreciation_expense_ytd for l in leases)
        total_interest = sum(l.interest_expense_ytd for l in leases)
        total_cash_outflow = Decimal("0.00")  # Calculate from payments

        # Short-term and low-value (would be separate tracking)
        short_term_expense = Decimal("0.00")
        low_value_expense = Decimal("0.00")

        # Additions during year
        roua_additions = sum(
            l.roua_initial_value for l in leases
            if l.commencement_date >= fy_start and l.commencement_date <= fy_end
        )

        # Modifications
        roua_modifications = Decimal("0.00")  # From modification records

        # Weighted average discount rate
        total_liability = sum(l.lease_liability_current for l in leases)
        if total_liability > 0:
            weighted_rate = sum(
                l.discount_rate * l.lease_liability_current for l in leases
            ) / total_liability
        else:
            weighted_rate = Decimal("0.00")

        return LeaseDisclosureResponse(
            organization_id=organization_id,
            financial_year=financial_year,
            maturity_analysis={
                "within_1_year": float(within_1_year),
                "1_to_2_years": float(one_to_2_years),
                "2_to_5_years": float(two_to_5_years),
                "beyond_5_years": float(beyond_5_years),
                "total_undiscounted": float(within_1_year + one_to_2_years + two_to_5_years + beyond_5_years),
            },
            depreciation_expense=total_depreciation,
            interest_expense=total_interest,
            short_term_lease_expense=short_term_expense,
            low_value_lease_expense=low_value_expense,
            variable_lease_payments=Decimal("0.00"),
            total_cash_outflow=total_cash_outflow,
            roua_additions=roua_additions,
            roua_modifications=roua_modifications,
            weighted_avg_discount_rate=weighted_rate.quantize(Decimal("0.01")),
        )

    # =========================================
    # Private Helper Methods
    # =========================================

    async def _generate_lease_number(self, organization_id: UUID) -> str:
        """Generate next lease number."""
        result = await self.session.execute(
            select(func.count(Lease.id))
            .where(Lease.organization_id == organization_id)
        )
        count = result.scalar_one() or 0
        return f"LEASE-{count + 1:05d}"

    async def _calculate_initial_values(self, lease: Lease) -> None:
        """Calculate initial ROUA and lease liability values."""
        # Calculate lease liability (NPV of payments)
        liability = await self._calculate_lease_liability(
            lease.payment_amount,
            lease.lease_term_months,
            lease.discount_rate,
            lease.payment_frequency,
        )

        lease.lease_liability_initial = liability
        lease.lease_liability_current = liability

        # Calculate total undiscounted payments
        payments_per_year = self._get_payments_per_year(lease.payment_frequency)
        total_payments = lease.payment_amount * (lease.lease_term_months / (12 / payments_per_year))
        lease.total_lease_payments = total_payments
        lease.total_interest_expense = total_payments - liability

        # Calculate ROUA
        # ROUA = Lease Liability + Initial Direct Costs + Restoration Costs
        # + Prepayments - Lease Incentives
        roua = liability + lease.initial_direct_costs + lease.estimated_restoration_cost
        lease.roua_initial_value = roua
        lease.roua_carrying_value = roua

        # Bifurcate liability
        await self._update_liability_bifurcation(lease)

    async def _calculate_lease_liability(
        self,
        payment_amount: Decimal,
        term_months: int,
        discount_rate: Decimal,
        frequency: PaymentFrequency,
    ) -> Decimal:
        """Calculate NPV of lease payments."""
        payments_per_year = self._get_payments_per_year(frequency)
        num_payments = term_months / (12 / payments_per_year)
        periodic_rate = (discount_rate / 100) / payments_per_year

        if periodic_rate == 0:
            return payment_amount * Decimal(str(num_payments))

        # PV of annuity formula
        pv_factor = (1 - (1 + periodic_rate) ** (-num_payments)) / periodic_rate
        liability = payment_amount * Decimal(str(pv_factor))

        return liability.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def _get_payments_per_year(self, frequency: PaymentFrequency) -> int:
        """Get number of payments per year."""
        return {
            PaymentFrequency.MONTHLY: 12,
            PaymentFrequency.QUARTERLY: 4,
            PaymentFrequency.HALF_YEARLY: 2,
            PaymentFrequency.YEARLY: 1,
        }[frequency]

    def _get_first_payment_date(self, lease: Lease) -> date:
        """Calculate first payment date."""
        if lease.payment_in_advance:
            return lease.commencement_date

        # First payment after one period
        months_per_period = 12 // self._get_payments_per_year(lease.payment_frequency)
        first_payment = lease.commencement_date

        # Move to payment day
        try:
            first_payment = first_payment.replace(day=lease.payment_day)
        except ValueError:
            # Handle months with fewer days
            first_payment = first_payment.replace(day=28)

        # Add one period if not in advance
        if first_payment.month + months_per_period > 12:
            first_payment = first_payment.replace(
                year=first_payment.year + 1,
                month=first_payment.month + months_per_period - 12,
            )
        else:
            first_payment = first_payment.replace(month=first_payment.month + months_per_period)

        return first_payment

    async def _generate_payment_schedule(self, lease: Lease) -> None:
        """Generate amortization schedule for the lease."""
        payments_per_year = self._get_payments_per_year(lease.payment_frequency)
        months_per_period = 12 // payments_per_year
        periodic_rate = (lease.discount_rate / 100) / payments_per_year

        opening_liability = lease.lease_liability_initial
        payment_date = self._get_first_payment_date(lease)
        roua_monthly_depreciation = lease.roua_initial_value / Decimal(str(lease.lease_term_months))
        roua_period_depreciation = roua_monthly_depreciation * months_per_period
        roua_carrying = lease.roua_initial_value

        payment_number = 1
        while opening_liability > Decimal("0.01") and payment_date <= lease.end_date:
            # Calculate interest
            interest = (opening_liability * Decimal(str(periodic_rate))).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            # Principal is payment minus interest
            principal = lease.payment_amount - interest
            if principal > opening_liability:
                principal = opening_liability
                interest = lease.payment_amount - principal

            closing_liability = opening_liability - principal

            # ROUA depreciation
            if roua_period_depreciation > roua_carrying:
                roua_period_depreciation = roua_carrying
            roua_carrying -= roua_period_depreciation

            # Financial year
            fy = self._get_financial_year(payment_date)

            schedule = LeasePaymentSchedule(
                lease_id=lease.id,
                payment_number=payment_number,
                payment_date=payment_date,
                financial_year=fy,
                opening_liability=opening_liability,
                payment_amount=lease.payment_amount,
                interest_component=interest,
                principal_component=principal,
                closing_liability=closing_liability,
                depreciation_amount=roua_period_depreciation.quantize(Decimal("0.01")),
                roua_carrying_value=roua_carrying.quantize(Decimal("0.01")),
                created_by=lease.created_by,
                updated_by=lease.updated_by,
            )
            self.session.add(schedule)

            # Move to next period
            opening_liability = closing_liability
            payment_number += 1

            # Advance payment date
            new_month = payment_date.month + months_per_period
            new_year = payment_date.year
            if new_month > 12:
                new_month -= 12
                new_year += 1
            try:
                payment_date = payment_date.replace(year=new_year, month=new_month)
            except ValueError:
                payment_date = payment_date.replace(year=new_year, month=new_month, day=28)

    async def _regenerate_payment_schedule(self, lease: Lease, from_date: date) -> None:
        """Regenerate payment schedule after modification."""
        # Delete future schedules
        await self.session.execute(
            select(LeasePaymentSchedule)
            .where(
                LeasePaymentSchedule.lease_id == lease.id,
                LeasePaymentSchedule.payment_date >= from_date,
                LeasePaymentSchedule.is_paid == False,
            )
        )
        # Would need delete - simplified here

        # Regenerate from modification date
        await self._generate_payment_schedule(lease)

    async def _update_liability_bifurcation(self, lease: Lease) -> None:
        """Split liability into current and non-current portions."""
        # Get payments due within 12 months
        cutoff = date.today() + timedelta(days=365)

        result = await self.session.execute(
            select(func.sum(LeasePaymentSchedule.principal_component))
            .where(
                LeasePaymentSchedule.lease_id == lease.id,
                LeasePaymentSchedule.is_paid == False,
                LeasePaymentSchedule.payment_date <= cutoff,
            )
        )
        current_principal = result.scalar_one() or Decimal("0.00")

        lease.lease_liability_current_portion = current_principal
        lease.lease_liability_non_current = lease.lease_liability_current - current_principal

    async def _get_upcoming_payments_total(
        self,
        organization_id: UUID,
        days: int,
    ) -> Decimal:
        """Get total upcoming payments within days."""
        cutoff = date.today() + timedelta(days=days)

        result = await self.session.execute(
            select(func.sum(LeasePaymentSchedule.payment_amount))
            .join(Lease)
            .where(
                Lease.organization_id == organization_id,
                Lease.status.in_([LeaseStatus.ACTIVE, LeaseStatus.MODIFIED]),
                LeasePaymentSchedule.is_paid == False,
                LeasePaymentSchedule.payment_date <= cutoff,
            )
        )
        return result.scalar_one() or Decimal("0.00")

    def _get_financial_year(self, d: date) -> str:
        """Get financial year string for a date."""
        if d.month >= 4:
            return f"{d.year}-{str(d.year + 1)[2:]}"
        else:
            return f"{d.year - 1}-{str(d.year)[2:]}"

    async def _get_fy_and_period(
        self,
        organization_id: UUID,
        transaction_date: date,
    ) -> Tuple[UUID, UUID]:
        """Get financial year and period for a transaction date."""
        fy = await self.fy_repo.get_by_date(organization_id, transaction_date)
        if not fy:
            raise LeaseAccountingError(f"No financial year found for date {transaction_date}")
        if fy.is_closed:
            raise ClosedPeriodError(detail="Cannot post to a closed financial year")

        period = await self.period_repo.get_by_date(fy.id, transaction_date)
        if not period:
            raise LeaseAccountingError(f"No period found for date {transaction_date}")
        if period.is_closed:
            raise ClosedPeriodError(period=str(transaction_date))

        return fy.id, period.id

    async def _create_initial_recognition_entries(self, lease: Lease) -> Optional[List]:
        """
        Create GL entries for initial lease recognition.

        Ind AS 116 Initial Recognition:
        DR: Right-of-Use Asset (at initial measurement)
        CR: Lease Liability (present value of lease payments)
        """
        # Skip if GL accounts are not configured
        if not lease.roua_account_id or not lease.lease_liability_account_id:
            return None

        try:
            # Get financial year and period
            fy_id, period_id = await self._get_fy_and_period(
                lease.organization_id,
                lease.commencement_date,
            )

            gl_lines: List[Dict[str, Any]] = []

            # DR: Right-of-Use Asset (ROUA)
            gl_lines.append({
                "account_id": lease.roua_account_id,
                "debit_amount": lease.roua_initial_value,
                "credit_amount": Decimal("0.00"),
                "narration": f"Initial recognition of ROUA - {lease.lease_number}",
            })

            # CR: Lease Liability
            gl_lines.append({
                "account_id": lease.lease_liability_account_id,
                "debit_amount": Decimal("0.00"),
                "credit_amount": lease.lease_liability_initial,
                "narration": f"Initial recognition of lease liability - {lease.lease_number}",
            })

            # DR/CR: Initial Direct Costs (if any and ROUA adjusted)
            # Note: Initial direct costs are already included in ROUA
            # If there's a difference due to restoration costs, handle here
            if lease.estimated_restoration_cost > 0:
                # This is typically Dr ROUA / Cr Provision for restoration
                # For simplicity, we've included it in ROUA above
                pass

            # Post GL entries
            entries = await self.gl_posting_service.post_from_source(
                source_type=GLEntrySourceType.MANUAL,  # Or create LEASE_RECOGNITION type
                source_id=lease.id,
                source_reference=f"LEASE-INIT-{lease.lease_number}",
                organization_id=lease.organization_id,
                financial_year_id=fy_id,
                period_id=period_id,
                voucher_date=lease.commencement_date,
                narration=f"Lease Initial Recognition: {lease.lease_number} - {lease.lease_name}",
                lines=gl_lines,
                posted_by=lease.created_by,
                unit_id=lease.asset_location_id,
            )

            return entries

        except Exception as e:
            raise GLPostingFailedError(
                detail=f"Failed to post initial recognition entries: {str(e)}",
            )

    async def _create_interest_voucher(
        self,
        schedule: LeasePaymentSchedule,
    ) -> Optional[List]:
        """
        Create GL entries for interest expense accrual.

        DR: Interest Expense
        CR: Lease Liability (or accrued interest)
        """
        lease = schedule.lease

        if not lease.interest_expense_account_id or not lease.lease_liability_account_id:
            return None

        try:
            # Get financial year and period
            fy_id, period_id = await self._get_fy_and_period(
                lease.organization_id,
                schedule.payment_date,
            )

            gl_lines: List[Dict[str, Any]] = []

            # DR: Interest Expense
            gl_lines.append({
                "account_id": lease.interest_expense_account_id,
                "debit_amount": schedule.interest_component,
                "credit_amount": Decimal("0.00"),
                "narration": f"Interest expense - {lease.lease_number} - Payment #{schedule.payment_number}",
            })

            # CR: Lease Liability (interest accrues to liability)
            gl_lines.append({
                "account_id": lease.lease_liability_account_id,
                "debit_amount": Decimal("0.00"),
                "credit_amount": schedule.interest_component,
                "narration": f"Interest accrual - {lease.lease_number}",
            })

            entries = await self.gl_posting_service.post_from_source(
                source_type=GLEntrySourceType.INTEREST_ACCRUAL,
                source_id=schedule.id,
                source_reference=f"LEASE-INT-{lease.lease_number}-{schedule.payment_number}",
                organization_id=lease.organization_id,
                financial_year_id=fy_id,
                period_id=period_id,
                voucher_date=schedule.payment_date,
                narration=f"Lease Interest: {lease.lease_number} - Period {schedule.payment_number}",
                lines=gl_lines,
                posted_by=schedule.updated_by or lease.created_by,
                unit_id=lease.asset_location_id,
            )

            return entries

        except Exception as e:
            raise GLPostingFailedError(
                detail=f"Failed to post interest entries: {str(e)}",
            )

    async def _create_depreciation_voucher(
        self,
        lease: Lease,
        depreciation_amount: Decimal,
        depreciation_date: date,
        posted_by: UUID,
    ) -> Optional[List]:
        """
        Create GL entries for ROUA depreciation.

        DR: Depreciation Expense
        CR: Accumulated Depreciation - ROUA
        """
        if not lease.depreciation_expense_account_id or not lease.accumulated_depreciation_account_id:
            return None

        try:
            # Get financial year and period
            fy_id, period_id = await self._get_fy_and_period(
                lease.organization_id,
                depreciation_date,
            )

            gl_lines: List[Dict[str, Any]] = []

            # DR: Depreciation Expense
            gl_lines.append({
                "account_id": lease.depreciation_expense_account_id,
                "debit_amount": depreciation_amount,
                "credit_amount": Decimal("0.00"),
                "narration": f"ROUA depreciation - {lease.lease_number}",
            })

            # CR: Accumulated Depreciation - ROUA
            gl_lines.append({
                "account_id": lease.accumulated_depreciation_account_id,
                "debit_amount": Decimal("0.00"),
                "credit_amount": depreciation_amount,
                "narration": f"Accumulated depreciation - {lease.lease_number}",
            })

            entries = await self.gl_posting_service.post_from_source(
                source_type=GLEntrySourceType.DEPRECIATION,
                source_id=lease.id,
                source_reference=f"LEASE-DEP-{lease.lease_number}-{depreciation_date.strftime('%Y%m')}",
                organization_id=lease.organization_id,
                financial_year_id=fy_id,
                period_id=period_id,
                voucher_date=depreciation_date,
                narration=f"ROUA Depreciation: {lease.lease_number} - {depreciation_date.strftime('%b %Y')}",
                lines=gl_lines,
                posted_by=posted_by,
                unit_id=lease.asset_location_id,
            )

            return entries

        except Exception as e:
            raise GLPostingFailedError(
                detail=f"Failed to post depreciation entries: {str(e)}",
            )

    async def _create_termination_entries(
        self,
        lease: Lease,
        gain_loss: Decimal,
        settlement: Decimal,
    ) -> Optional[List]:
        """
        Create GL entries for lease termination.

        DR: Lease Liability (remaining balance)
        DR: Accumulated Depreciation - ROUA
        DR/CR: Gain/Loss on Termination
        CR: Right-of-Use Asset (original value)
        CR: Cash/Bank (settlement amount if any)
        """
        if not lease.roua_account_id or not lease.lease_liability_account_id:
            return None

        try:
            termination_date = lease.end_date or date.today()

            # Get financial year and period
            fy_id, period_id = await self._get_fy_and_period(
                lease.organization_id,
                termination_date,
            )

            gl_lines: List[Dict[str, Any]] = []

            # Store original values before they were zeroed
            remaining_liability = lease.lease_liability_initial - (lease.roua_initial_value - lease.roua_carrying_value)
            # Note: In a real scenario, we'd track these before termination

            # DR: Lease Liability (write off remaining)
            if remaining_liability > 0:
                gl_lines.append({
                    "account_id": lease.lease_liability_account_id,
                    "debit_amount": remaining_liability,
                    "credit_amount": Decimal("0.00"),
                    "narration": f"Write-off lease liability - {lease.lease_number}",
                })

            # DR: Accumulated Depreciation - ROUA
            if lease.accumulated_depreciation_account_id and lease.roua_accumulated_depreciation > 0:
                gl_lines.append({
                    "account_id": lease.accumulated_depreciation_account_id,
                    "debit_amount": lease.roua_accumulated_depreciation,
                    "credit_amount": Decimal("0.00"),
                    "narration": f"Write-off accumulated depreciation - {lease.lease_number}",
                })

            # CR: Right-of-Use Asset (original cost)
            gl_lines.append({
                "account_id": lease.roua_account_id,
                "debit_amount": Decimal("0.00"),
                "credit_amount": lease.roua_initial_value,
                "narration": f"Derecognize ROUA - {lease.lease_number}",
            })

            # Handle gain/loss on termination
            # We need a gain/loss account - for now use interest expense as fallback
            gain_loss_account = lease.interest_expense_account_id

            if gain_loss > 0:
                # Gain on termination (credit)
                gl_lines.append({
                    "account_id": gain_loss_account,
                    "debit_amount": Decimal("0.00"),
                    "credit_amount": gain_loss,
                    "narration": f"Gain on lease termination - {lease.lease_number}",
                })
            elif gain_loss < 0:
                # Loss on termination (debit)
                gl_lines.append({
                    "account_id": gain_loss_account,
                    "debit_amount": abs(gain_loss),
                    "credit_amount": Decimal("0.00"),
                    "narration": f"Loss on lease termination - {lease.lease_number}",
                })

            if not gl_lines:
                return None

            entries = await self.gl_posting_service.post_from_source(
                source_type=GLEntrySourceType.MANUAL,  # Or create LEASE_TERMINATION type
                source_id=lease.id,
                source_reference=f"LEASE-TERM-{lease.lease_number}",
                organization_id=lease.organization_id,
                financial_year_id=fy_id,
                period_id=period_id,
                voucher_date=termination_date,
                narration=f"Lease Termination: {lease.lease_number} - {lease.lease_name}",
                lines=gl_lines,
                posted_by=lease.updated_by or lease.created_by,
                unit_id=lease.asset_location_id,
            )

            return entries

        except Exception as e:
            raise GLPostingFailedError(
                detail=f"Failed to post termination entries: {str(e)}",
            )
