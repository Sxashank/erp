"""
Fixed Deposit Service
"""

from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Tuple
from uuid import UUID
import math

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.fixed_deposits.fd_product import (
    FDProduct,
    FDInterestPayoutFrequency,
    FDCompoundingFrequency,
)
from app.models.fixed_deposits.fixed_deposit import (
    FixedDeposit,
    FDInterestAccrual,
    FDTransaction,
    FDNominee,
    FDStatus,
    FDTransactionType,
)
from app.schemas.fixed_deposits.fixed_deposit import (
    FixedDepositCreate,
    FixedDepositUpdate,
    FixedDepositResponse,
    FixedDepositListResponse,
    FixedDepositSummary,
    FDMaturityProjection,
    FDClosureRequest,
    FDRenewalRequest,
    FDNomineeCreate,
)
from app.services.fixed_deposits.fd_product_service import FDProductService


class FixedDepositService:
    """Service for Fixed Deposit operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.product_service = FDProductService(db)

    async def _generate_fd_number(self, organization_id: UUID) -> str:
        """Generate unique FD number."""
        year = date.today().year
        prefix = f"FD/{year}/"

        # Get last FD number for this year
        result = await self.db.execute(
            select(FixedDeposit.fd_number)
            .where(
                FixedDeposit.organization_id == organization_id,
                FixedDeposit.fd_number.like(f"{prefix}%"),
            )
            .order_by(FixedDeposit.fd_number.desc())
            .limit(1)
        )
        last_number = result.scalar_one_or_none()

        if last_number:
            sequence = int(last_number.split("/")[-1]) + 1
        else:
            sequence = 1

        return f"{prefix}{sequence:06d}"

    def _calculate_maturity_amount(
        self,
        principal: Decimal,
        rate: Decimal,
        tenure_days: int,
        compounding_frequency: FDCompoundingFrequency,
    ) -> Decimal:
        """Calculate maturity amount based on compounding."""
        rate_decimal = rate / Decimal("100")
        years = Decimal(str(tenure_days)) / Decimal("365")

        if compounding_frequency == FDCompoundingFrequency.SIMPLE:
            # Simple interest
            interest = principal * rate_decimal * years
            return (principal + interest).quantize(Decimal("0.01"), ROUND_HALF_UP)

        # Compound interest
        # A = P(1 + r/n)^(nt)
        n = {
            FDCompoundingFrequency.MONTHLY: 12,
            FDCompoundingFrequency.QUARTERLY: 4,
            FDCompoundingFrequency.HALF_YEARLY: 2,
            FDCompoundingFrequency.ANNUALLY: 1,
        }.get(compounding_frequency, 4)

        # Convert to float for calculation, then back to Decimal
        p = float(principal)
        r = float(rate_decimal)
        t = float(years)

        maturity = p * math.pow(1 + r / n, n * t)
        return Decimal(str(maturity)).quantize(Decimal("0.01"), ROUND_HALF_UP)

    async def create_fd(self, data: FixedDepositCreate) -> FixedDeposit:
        """Create a new Fixed Deposit."""
        # Get product
        product = await self.product_service.get_product(data.product_id)
        if not product:
            raise ValueError("FD Product not found")

        # Validate tenure
        if data.tenure_days < product.min_tenure_days:
            raise ValueError(f"Minimum tenure is {product.min_tenure_days} days")
        if data.tenure_days > product.max_tenure_days:
            raise ValueError(f"Maximum tenure is {product.max_tenure_days} days")

        # Validate amount
        if data.deposit_amount < product.min_amount:
            raise ValueError(f"Minimum deposit amount is {product.min_amount}")
        if product.max_amount and data.deposit_amount > product.max_amount:
            raise ValueError(f"Maximum deposit amount is {product.max_amount}")

        # Get applicable interest rate
        interest_rate = await self.product_service.get_applicable_rate(
            product_id=data.product_id,
            tenure_days=data.tenure_days,
            amount=data.deposit_amount,
            customer_category=data.customer_category,
        )
        if interest_rate is None:
            raise ValueError("No applicable interest rate found for given parameters")

        # Calculate dates
        value_date = data.value_date or data.deposit_date
        maturity_date = value_date + timedelta(days=data.tenure_days)

        # Get frequencies from product or use provided
        interest_payout_frequency = (
            data.interest_payout_frequency or product.interest_payout_frequency
        )
        compounding_frequency = (
            data.compounding_frequency or product.compounding_frequency
        )

        # Calculate maturity amount
        maturity_amount = self._calculate_maturity_amount(
            principal=data.deposit_amount,
            rate=interest_rate,
            tenure_days=data.tenure_days,
            compounding_frequency=compounding_frequency,
        )

        # Generate FD number
        fd_number = await self._generate_fd_number(data.organization_id)

        # Create FD
        fd = FixedDeposit(
            organization_id=data.organization_id,
            fd_number=fd_number,
            product_id=data.product_id,
            customer_id=data.customer_id,
            customer_category=data.customer_category,
            deposit_amount=data.deposit_amount,
            deposit_date=data.deposit_date,
            value_date=value_date,
            tenure_days=data.tenure_days,
            maturity_date=maturity_date,
            interest_rate=interest_rate,
            interest_payout_frequency=interest_payout_frequency,
            compounding_frequency=compounding_frequency,
            maturity_amount=maturity_amount,
            interest_payout_mode=data.interest_payout_mode,
            payout_bank_account_id=data.payout_bank_account_id,
            auto_renew=data.auto_renew,
            renewal_tenure_days=data.renewal_tenure_days,
            branch_id=data.branch_id,
            remarks=data.remarks,
            status=FDStatus.DRAFT,
        )
        self.db.add(fd)
        await self.db.flush()

        # Create nominees
        if data.nominees:
            for nominee_data in data.nominees:
                nominee = FDNominee(
                    fixed_deposit_id=fd.id,
                    **nominee_data.model_dump(),
                )
                self.db.add(nominee)

        # Create initial deposit transaction
        transaction = FDTransaction(
            fixed_deposit_id=fd.id,
            transaction_date=data.deposit_date,
            transaction_type=FDTransactionType.DEPOSIT,
            description=f"Initial deposit for FD {fd_number}",
            credit_amount=data.deposit_amount,
            balance=data.deposit_amount,
        )
        self.db.add(transaction)

        await self.db.commit()
        await self.db.refresh(fd)

        return await self.get_fd(fd.id)

    async def get_fd(self, fd_id: UUID) -> Optional[FixedDeposit]:
        """Get FD by ID with all relationships."""
        result = await self.db.execute(
            select(FixedDeposit)
            .options(
                selectinload(FixedDeposit.product),
                selectinload(FixedDeposit.nominees),
                selectinload(FixedDeposit.transactions),
                selectinload(FixedDeposit.interest_accruals),
            )
            .where(FixedDeposit.id == fd_id)
        )
        return result.scalar_one_or_none()

    async def update_fd(
        self, fd_id: UUID, data: FixedDepositUpdate
    ) -> Optional[FixedDeposit]:
        """Update FD details (limited fields)."""
        fd = await self.get_fd(fd_id)
        if not fd:
            return None

        if fd.status not in [FDStatus.DRAFT, FDStatus.ACTIVE]:
            raise ValueError("Cannot update FD in current status")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(fd, field, value)

        await self.db.commit()
        await self.db.refresh(fd)
        return fd

    async def approve_fd(
        self, fd_id: UUID, user_id: UUID
    ) -> Optional[FixedDeposit]:
        """Approve and activate an FD."""
        fd = await self.get_fd(fd_id)
        if not fd:
            return None

        if fd.status != FDStatus.DRAFT:
            raise ValueError("Only draft FDs can be approved")

        fd.status = FDStatus.ACTIVE
        fd.approved_by_user_id = user_id
        fd.approved_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(fd)
        return fd

    async def list_fds(
        self,
        organization_id: UUID,
        customer_id: Optional[UUID] = None,
        product_id: Optional[UUID] = None,
        status: Optional[FDStatus] = None,
        maturing_before: Optional[date] = None,
        maturing_after: Optional[date] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> FixedDepositListResponse:
        """List FDs with filtering."""
        query = select(FixedDeposit).where(
            FixedDeposit.organization_id == organization_id
        )

        if customer_id:
            query = query.where(FixedDeposit.customer_id == customer_id)
        if product_id:
            query = query.where(FixedDeposit.product_id == product_id)
        if status:
            query = query.where(FixedDeposit.status == status)
        if maturing_before:
            query = query.where(FixedDeposit.maturity_date <= maturing_before)
        if maturing_after:
            query = query.where(FixedDeposit.maturity_date >= maturing_after)

        # Get total count
        count_query = select(func.count(FixedDeposit.id)).where(
            FixedDeposit.organization_id == organization_id
        )
        if customer_id:
            count_query = count_query.where(FixedDeposit.customer_id == customer_id)
        if status:
            count_query = count_query.where(FixedDeposit.status == status)

        count_result = await self.db.execute(count_query)
        total = count_result.scalar()

        # Get paginated results
        result = await self.db.execute(
            query
            .options(
                selectinload(FixedDeposit.product),
                selectinload(FixedDeposit.nominees),
            )
            .order_by(FixedDeposit.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        fds = result.scalars().all()

        # Build response with product details
        items = []
        for fd in fds:
            response = FixedDepositResponse.model_validate(fd)
            if fd.product:
                response.product_code = fd.product.product_code
                response.product_name = fd.product.product_name
            items.append(response)

        return FixedDepositListResponse(items=items, total=total)

    async def get_summary(
        self, organization_id: UUID
    ) -> FixedDepositSummary:
        """Get FD summary statistics."""
        today = date.today()
        month_end = date(today.year, today.month + 1, 1) - timedelta(days=1) if today.month < 12 else date(today.year, 12, 31)
        next_month_end = date(today.year, today.month + 2, 1) - timedelta(days=1) if today.month < 11 else date(today.year + 1, (today.month + 2) % 12 or 12, 1) - timedelta(days=1)

        # Total FDs
        total_result = await self.db.execute(
            select(func.count(FixedDeposit.id))
            .where(FixedDeposit.organization_id == organization_id)
        )
        total_fds = total_result.scalar() or 0

        # Active FDs
        active_result = await self.db.execute(
            select(
                func.count(FixedDeposit.id),
                func.sum(FixedDeposit.deposit_amount),
                func.sum(FixedDeposit.maturity_amount),
            )
            .where(
                FixedDeposit.organization_id == organization_id,
                FixedDeposit.status == FDStatus.ACTIVE,
            )
        )
        active_row = active_result.one()
        active_fds = active_row[0] or 0
        total_deposit = active_row[1] or Decimal("0")
        total_maturity = active_row[2] or Decimal("0")

        # Maturing this month
        maturing_this_month_result = await self.db.execute(
            select(func.count(FixedDeposit.id))
            .where(
                FixedDeposit.organization_id == organization_id,
                FixedDeposit.status == FDStatus.ACTIVE,
                FixedDeposit.maturity_date >= today,
                FixedDeposit.maturity_date <= month_end,
            )
        )
        maturing_this_month = maturing_this_month_result.scalar() or 0

        # Maturing next month
        maturing_next_month_result = await self.db.execute(
            select(func.count(FixedDeposit.id))
            .where(
                FixedDeposit.organization_id == organization_id,
                FixedDeposit.status == FDStatus.ACTIVE,
                FixedDeposit.maturity_date > month_end,
                FixedDeposit.maturity_date <= next_month_end,
            )
        )
        maturing_next_month = maturing_next_month_result.scalar() or 0

        # By status
        status_result = await self.db.execute(
            select(FixedDeposit.status, func.count(FixedDeposit.id))
            .where(FixedDeposit.organization_id == organization_id)
            .group_by(FixedDeposit.status)
        )
        by_status = {row[0].value: row[1] for row in status_result.all()}

        # By customer category
        category_result = await self.db.execute(
            select(FixedDeposit.customer_category, func.count(FixedDeposit.id))
            .where(
                FixedDeposit.organization_id == organization_id,
                FixedDeposit.status == FDStatus.ACTIVE,
            )
            .group_by(FixedDeposit.customer_category)
        )
        by_category = {row[0].value: row[1] for row in category_result.all()}

        return FixedDepositSummary(
            total_fds=total_fds,
            active_fds=active_fds,
            total_deposit_amount=total_deposit,
            total_maturity_amount=total_maturity,
            maturing_this_month=maturing_this_month,
            maturing_next_month=maturing_next_month,
            by_status=by_status,
            by_customer_category=by_category,
        )

    async def close_fd(
        self, fd_id: UUID, request: FDClosureRequest
    ) -> FixedDeposit:
        """Close an FD (maturity or premature)."""
        fd = await self.get_fd(fd_id)
        if not fd:
            raise ValueError("FD not found")

        if fd.status != FDStatus.ACTIVE:
            raise ValueError("Only active FDs can be closed")

        product = fd.product
        is_premature = request.closure_date < fd.maturity_date

        # Calculate closure amount
        if is_premature:
            # Apply premature penalty
            effective_rate = fd.interest_rate - (product.premature_penalty_rate or Decimal("0"))
            effective_rate = max(effective_rate, Decimal("0"))

            # Calculate days held
            days_held = (request.closure_date - fd.value_date).days

            # Recalculate interest with penalty
            closure_interest = (
                fd.deposit_amount * effective_rate / Decimal("100") *
                Decimal(str(days_held)) / Decimal("365")
            ).quantize(Decimal("0.01"), ROUND_HALF_UP)

            closure_amount = fd.deposit_amount + closure_interest - fd.tds_deducted
            fd.status = FDStatus.PREMATURE_CLOSED
        else:
            # Maturity closure
            closure_amount = fd.maturity_amount - fd.paid_interest - fd.tds_deducted
            fd.status = FDStatus.MATURED

        # Create closure transaction
        transaction = FDTransaction(
            fixed_deposit_id=fd.id,
            transaction_date=request.closure_date,
            transaction_type=(
                FDTransactionType.PREMATURE_PAYOUT
                if is_premature
                else FDTransactionType.MATURITY_PAYOUT
            ),
            description=f"{'Premature' if is_premature else 'Maturity'} closure of FD {fd.fd_number}",
            debit_amount=closure_amount,
            balance=Decimal("0"),
            payment_mode=request.payout_mode,
            remarks=request.remarks,
        )
        self.db.add(transaction)

        fd.closed_date = request.closure_date
        fd.closure_amount = closure_amount
        fd.closure_remarks = request.remarks

        await self.db.commit()
        await self.db.refresh(fd)
        return fd

    async def renew_fd(
        self, fd_id: UUID, request: FDRenewalRequest
    ) -> FixedDeposit:
        """Renew an FD at maturity."""
        fd = await self.get_fd(fd_id)
        if not fd:
            raise ValueError("FD not found")

        if fd.status != FDStatus.ACTIVE:
            raise ValueError("Only active FDs can be renewed")

        # Calculate new principal
        maturity_interest = fd.maturity_amount - fd.deposit_amount
        new_principal = fd.deposit_amount

        if request.include_interest:
            new_principal += maturity_interest - fd.tds_deducted

        if request.partial_withdrawal:
            new_principal -= request.partial_withdrawal
            if new_principal <= 0:
                raise ValueError("Withdrawal amount exceeds available balance")

        # Get new product and tenure
        new_product_id = request.new_product_id or fd.product_id
        new_tenure = request.new_tenure_days or fd.renewal_tenure_days or fd.tenure_days

        # Create new FD
        new_fd_data = FixedDepositCreate(
            organization_id=fd.organization_id,
            product_id=new_product_id,
            customer_id=fd.customer_id,
            customer_category=fd.customer_category,
            deposit_amount=new_principal,
            deposit_date=fd.maturity_date,
            value_date=fd.maturity_date,
            tenure_days=new_tenure,
            interest_payout_mode=fd.interest_payout_mode,
            payout_bank_account_id=fd.payout_bank_account_id,
            auto_renew=fd.auto_renew,
            renewal_tenure_days=fd.renewal_tenure_days,
            branch_id=fd.branch_id,
            remarks=f"Renewed from FD {fd.fd_number}",
        )

        new_fd = await self.create_fd(new_fd_data)
        new_fd.parent_fd_id = fd.id
        new_fd.renewal_count = fd.renewal_count + 1

        # Mark old FD as renewed
        fd.status = FDStatus.RENEWED

        # Create renewal transaction on old FD
        transaction = FDTransaction(
            fixed_deposit_id=fd.id,
            transaction_date=fd.maturity_date,
            transaction_type=FDTransactionType.RENEWAL,
            description=f"Renewed to FD {new_fd.fd_number}",
            debit_amount=fd.deposit_amount,
            balance=Decimal("0"),
            remarks=request.remarks,
        )
        self.db.add(transaction)

        await self.db.commit()
        return new_fd

    async def add_nominee(
        self, fd_id: UUID, data: FDNomineeCreate
    ) -> FDNominee:
        """Add nominee to FD."""
        nominee = FDNominee(
            fixed_deposit_id=fd_id,
            **data.model_dump(),
        )
        self.db.add(nominee)
        await self.db.commit()
        await self.db.refresh(nominee)
        return nominee

    async def remove_nominee(self, nominee_id: UUID) -> bool:
        """Remove nominee from FD."""
        result = await self.db.execute(
            select(FDNominee).where(FDNominee.id == nominee_id)
        )
        nominee = result.scalar_one_or_none()
        if not nominee:
            return False

        await self.db.delete(nominee)
        await self.db.commit()
        return True


class FDInterestService:
    """Service for FD interest calculations and accruals."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_daily_interest(
        self,
        principal: Decimal,
        rate: Decimal,
        days: int = 1,
    ) -> Decimal:
        """Calculate interest for given days."""
        return (
            principal * rate / Decimal("100") * Decimal(str(days)) / Decimal("365")
        ).quantize(Decimal("0.01"), ROUND_HALF_UP)

    async def run_interest_accrual(
        self,
        organization_id: UUID,
        accrual_date: date,
    ) -> dict:
        """Run daily interest accrual for all active FDs."""
        # Get all active FDs
        result = await self.db.execute(
            select(FixedDeposit)
            .where(
                FixedDeposit.organization_id == organization_id,
                FixedDeposit.status == FDStatus.ACTIVE,
                FixedDeposit.value_date <= accrual_date,
                FixedDeposit.maturity_date >= accrual_date,
            )
        )
        fds = result.scalars().all()

        processed = 0
        total_interest = Decimal("0")

        for fd in fds:
            # Check if already accrued for this date
            existing = await self.db.execute(
                select(FDInterestAccrual)
                .where(
                    FDInterestAccrual.fixed_deposit_id == fd.id,
                    FDInterestAccrual.accrual_date == accrual_date,
                )
            )
            if existing.scalar_one_or_none():
                continue

            # Get last accrual to determine period
            last_accrual_result = await self.db.execute(
                select(FDInterestAccrual)
                .where(FDInterestAccrual.fixed_deposit_id == fd.id)
                .order_by(FDInterestAccrual.accrual_date.desc())
                .limit(1)
            )
            last_accrual = last_accrual_result.scalar_one_or_none()

            period_from = (
                last_accrual.period_to + timedelta(days=1)
                if last_accrual
                else fd.value_date
            )
            period_to = accrual_date
            days = (period_to - period_from).days + 1

            # Calculate interest
            interest_amount = await self.calculate_daily_interest(
                principal=fd.deposit_amount,
                rate=fd.interest_rate,
                days=days,
            )

            cumulative = (
                (last_accrual.cumulative_interest + interest_amount)
                if last_accrual
                else interest_amount
            )

            # Create accrual record
            accrual = FDInterestAccrual(
                fixed_deposit_id=fd.id,
                accrual_date=accrual_date,
                period_from=period_from,
                period_to=period_to,
                days=days,
                principal_amount=fd.deposit_amount,
                interest_rate=fd.interest_rate,
                interest_amount=interest_amount,
                cumulative_interest=cumulative,
            )
            self.db.add(accrual)

            # Update FD
            fd.accrued_interest = cumulative
            fd.last_interest_calc_date = accrual_date

            processed += 1
            total_interest += interest_amount

        await self.db.commit()

        return {
            "processed": processed,
            "total_interest": total_interest,
            "accrual_date": accrual_date.isoformat(),
        }

    async def process_interest_payout(
        self,
        organization_id: UUID,
        payout_date: date,
    ) -> dict:
        """Process interest payout for eligible FDs."""
        # Get FDs due for interest payout
        result = await self.db.execute(
            select(FixedDeposit)
            .where(
                FixedDeposit.organization_id == organization_id,
                FixedDeposit.status == FDStatus.ACTIVE,
                FixedDeposit.interest_payout_frequency != FDInterestPayoutFrequency.ON_MATURITY,
            )
        )
        fds = result.scalars().all()

        processed = 0
        total_payout = Decimal("0")

        for fd in fds:
            # Check if payout is due based on frequency
            last_payout = fd.last_interest_payout_date or fd.value_date

            frequency_days = {
                FDInterestPayoutFrequency.MONTHLY: 30,
                FDInterestPayoutFrequency.QUARTERLY: 90,
                FDInterestPayoutFrequency.HALF_YEARLY: 180,
                FDInterestPayoutFrequency.ANNUALLY: 365,
            }.get(fd.interest_payout_frequency, 90)

            next_payout_date = last_payout + timedelta(days=frequency_days)

            if payout_date < next_payout_date:
                continue

            # Calculate unpaid interest
            unpaid_interest = fd.accrued_interest - fd.paid_interest
            if unpaid_interest <= 0:
                continue

            # Create payout transaction
            transaction = FDTransaction(
                fixed_deposit_id=fd.id,
                transaction_date=payout_date,
                transaction_type=FDTransactionType.INTEREST_PAYOUT,
                description=f"Interest payout for period ending {payout_date}",
                debit_amount=unpaid_interest,
                balance=fd.deposit_amount,
                payment_mode=fd.interest_payout_mode,
            )
            self.db.add(transaction)

            # Update FD
            fd.paid_interest += unpaid_interest
            fd.last_interest_payout_date = payout_date

            # Mark accruals as paid
            await self.db.execute(
                select(FDInterestAccrual)
                .where(
                    FDInterestAccrual.fixed_deposit_id == fd.id,
                    FDInterestAccrual.is_paid == False,
                )
            )

            processed += 1
            total_payout += unpaid_interest

        await self.db.commit()

        return {
            "processed": processed,
            "total_payout": total_payout,
            "payout_date": payout_date.isoformat(),
        }

    async def get_maturity_projection(
        self, fd_id: UUID
    ) -> FDMaturityProjection:
        """Get maturity projection for an FD."""
        result = await self.db.execute(
            select(FixedDeposit)
            .options(selectinload(FixedDeposit.product))
            .where(FixedDeposit.id == fd_id)
        )
        fd = result.scalar_one_or_none()

        if not fd:
            raise ValueError("FD not found")

        # Calculate projected interest
        projected_interest = fd.maturity_amount - fd.deposit_amount

        # Estimate TDS (if applicable and threshold exceeded)
        tds_estimate = Decimal("0")
        if fd.product.tds_applicable and projected_interest > fd.product.tds_threshold:
            tds_estimate = (projected_interest * Decimal("0.10")).quantize(
                Decimal("0.01"), ROUND_HALF_UP
            )

        net_maturity = fd.maturity_amount - tds_estimate

        # Generate period-wise schedule
        schedule = []
        current_date = fd.value_date
        current_principal = fd.deposit_amount

        frequency_days = {
            FDInterestPayoutFrequency.MONTHLY: 30,
            FDInterestPayoutFrequency.QUARTERLY: 90,
            FDInterestPayoutFrequency.HALF_YEARLY: 180,
            FDInterestPayoutFrequency.ANNUALLY: 365,
            FDInterestPayoutFrequency.ON_MATURITY: fd.tenure_days,
        }.get(fd.interest_payout_frequency, 90)

        while current_date < fd.maturity_date:
            period_end = min(
                current_date + timedelta(days=frequency_days),
                fd.maturity_date,
            )
            days = (period_end - current_date).days

            period_interest = await self.calculate_daily_interest(
                principal=current_principal,
                rate=fd.interest_rate,
                days=days,
            )

            schedule.append({
                "period_from": current_date.isoformat(),
                "period_to": period_end.isoformat(),
                "days": days,
                "principal": float(current_principal),
                "interest": float(period_interest),
            })

            # If compounding, add interest to principal
            if fd.interest_payout_frequency == FDInterestPayoutFrequency.ON_MATURITY:
                if fd.compounding_frequency != FDCompoundingFrequency.SIMPLE:
                    current_principal += period_interest

            current_date = period_end + timedelta(days=1)

        return FDMaturityProjection(
            fd_id=fd.id,
            fd_number=fd.fd_number,
            deposit_amount=fd.deposit_amount,
            interest_rate=fd.interest_rate,
            tenure_days=fd.tenure_days,
            maturity_date=fd.maturity_date,
            projected_interest=projected_interest,
            projected_maturity_amount=fd.maturity_amount,
            tds_estimate=tds_estimate,
            net_maturity_amount=net_maturity,
            schedule=schedule,
        )
