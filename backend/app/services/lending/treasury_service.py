"""Treasury and ALM services for the lending module."""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.lending.enums import InterestType, LoanAccountStatus
from app.models.lending.loan_account import LoanAccount
from app.models.lending.treasury import (
    ALMLiability,
    ALMPosition,
    Borrowing,
    BorrowingCovenant,
    BorrowingPayment,
    BorrowingSchedule,
    BorrowingTranche,
    ExposureLimit,
    IRSAnalysis,
    Lender,
)
from app.repositories.lending.treasury_repo import (
    ALMAssetRepository,
    ALMLiabilityRepository,
    ALMPositionRepository,
    BorrowingCovenantRepository,
    BorrowingPaymentRepository,
    BorrowingRepository,
    BorrowingScheduleRepository,
    BorrowingTrancheRepository,
    ExposureLimitRepository,
    ExposureTrackingRepository,
    IRSAnalysisRepository,
    LenderRepository,
)
from app.schemas.lending.treasury import (
    ALMGapAnalysis,
    ALMPositionGenerate,
    ALMSummary,
    BorrowingCovenantCreate,
    BorrowingCovenantUpdate,
    BorrowingCreate,
    BorrowingPaymentCreate,
    BorrowingSummary,
    BorrowingTrancheCreate,
    BorrowingTrancheDisbursement,
    BorrowingUpdate,
    ExposureLimitCreate,
    ExposureLimitUpdate,
    ExposureSummary,
    IRSAnalysisGenerate,
    IRSPreviewResponse,
    IRSPreviewSummary,
    IRSShockBucket,
    LenderCreate,
    LenderUpdate,
    TreasurySummary,
)


class TreasuryService:
    """Service for treasury and ALM operations."""

    # ALM bucket day ranges (as per RBI)
    ALM_BUCKETS = {
        "DAY_1": (1, 1),
        "DAYS_2_7": (2, 7),
        "DAYS_8_14": (8, 14),
        "DAYS_15_28": (15, 28),
        "DAYS_29_3M": (29, 90),
        "MONTHS_3_6": (91, 180),
        "MONTHS_6_12": (181, 365),
        "YEARS_1_3": (366, 1095),
        "YEARS_3_5": (1096, 1825),
        "OVER_5_YEARS": (1826, 99999),
    }

    def __init__(self, session: AsyncSession):
        self.session = session
        self.lender_repo = LenderRepository(session)
        self.borrowing_repo = BorrowingRepository(session)
        self.tranche_repo = BorrowingTrancheRepository(session)
        self.schedule_repo = BorrowingScheduleRepository(session)
        self.payment_repo = BorrowingPaymentRepository(session)
        self.covenant_repo = BorrowingCovenantRepository(session)
        self.alm_position_repo = ALMPositionRepository(session)
        self.alm_asset_repo = ALMAssetRepository(session)
        self.alm_liability_repo = ALMLiabilityRepository(session)
        self.irs_repo = IRSAnalysisRepository(session)
        self.exposure_limit_repo = ExposureLimitRepository(session)
        self.exposure_tracking_repo = ExposureTrackingRepository(session)

    # =========================================================================
    # Lender Operations
    # =========================================================================

    async def create_lender(
        self,
        organization_id: UUID,
        data: LenderCreate,
        created_by: UUID | None = None,
    ) -> Lender:
        """Create a new lender."""
        lender_code = await self.lender_repo.generate_lender_code(organization_id)

        lender = Lender(
            organization_id=organization_id,
            lender_code=lender_code,
            status="ACTIVE",
            available_limit=data.total_sanction_limit,
            created_by=created_by,
            **data.model_dump(exclude_unset=True),
        )

        self.session.add(lender)
        await self.session.flush()
        return lender

    async def update_lender(
        self,
        lender_id: UUID,
        data: LenderUpdate,
        updated_by: UUID | None = None,
    ) -> Lender:
        """Update a lender."""
        lender = await self.lender_repo.get(lender_id)
        if not lender:
            raise NotFoundException("Lender not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(lender, field, value)

        lender.updated_by = updated_by
        await self.session.flush()
        return lender

    async def get_lender(self, lender_id: UUID) -> Lender:
        """Get a lender by ID."""
        lender = await self.lender_repo.get(lender_id)
        if not lender:
            raise NotFoundException("Lender not found")
        return lender

    async def list_lenders(
        self,
        organization_id: UUID,
        lender_type: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Lender], int]:
        """List lenders with optional filters."""
        if lender_type:
            return await self.lender_repo.get_by_type(organization_id, lender_type, skip, limit)
        return await self.lender_repo.get_active_lenders(organization_id, skip, limit)

    # =========================================================================
    # Borrowing Operations
    # =========================================================================

    async def create_borrowing(
        self,
        organization_id: UUID,
        data: BorrowingCreate,
        created_by: UUID | None = None,
    ) -> Borrowing:
        """Create a new borrowing facility."""
        # Validate lender exists
        lender = await self.lender_repo.get(data.lender_id)
        if not lender:
            raise NotFoundException("Lender not found")

        borrowing_number = await self.borrowing_repo.generate_borrowing_number(
            organization_id, data.borrowing_type
        )

        borrowing = Borrowing(
            organization_id=organization_id,
            borrowing_number=borrowing_number,
            available_amount=data.sanctioned_amount,
            status="SANCTIONED",
            created_by=created_by,
            **data.model_dump(exclude_unset=True),
        )

        self.session.add(borrowing)
        await self.session.flush()
        return borrowing

    async def update_borrowing(
        self,
        borrowing_id: UUID,
        data: BorrowingUpdate,
        updated_by: UUID | None = None,
    ) -> Borrowing:
        """Update a borrowing."""
        borrowing = await self.borrowing_repo.get(borrowing_id)
        if not borrowing:
            raise NotFoundException("Borrowing not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(borrowing, field, value)

        borrowing.updated_by = updated_by
        await self.session.flush()
        return borrowing

    async def get_borrowing(self, borrowing_id: UUID) -> Borrowing:
        """Get a borrowing by ID."""
        borrowing = await self.borrowing_repo.get(borrowing_id)
        if not borrowing:
            raise NotFoundException("Borrowing not found")
        return borrowing

    async def get_borrowing_with_details(self, borrowing_id: UUID) -> Borrowing:
        """Get borrowing with all related data."""
        borrowing = await self.borrowing_repo.get_with_details(borrowing_id)
        if not borrowing:
            raise NotFoundException("Borrowing not found")
        return borrowing

    async def list_borrowings(
        self,
        organization_id: UUID,
        lender_id: UUID | None = None,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Borrowing], int]:
        """List borrowings with optional filters.

        Returns ALL borrowings (regardless of status) when no status filter
        is given. Use ``status="ACTIVE"`` etc. to narrow.
        """
        return await self.borrowing_repo.list_for_org(
            organization_id, lender_id, status, skip, limit
        )

    # =========================================================================
    # Tranche/Drawdown Operations
    # =========================================================================

    async def create_tranche(
        self,
        data: BorrowingTrancheCreate,
        created_by: UUID | None = None,
    ) -> BorrowingTranche:
        """Create a drawdown request."""
        borrowing = await self.borrowing_repo.get(data.borrowing_id)
        if not borrowing:
            raise NotFoundException("Borrowing not found")

        if borrowing.status not in ["SANCTIONED", "ACTIVE"]:
            raise BadRequestException("Borrowing not in valid status for drawdown")

        if data.requested_amount > borrowing.available_amount:
            raise BadRequestException(
                f"Requested amount exceeds available amount of {borrowing.available_amount}"
            )

        tranche_number = await self.tranche_repo.get_next_tranche_number(data.borrowing_id)

        tranche = BorrowingTranche(
            borrowing_id=data.borrowing_id,
            tranche_number=tranche_number,
            request_date=data.request_date,
            requested_amount=data.requested_amount,
            purpose=data.purpose,
            status="REQUESTED",
            created_by=created_by,
        )

        self.session.add(tranche)
        await self.session.flush()
        return tranche

    async def approve_tranche(
        self,
        tranche_id: UUID,
        approved_by: UUID,
        remarks: str | None = None,
    ) -> BorrowingTranche:
        """Approve a drawdown request."""
        tranche = await self.tranche_repo.get(tranche_id)
        if not tranche:
            raise NotFoundException("Tranche not found")

        if tranche.status != "REQUESTED":
            raise BadRequestException("Tranche is not pending approval")

        tranche.status = "APPROVED"
        tranche.approved_by = approved_by
        tranche.approved_at = datetime.utcnow()
        tranche.remarks = remarks

        await self.session.flush()
        return tranche

    async def disburse_tranche(
        self,
        tranche_id: UUID,
        data: BorrowingTrancheDisbursement,
        updated_by: UUID | None = None,
    ) -> BorrowingTranche:
        """Process tranche disbursement."""
        tranche = await self.tranche_repo.get(tranche_id)
        if not tranche:
            raise NotFoundException("Tranche not found")

        if tranche.status != "APPROVED":
            raise BadRequestException("Tranche is not approved for disbursement")

        borrowing = await self.borrowing_repo.get(tranche.borrowing_id)

        # Update tranche
        tranche.disbursement_date = data.disbursement_date
        tranche.disbursed_amount = data.disbursed_amount
        tranche.principal_outstanding = data.disbursed_amount
        tranche.effective_rate = data.effective_rate or borrowing.effective_rate
        tranche.utr_number = data.utr_number
        tranche.bank_reference = data.bank_reference
        tranche.status = "DISBURSED"
        tranche.remarks = data.remarks

        # Update borrowing balances
        borrowing.drawn_amount += data.disbursed_amount
        borrowing.available_amount -= data.disbursed_amount
        borrowing.principal_outstanding += data.disbursed_amount

        if borrowing.status == "SANCTIONED":
            borrowing.status = "ACTIVE"

        if borrowing.available_amount <= 0:
            borrowing.status = "FULLY_DRAWN"

        await self.session.flush()
        return tranche

    # =========================================================================
    # Payment Operations
    # =========================================================================

    async def record_payment(
        self,
        data: BorrowingPaymentCreate,
        created_by: UUID | None = None,
    ) -> BorrowingPayment:
        """Record a borrowing payment."""
        borrowing = await self.borrowing_repo.get(data.borrowing_id)
        if not borrowing:
            raise NotFoundException("Borrowing not found")

        total_amount = data.principal_amount + data.interest_amount + data.fee_amount

        # Calculate days for interest if not provided
        days_counted = None
        if data.interest_from_date and data.interest_to_date:
            days_counted = (data.interest_to_date - data.interest_from_date).days

        payment = BorrowingPayment(
            borrowing_id=data.borrowing_id,
            schedule_id=data.schedule_id,
            payment_type=data.payment_type,
            payment_date=data.payment_date,
            value_date=data.value_date,
            principal_amount=data.principal_amount,
            interest_amount=data.interest_amount,
            fee_amount=data.fee_amount,
            total_amount=total_amount,
            payment_mode=data.payment_mode,
            utr_number=data.utr_number,
            bank_reference=data.bank_reference,
            from_bank_account=data.from_bank_account,
            interest_from_date=data.interest_from_date,
            interest_to_date=data.interest_to_date,
            days_counted=days_counted,
            rate_applied=borrowing.effective_rate,
            remarks=data.remarks,
            created_by=created_by,
        )

        self.session.add(payment)

        # Update borrowing principal outstanding
        if data.principal_amount > 0:
            borrowing.principal_outstanding -= data.principal_amount
            if borrowing.principal_outstanding <= 0:
                borrowing.status = "CLOSED"

        # Update schedule if linked
        if data.schedule_id:
            schedule = await self.schedule_repo.get(data.schedule_id)
            if schedule:
                schedule.principal_paid += data.principal_amount
                schedule.interest_paid += data.interest_amount
                schedule.total_paid += total_amount
                schedule.paid_date = data.payment_date
                if (
                    schedule.principal_paid >= schedule.principal_due
                    and schedule.interest_paid >= schedule.interest_due
                ):
                    schedule.status = "PAID"
                elif schedule.total_paid > 0:
                    schedule.status = "PARTIALLY_PAID"

        await self.session.flush()
        return payment

    async def list_payments(
        self,
        borrowing_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[BorrowingPayment], int]:
        """List payments for a borrowing."""
        return await self.payment_repo.get_by_borrowing(borrowing_id, skip, limit)

    # =========================================================================
    # Schedule Operations
    # =========================================================================

    async def generate_schedule(
        self,
        borrowing_id: UUID,
        created_by: UUID | None = None,
    ) -> list[BorrowingSchedule]:
        """Generate repayment schedule for a borrowing."""
        borrowing = await self.borrowing_repo.get(borrowing_id)
        if not borrowing:
            raise NotFoundException("Borrowing not found")

        schedules = []
        principal = borrowing.principal_outstanding
        rate = borrowing.effective_rate / Decimal("100") / 12  # Monthly rate

        # Determine number of installments
        total_months = borrowing.tenure_months - borrowing.moratorium_months

        # Calculate start date
        start_date = borrowing.first_principal_date or borrowing.sanction_date
        if borrowing.moratorium_months > 0:
            start_date = start_date + timedelta(days=borrowing.moratorium_months * 30)

        # Simple equal principal repayment
        principal_per_installment = principal / total_months

        current_date = start_date
        opening_balance = principal

        for i in range(total_months):
            interest_due = opening_balance * rate
            closing_balance = opening_balance - principal_per_installment

            schedule = BorrowingSchedule(
                borrowing_id=borrowing_id,
                installment_number=i + 1,
                due_date=current_date,
                principal_due=principal_per_installment,
                interest_due=interest_due,
                total_due=principal_per_installment + interest_due,
                opening_balance=opening_balance,
                closing_balance=max(closing_balance, Decimal("0")),
                status="NOT_DUE",
                created_by=created_by,
            )

            self.session.add(schedule)
            schedules.append(schedule)

            opening_balance = closing_balance
            current_date = current_date + timedelta(days=30)  # Approximate monthly

        await self.session.flush()
        return schedules

    async def get_schedule(
        self,
        borrowing_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[BorrowingSchedule], int]:
        """Get repayment schedule for a borrowing."""
        return await self.schedule_repo.get_by_borrowing(borrowing_id, skip, limit)

    # =========================================================================
    # Covenant Operations
    # =========================================================================

    async def create_covenant(
        self,
        data: BorrowingCovenantCreate,
        created_by: UUID | None = None,
    ) -> BorrowingCovenant:
        """Create a borrowing covenant."""
        borrowing = await self.borrowing_repo.get(data.borrowing_id)
        if not borrowing:
            raise NotFoundException("Borrowing not found")

        covenant = BorrowingCovenant(
            created_by=created_by,
            **data.model_dump(exclude_unset=True),
        )

        self.session.add(covenant)
        await self.session.flush()
        return covenant

    async def update_covenant(
        self,
        covenant_id: UUID,
        data: BorrowingCovenantUpdate,
        updated_by: UUID | None = None,
    ) -> BorrowingCovenant:
        """Update a covenant."""
        covenant = await self.covenant_repo.get(covenant_id)
        if not covenant:
            raise NotFoundException("Covenant not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(covenant, field, value)

        covenant.updated_by = updated_by
        await self.session.flush()
        return covenant

    async def test_covenant(
        self,
        covenant_id: UUID,
        current_value: Decimal,
        updated_by: UUID | None = None,
    ) -> BorrowingCovenant:
        """Test a covenant and update status."""
        covenant = await self.covenant_repo.get(covenant_id)
        if not covenant:
            raise NotFoundException("Covenant not found")

        covenant.current_value = current_value
        covenant.last_tested_date = date.today()

        # Determine compliance
        is_compliant = True
        if covenant.threshold_type == "MIN":
            is_compliant = current_value >= covenant.threshold_value
        elif covenant.threshold_type == "MAX":
            is_compliant = current_value <= covenant.threshold_value
        elif covenant.threshold_type == "RANGE":
            is_compliant = (
                current_value >= covenant.threshold_min and current_value <= covenant.threshold_max
            )

        covenant.status = "COMPLIANT" if is_compliant else "NON_COMPLIANT"
        covenant.updated_by = updated_by

        await self.session.flush()
        return covenant

    # =========================================================================
    # ALM Operations
    # =========================================================================

    async def generate_alm_position(
        self,
        organization_id: UUID,
        data: ALMPositionGenerate,
        generated_by: UUID | None = None,
    ) -> ALMPosition:
        """Generate ALM position snapshot."""
        # Check if position already exists
        existing = await self.alm_position_repo.get_by_date(organization_id, data.position_date)
        if existing:
            # Delete existing assets and liabilities for regeneration
            await self.alm_asset_repo.delete_by_position(existing.position_id)
            await self.alm_liability_repo.delete_by_position(existing.position_id)
            position = existing
        else:
            position = ALMPosition(
                organization_id=organization_id,
                position_date=data.position_date,
                generated_by=generated_by,
                remarks=data.remarks,
            )
            self.session.add(position)
            await self.session.flush()

        # Generate assets from loan accounts (simplified)
        # In production, this would query loan accounts and investments
        total_assets = Decimal("0")
        total_liabilities = Decimal("0")

        bucket_analysis = {}

        # Generate liabilities from borrowings
        borrowings, _ = await self.borrowing_repo.get_active_borrowings(organization_id, 0, 1000)

        for borrowing in borrowings:
            days_to_maturity = (borrowing.maturity_date - data.position_date).days
            bucket = self._get_alm_bucket(days_to_maturity)

            liability = ALMLiability(
                position_id=position.position_id,
                liability_type="BORROWINGS_BANK",
                alm_bucket=bucket,
                book_value=borrowing.principal_outstanding,
                rate_sensitive_amount=(
                    borrowing.principal_outstanding
                    if borrowing.rate_type == "FLOATING"
                    else Decimal("0")
                ),
                non_rate_sensitive_amount=(
                    borrowing.principal_outstanding
                    if borrowing.rate_type == "FIXED"
                    else Decimal("0")
                ),
                weighted_avg_rate=borrowing.effective_rate,
                weighted_avg_maturity_days=days_to_maturity,
                source_type="BORROWING",
                source_count=1,
            )
            self.session.add(liability)
            total_liabilities += borrowing.principal_outstanding

            # Update bucket analysis
            if bucket not in bucket_analysis:
                bucket_analysis[bucket] = {"assets": 0, "liabilities": 0, "gap": 0}
            bucket_analysis[bucket]["liabilities"] += float(borrowing.principal_outstanding)

        # Calculate gaps
        cumulative_gap = Decimal("0")
        for bucket in self.ALM_BUCKETS.keys():
            if bucket in bucket_analysis:
                bucket_analysis[bucket]["gap"] = (
                    bucket_analysis[bucket]["assets"] - bucket_analysis[bucket]["liabilities"]
                )
                cumulative_gap += Decimal(str(bucket_analysis[bucket]["gap"]))
                bucket_analysis[bucket]["cumulative_gap"] = float(cumulative_gap)

        # Update position totals
        position.total_assets = total_assets
        position.total_liabilities = total_liabilities
        position.net_position = total_assets - total_liabilities
        position.bucket_analysis = bucket_analysis
        position.cumulative_gap_1_year = cumulative_gap
        if total_liabilities > 0:
            position.cumulative_gap_percent = (cumulative_gap / total_liabilities) * 100

        await self.session.flush()
        return position

    def _get_alm_bucket(self, days: int) -> str:
        """Get ALM bucket for given days to maturity."""
        for bucket, (min_days, max_days) in self.ALM_BUCKETS.items():
            if min_days <= days <= max_days:
                return bucket
        return "OVER_5_YEARS"

    async def get_alm_position(self, position_id: UUID) -> ALMPosition:
        """Get ALM position with details."""
        position = await self.alm_position_repo.get_with_details(position_id)
        if not position:
            raise NotFoundException("ALM position not found")
        return position

    async def get_latest_alm_position(self, organization_id: UUID) -> ALMPosition | None:
        """Get latest ALM position."""
        return await self.alm_position_repo.get_latest(organization_id)

    # =========================================================================
    # IRS Analysis Operations
    # =========================================================================

    async def generate_irs_analysis(
        self,
        organization_id: UUID,
        data: IRSAnalysisGenerate,
        generated_by: UUID | None = None,
    ) -> IRSAnalysis:
        """Generate Interest Rate Sensitivity analysis."""
        # Get latest ALM position
        position = await self.alm_position_repo.get_by_date(organization_id, data.analysis_date)

        # Calculate rate sensitive amounts (simplified)
        rsa = Decimal("0")  # Rate Sensitive Assets
        rsl = Decimal("0")  # Rate Sensitive Liabilities

        borrowings, _ = await self.borrowing_repo.get_active_borrowings(organization_id, 0, 1000)

        for borrowing in borrowings:
            if borrowing.rate_type in ["FLOATING", "MCLR_LINKED", "REPO_LINKED"]:
                rsl += borrowing.principal_outstanding

        gap = rsa - rsl

        # Calculate NII impact
        shock_rate = Decimal(str(data.shock_bps)) / Decimal("10000")
        nii_impact = gap * shock_rate
        nii_impact_percent = Decimal("0")
        if rsl > 0:
            nii_impact_percent = (nii_impact / rsl) * 100

        analysis = IRSAnalysis(
            organization_id=organization_id,
            position_id=position.position_id if position else None,
            analysis_date=data.analysis_date,
            shock_type=data.shock_type,
            shock_bps=data.shock_bps,
            rate_sensitive_assets=rsa,
            rate_sensitive_liabilities=rsl,
            rate_sensitivity_gap=gap,
            nii_impact=nii_impact,
            nii_impact_percent=nii_impact_percent,
            generated_by=generated_by,
            remarks=data.remarks,
        )

        self.session.add(analysis)
        await self.session.flush()
        return analysis

    # Default shock buckets for the dashboard preview (basis points).
    _DEFAULT_IRS_SHOCK_BUCKETS_BPS = (-200, -100, -50, 50, 100, 200)

    async def preview_irs_analysis(
        self,
        organization_id: UUID,
        as_of_date: date | None = None,
        shock_bps_buckets: list[int] | None = None,
    ) -> IRSPreviewResponse:
        """Compute Interest Rate Sensitivity (IRS) preview without persisting.

        For each rate-shock bucket (basis points), returns the projected impact
        on Net Interest Income (NII) given current rate-sensitive assets (RSA)
        and rate-sensitive liabilities (RSL). Used by the IRS dashboard view —
        no rows are written to `trs_irs_analysis`.

        - RSA = principal_outstanding of active loans with InterestType.FLOATING.
        - RSL = principal_outstanding of active borrowings whose rate_type is
          FLOATING / MCLR_LINKED / REPO_LINKED.
        - Gap = RSA - RSL.
        - NII impact = Gap * (shock_bps / 10_000).
        - NII impact % = NII impact / RSL * 100 (0 if RSL == 0).
        """
        analysis_date = as_of_date or date.today()
        buckets_bps = list(shock_bps_buckets or self._DEFAULT_IRS_SHOCK_BUCKETS_BPS)

        # --- Rate-sensitive assets: active FLOATING loan accounts --------------
        rsa_query = select(func.coalesce(func.sum(LoanAccount.principal_outstanding), 0)).where(
            LoanAccount.organization_id == organization_id,
            LoanAccount.interest_type == InterestType.FLOATING,
            LoanAccount.status == LoanAccountStatus.ACTIVE,
            LoanAccount.is_active == True,  # noqa: E712
        )
        rsa_result = await self.session.execute(rsa_query)
        rsa = Decimal(str(rsa_result.scalar() or 0))

        # Total assets across all active loans (for gap-to-total-assets ratio).
        total_assets_query = select(
            func.coalesce(func.sum(LoanAccount.principal_outstanding), 0)
        ).where(
            LoanAccount.organization_id == organization_id,
            LoanAccount.status == LoanAccountStatus.ACTIVE,
            LoanAccount.is_active == True,  # noqa: E712
        )
        total_assets_result = await self.session.execute(total_assets_query)
        total_assets = Decimal(str(total_assets_result.scalar() or 0))

        # --- Rate-sensitive liabilities: floating-rate borrowings --------------
        borrowings, _ = await self.borrowing_repo.get_active_borrowings(organization_id, 0, 1000)
        rsl = Decimal("0")
        for borrowing in borrowings:
            if borrowing.rate_type in ("FLOATING", "MCLR_LINKED", "REPO_LINKED"):
                rsl += borrowing.principal_outstanding

        gap = rsa - rsl

        # --- Build per-shock impact rows --------------------------------------
        shock_buckets: list[IRSShockBucket] = []
        for shock_bps in buckets_bps:
            shock_rate = Decimal(str(shock_bps)) / Decimal("10000")
            nii_impact = (gap * shock_rate).quantize(Decimal("0.01"))
            nii_impact_percent = Decimal("0")
            if rsl > 0:
                nii_impact_percent = ((nii_impact / rsl) * 100).quantize(Decimal("0.0001"))
            shock_buckets.append(
                IRSShockBucket(
                    shock_bps=shock_bps,
                    rsa=rsa,
                    rsl=rsl,
                    gap=gap,
                    nii_impact=nii_impact,
                    nii_impact_percent=nii_impact_percent,
                )
            )

        # --- Summary block -----------------------------------------------------
        gap_to_total_assets_percent = Decimal("0")
        if total_assets > 0:
            gap_to_total_assets_percent = ((gap / total_assets) * 100).quantize(Decimal("0.0001"))

        summary = IRSPreviewSummary(
            rsa=rsa,
            rsl=rsl,
            gap=gap,
            total_assets=total_assets,
            gap_to_total_assets_percent=gap_to_total_assets_percent,
        )

        return IRSPreviewResponse(
            as_of_date=analysis_date,
            summary=summary,
            shocks=shock_buckets,
        )

    # =========================================================================
    # Exposure Limit Operations
    # =========================================================================

    async def create_exposure_limit(
        self,
        organization_id: UUID,
        data: ExposureLimitCreate,
        created_by: UUID | None = None,
    ) -> ExposureLimit:
        """Create an exposure limit."""
        # Check if limit already exists
        existing = await self.exposure_limit_repo.get_by_type_key(
            organization_id, data.limit_type, data.limit_key
        )
        if existing:
            raise BadRequestException(
                f"Limit already exists for {data.limit_type}/{data.limit_key}"
            )

        limit = ExposureLimit(
            organization_id=organization_id,
            created_by=created_by,
            **data.model_dump(exclude_unset=True),
        )

        self.session.add(limit)
        await self.session.flush()
        return limit

    async def update_exposure_limit(
        self,
        limit_id: UUID,
        data: ExposureLimitUpdate,
        updated_by: UUID | None = None,
    ) -> ExposureLimit:
        """Update an exposure limit."""
        limit = await self.exposure_limit_repo.get(limit_id)
        if not limit:
            raise NotFoundException("Exposure limit not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(limit, field, value)

        limit.updated_by = updated_by
        await self.session.flush()
        return limit

    async def check_exposure(
        self,
        organization_id: UUID,
        limit_type: str,
        limit_key: str,
        additional_exposure: Decimal,
    ) -> dict[str, Any]:
        """Check if additional exposure would breach limit."""
        limit = await self.exposure_limit_repo.get_by_type_key(
            organization_id, limit_type, limit_key
        )

        if not limit:
            return {
                "limit_exists": False,
                "can_proceed": True,
                "message": "No limit defined",
            }

        new_exposure = limit.current_exposure + additional_exposure
        effective_limit = limit.internal_limit_amount or limit.regulatory_limit_amount

        if effective_limit and new_exposure > effective_limit:
            return {
                "limit_exists": True,
                "can_proceed": False,
                "current_exposure": float(limit.current_exposure),
                "new_exposure": float(new_exposure),
                "limit": float(effective_limit),
                "breach_amount": float(new_exposure - effective_limit),
                "message": "Exposure would breach limit",
            }

        warning_threshold = effective_limit * (limit.warning_threshold_percent / 100)
        if new_exposure > warning_threshold:
            return {
                "limit_exists": True,
                "can_proceed": True,
                "warning": True,
                "current_exposure": float(limit.current_exposure),
                "new_exposure": float(new_exposure),
                "limit": float(effective_limit),
                "utilization_percent": float(new_exposure / effective_limit * 100),
                "message": "Exposure approaching limit threshold",
            }

        return {
            "limit_exists": True,
            "can_proceed": True,
            "warning": False,
            "current_exposure": float(limit.current_exposure),
            "new_exposure": float(new_exposure),
            "limit": float(effective_limit),
            "message": "Within limits",
        }

    # =========================================================================
    # Summary Operations
    # =========================================================================

    async def get_borrowing_summary(self, organization_id: UUID) -> BorrowingSummary:
        """Get borrowing summary."""
        borrowings, count = await self.borrowing_repo.get_active_borrowings(
            organization_id, 0, 1000
        )

        total_sanctioned = sum(b.sanctioned_amount for b in borrowings)
        total_drawn = sum(b.drawn_amount for b in borrowings)
        total_available = sum(b.available_amount for b in borrowings)
        total_outstanding = sum(b.principal_outstanding for b in borrowings)

        # Get unique lenders
        lender_ids = set(b.lender_id for b in borrowings)

        # Calculate weighted average rate
        weighted_rate = Decimal("0")
        if total_outstanding > 0:
            for b in borrowings:
                weighted_rate += b.effective_rate * (b.principal_outstanding / total_outstanding)

        # Get upcoming repayments
        upcoming = await self.schedule_repo.get_upcoming_payments(organization_id, 30)
        upcoming_amount = sum(s.total_due - s.total_paid for s in upcoming)

        # Get maturing borrowings
        maturing = await self.borrowing_repo.get_maturing_borrowings(organization_id, 90)

        return BorrowingSummary(
            total_sanctioned=total_sanctioned,
            total_drawn=total_drawn,
            total_available=total_available,
            total_outstanding=total_outstanding,
            active_borrowings=count,
            lender_count=len(lender_ids),
            weighted_avg_rate=weighted_rate if borrowings else None,
            upcoming_repayments_30d=upcoming_amount,
            upcoming_maturities_90d=len(maturing),
        )

    async def get_alm_summary(self, organization_id: UUID) -> ALMSummary | None:
        """Get ALM summary."""
        position = await self.alm_position_repo.get_latest(organization_id)
        if not position:
            return None

        gap_analysis = []
        if position.bucket_analysis:
            for bucket, data in position.bucket_analysis.items():
                gap_analysis.append(
                    ALMGapAnalysis(
                        bucket=bucket,
                        assets=Decimal(str(data.get("assets", 0))),
                        liabilities=Decimal(str(data.get("liabilities", 0))),
                        gap=Decimal(str(data.get("gap", 0))),
                        cumulative_gap=Decimal(str(data.get("cumulative_gap", 0))),
                        gap_percent=Decimal("0"),  # Calculate if needed
                    )
                )

        return ALMSummary(
            position_date=position.position_date,
            total_assets=position.total_assets,
            total_liabilities=position.total_liabilities,
            net_position=position.net_position,
            cumulative_gap_1_year=position.cumulative_gap_1_year or Decimal("0"),
            cumulative_gap_percent=position.cumulative_gap_percent or Decimal("0"),
            gap_analysis=gap_analysis,
        )

    async def get_exposure_summary(self, organization_id: UUID) -> ExposureSummary:
        """Get exposure summary."""
        # Org-scoped fetch — `get_all` on the base is unscoped, so we query
        # directly via the same session.
        from sqlalchemy import select as _select

        result = await self.exposure_limit_repo.session.execute(
            _select(ExposureLimit).where(
                ExposureLimit.organization_id == organization_id,
                ExposureLimit.is_active == True,  # noqa: E712
            )
        )
        limits = list(result.scalars().all())
        total = len(limits)

        within_limit = sum(1 for l in limits if l.status == "WITHIN_LIMIT")
        near_limit = sum(1 for l in limits if l.status == "NEAR_LIMIT")
        breach = sum(1 for l in limits if l.status == "BREACH")
        total_exposure = sum(l.current_exposure for l in limits)

        # Get top exposures
        top_exposures = sorted(limits, key=lambda l: l.current_exposure, reverse=True)[:5]

        return ExposureSummary(
            total_limits=total,
            within_limit=within_limit,
            near_limit=near_limit,
            breach_count=breach,
            total_exposure=total_exposure,
            top_exposures=[
                {
                    "type": l.limit_type,
                    "key": l.limit_key,
                    "exposure": float(l.current_exposure),
                    "status": l.status,
                }
                for l in top_exposures
            ],
        )

    async def get_treasury_summary(self, organization_id: UUID) -> TreasurySummary:
        """Get complete treasury summary."""
        borrowing_summary = await self.get_borrowing_summary(organization_id)
        alm_summary = await self.get_alm_summary(organization_id)
        exposure_summary = await self.get_exposure_summary(organization_id)

        return TreasurySummary(
            borrowing_summary=borrowing_summary,
            alm_summary=alm_summary,
            exposure_summary=exposure_summary,
        )
