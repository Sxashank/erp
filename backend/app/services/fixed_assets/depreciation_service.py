"""Depreciation service for Fixed Assets module."""

from calendar import monthrange
from collections import defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.fixed_assets.fixed_asset import FixedAsset
from app.models.fixed_assets.asset_category import AssetCategory
from app.models.fixed_assets.depreciation import Depreciation, DepreciationRun
from app.core.constants import (
    AssetStatus,
    DepreciationMethod,
    DepreciationType,
    GLEntrySourceType,
)
from app.schemas.fixed_assets.depreciation import (
    DepreciationRunCreate,
    DepreciationScheduleItem,
    DepreciationScheduleResponse,
)
from app.services.fixed_assets.asset_service import AssetService
from app.services.finance.gl_posting_service import GLPostingService
from app.repositories.finance.financial_year_repo import (
    FinancialYearRepository,
    FinancialPeriodRepository,
)


class DepreciationService:
    """Service for depreciation operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.asset_service = AssetService(session)
        self.gl_posting_service = GLPostingService(session)
        self.fy_repo = FinancialYearRepository(session)
        self.period_repo = FinancialPeriodRepository(session)

    async def run_depreciation(
        self,
        data: DepreciationRunCreate,
        run_by: Optional[UUID] = None,
    ) -> DepreciationRun:
        """Run monthly depreciation for all eligible assets."""
        # Check if run already exists for this period
        existing = await self._get_run_by_period(
            data.organization_id, data.depreciation_period
        )
        if existing:
            raise ValueError(
                f"Depreciation run already exists for period {data.depreciation_period}"
            )

        # Parse period
        year, month = map(int, data.depreciation_period.split("-"))
        period_from = date(year, month, 1)
        period_to = date(year, month, monthrange(year, month)[1])
        days_in_month = (period_to - period_from).days + 1

        # Create depreciation run
        dep_run = DepreciationRun(
            organization_id=data.organization_id,
            depreciation_period=data.depreciation_period,
            period_from=period_from,
            period_to=period_to,
            status="PROCESSING",
            run_started_at=datetime.now(timezone.utc),
            run_by=run_by,
            remarks=data.remarks,
        )
        if run_by:
            dep_run.created_by = run_by

        self.session.add(dep_run)
        await self.session.flush()

        # Get eligible assets
        assets = await self.asset_service.get_assets_for_depreciation(
            data.organization_id, period_to
        )

        total_depreciation = Decimal("0.00")
        processed_count = 0
        skipped_count = 0

        for asset in assets:
            # Check if depreciation already exists for this asset/period
            existing_dep = await self._get_depreciation_by_asset_period(
                asset.id, data.depreciation_period
            )
            if existing_dep:
                skipped_count += 1
                continue

            # Calculate days for pro-rata (if asset was put to use mid-month)
            if asset.depreciation_start_date and asset.depreciation_start_date > period_from:
                if asset.depreciation_start_date > period_to:
                    skipped_count += 1
                    continue
                days = (period_to - asset.depreciation_start_date).days + 1
            else:
                days = days_in_month

            # Calculate depreciation
            dep_amount = self._calculate_depreciation(
                asset=asset,
                days=days,
                days_in_year=365,
            )

            if dep_amount <= Decimal("0.00"):
                skipped_count += 1
                continue

            # Check if this would take WDV below residual value
            new_accumulated = asset.accumulated_depreciation + dep_amount
            new_wdv = asset.total_cost - new_accumulated
            if new_wdv < asset.residual_value:
                # Limit depreciation to not go below residual
                dep_amount = asset.wdv_value - asset.residual_value
                if dep_amount <= Decimal("0.00"):
                    skipped_count += 1
                    continue
                new_accumulated = asset.accumulated_depreciation + dep_amount
                new_wdv = asset.residual_value

            # Create depreciation entry
            depreciation = Depreciation(
                asset_id=asset.id,
                depreciation_run_id=dep_run.id,
                depreciation_period=data.depreciation_period,
                period_from=period_from,
                period_to=period_to,
                days_in_period=days,
                opening_wdv=asset.wdv_value,
                depreciation_rate=asset.depreciation_rate,
                depreciation_amount=dep_amount,
                accumulated_depreciation=new_accumulated,
                closing_wdv=new_wdv,
                depreciation_type=DepreciationType.REGULAR,
                is_posted=False,
            )
            if run_by:
                depreciation.created_by = run_by

            self.session.add(depreciation)

            # Update asset
            asset.accumulated_depreciation = new_accumulated
            asset.wdv_value = new_wdv
            asset.last_depreciation_date = period_to

            # Check if fully depreciated
            if new_wdv <= asset.residual_value:
                asset.status = AssetStatus.FULLY_DEPRECIATED

            total_depreciation += dep_amount
            processed_count += 1

        # Update run
        dep_run.total_assets = len(assets)
        dep_run.processed_assets = processed_count
        dep_run.skipped_assets = skipped_count
        dep_run.total_depreciation = total_depreciation
        dep_run.status = "COMPLETED"
        dep_run.run_completed_at = datetime.now(timezone.utc)

        await self.session.flush()
        await self.session.refresh(dep_run)
        return dep_run

    async def post_depreciation_run(
        self,
        run_id: UUID,
        posted_by: Optional[UUID] = None,
    ) -> DepreciationRun:
        """Post depreciation run to GL."""
        dep_run = await self.get_run(run_id)
        if not dep_run:
            raise ValueError("Depreciation run not found")

        if dep_run.status != "COMPLETED":
            raise ValueError("Depreciation run must be completed before posting")

        if dep_run.voucher_id:
            raise ValueError("Depreciation run already posted")

        # Get all depreciation entries for this run
        result = await self.session.execute(
            select(Depreciation)
            .options(selectinload(Depreciation.asset).selectinload(FixedAsset.category))
            .where(Depreciation.depreciation_run_id == run_id)
        )
        entries = result.scalars().all()

        if entries:
            # Group depreciation by category for GL entries
            category_totals: Dict[UUID, Dict[str, Any]] = defaultdict(
                lambda: {"depreciation_amount": Decimal("0.00"), "category": None}
            )

            for entry in entries:
                if entry.asset and entry.asset.category:
                    cat_id = entry.asset.category_id
                    category_totals[cat_id]["depreciation_amount"] += entry.depreciation_amount
                    category_totals[cat_id]["category"] = entry.asset.category

            # Create GL voucher for depreciation
            # Dr Depreciation Expense (per category)
            # Cr Accumulated Depreciation (per category)
            voucher_id = await self._post_depreciation_gl(
                organization_id=dep_run.organization_id,
                depreciation_period=dep_run.depreciation_period,
                period_to=dep_run.period_to,
                category_totals=category_totals,
                run_id=run_id,
                posted_by=posted_by,
            )

            if voucher_id:
                dep_run.voucher_id = voucher_id

        # Mark entries as posted
        for entry in entries:
            entry.is_posted = True
            entry.voucher_id = dep_run.voucher_id

        # Update run
        dep_run.status = "POSTED"
        dep_run.posted_at = datetime.now(timezone.utc)
        dep_run.posted_by = posted_by

        await self.session.flush()
        await self.session.refresh(dep_run)
        return dep_run

    async def execute_approved_posting_request(
        self,
        request,
        posted_by: Optional[UUID] = None,
    ) -> DepreciationRun:
        """Execute the posting mutation for an approved depreciation request."""
        return await self.post_depreciation_run(request.entity_id, posted_by=posted_by)

    async def reverse_depreciation(
        self,
        depreciation_id: UUID,
        reason: str,
        reversed_by: Optional[UUID] = None,
    ) -> Depreciation:
        """Reverse a depreciation entry."""
        original = await self.get_depreciation(depreciation_id)
        if not original:
            raise ValueError("Depreciation entry not found")

        if original.is_reversed:
            raise ValueError("Entry already reversed")

        # Create reversal entry
        reversal = Depreciation(
            asset_id=original.asset_id,
            depreciation_period=original.depreciation_period,
            period_from=original.period_from,
            period_to=original.period_to,
            days_in_period=original.days_in_period,
            opening_wdv=original.closing_wdv,
            depreciation_rate=original.depreciation_rate,
            depreciation_amount=-original.depreciation_amount,  # Negative
            accumulated_depreciation=original.opening_wdv - original.total_cost + original.accumulated_depreciation - original.depreciation_amount,
            closing_wdv=original.opening_wdv,
            depreciation_type=DepreciationType.REVERSAL,
            is_posted=False,
            reversal_of_id=original.id,
            remarks=reason,
        )
        if reversed_by:
            reversal.created_by = reversed_by

        self.session.add(reversal)

        # Mark original as reversed
        original.is_reversed = True
        original.reversed_by_id = reversal.id

        # Update asset
        asset = await self.asset_service.get(original.asset_id)
        if asset:
            asset.accumulated_depreciation -= original.depreciation_amount
            asset.wdv_value += original.depreciation_amount
            if asset.status == AssetStatus.FULLY_DEPRECIATED:
                asset.status = AssetStatus.ACTIVE

        await self.session.flush()
        await self.session.refresh(reversal)
        return reversal

    async def generate_depreciation_schedule(
        self,
        asset_id: UUID,
        periods: int = 60,
    ) -> DepreciationScheduleResponse:
        """Generate projected depreciation schedule for an asset."""
        asset = await self.asset_service.get(asset_id)
        if not asset:
            raise ValueError("Asset not found")

        schedule = []
        current_wdv = asset.wdv_value
        accumulated = asset.accumulated_depreciation
        start_date = asset.last_depreciation_date or asset.depreciation_start_date or date.today()

        # Start from next month
        if start_date.day > 1:
            if start_date.month == 12:
                start_year = start_date.year + 1
                start_month = 1
            else:
                start_year = start_date.year
                start_month = start_date.month + 1
        else:
            start_year = start_date.year
            start_month = start_date.month

        for i in range(periods):
            # Calculate period dates
            month = ((start_month - 1 + i) % 12) + 1
            year = start_year + ((start_month - 1 + i) // 12)
            period_str = f"{year:04d}-{month:02d}"
            period_from = date(year, month, 1)
            period_to = date(year, month, monthrange(year, month)[1])
            days = (period_to - period_from).days + 1

            # Check if fully depreciated
            if current_wdv <= asset.residual_value:
                schedule.append(DepreciationScheduleItem(
                    period=period_str,
                    period_from=period_from,
                    period_to=period_to,
                    opening_wdv=current_wdv,
                    depreciation_rate=asset.depreciation_rate,
                    depreciation_amount=Decimal("0.00"),
                    accumulated_depreciation=accumulated,
                    closing_wdv=current_wdv,
                    is_fully_depreciated=True,
                ))
                break

            # Calculate depreciation
            dep_amount = self._calculate_depreciation(
                asset=asset,
                days=days,
                days_in_year=365,
                wdv_override=current_wdv,
            )

            # Check residual value limit
            if current_wdv - dep_amount < asset.residual_value:
                dep_amount = current_wdv - asset.residual_value

            new_wdv = current_wdv - dep_amount
            accumulated += dep_amount

            schedule.append(DepreciationScheduleItem(
                period=period_str,
                period_from=period_from,
                period_to=period_to,
                opening_wdv=current_wdv,
                depreciation_rate=asset.depreciation_rate,
                depreciation_amount=dep_amount,
                accumulated_depreciation=accumulated,
                closing_wdv=new_wdv,
                is_fully_depreciated=new_wdv <= asset.residual_value,
            ))

            current_wdv = new_wdv

        # Calculate remaining months
        remaining = 0
        for item in schedule:
            if not item.is_fully_depreciated:
                remaining += 1

        return DepreciationScheduleResponse(
            asset_id=asset.id,
            asset_code=asset.asset_code,
            asset_name=asset.asset_name,
            total_cost=asset.total_cost,
            residual_value=asset.residual_value,
            depreciable_value=asset.depreciable_value,
            depreciation_method=asset.depreciation_method,
            depreciation_rate=asset.depreciation_rate,
            useful_life_months=asset.useful_life_months,
            current_wdv=asset.wdv_value,
            current_accumulated_depreciation=asset.accumulated_depreciation,
            remaining_months=remaining,
            schedule=schedule,
        )

    async def get_run(self, run_id: UUID) -> Optional[DepreciationRun]:
        """Get depreciation run by ID."""
        result = await self.session.execute(
            select(DepreciationRun)
            .options(selectinload(DepreciationRun.entries))
            .where(DepreciationRun.id == run_id)
        )
        return result.scalar_one_or_none()

    async def get_depreciation(self, depreciation_id: UUID) -> Optional[Depreciation]:
        """Get depreciation entry by ID."""
        result = await self.session.execute(
            select(Depreciation)
            .options(selectinload(Depreciation.asset))
            .where(Depreciation.id == depreciation_id)
        )
        return result.scalar_one_or_none()

    async def list_runs(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[DepreciationRun], int]:
        """List depreciation runs."""
        query = select(DepreciationRun).where(
            DepreciationRun.organization_id == organization_id
        )

        # Count
        count_result = await self.session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        # Fetch
        result = await self.session.execute(
            query.order_by(DepreciationRun.depreciation_period.desc())
            .offset(skip)
            .limit(limit)
        )
        runs = list(result.scalars().all())

        return runs, total

    async def get_depreciation_history(
        self,
        asset_id: UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Depreciation], int]:
        """Get depreciation history for an asset."""
        query = select(Depreciation).where(Depreciation.asset_id == asset_id)

        # Count
        count_result = await self.session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total = count_result.scalar_one()

        # Fetch
        result = await self.session.execute(
            query.order_by(Depreciation.depreciation_period.desc())
            .offset(skip)
            .limit(limit)
        )
        entries = list(result.scalars().all())

        return entries, total

    def _calculate_depreciation(
        self,
        asset: FixedAsset,
        days: int,
        days_in_year: int,
        wdv_override: Optional[Decimal] = None,
    ) -> Decimal:
        """Calculate depreciation amount based on method."""
        wdv = wdv_override if wdv_override is not None else asset.wdv_value

        if asset.depreciation_method == DepreciationMethod.SLM:
            # Straight Line Method
            # Annual depreciation = (Cost - Residual) / Useful Life
            # OR = Depreciable Value * Rate
            annual_dep = asset.depreciable_value * asset.depreciation_rate / 100
            dep_amount = annual_dep * Decimal(days) / Decimal(days_in_year)

        elif asset.depreciation_method == DepreciationMethod.WDV:
            # Written Down Value Method
            # Depreciation = WDV * Rate
            annual_dep = wdv * asset.depreciation_rate / 100
            dep_amount = annual_dep * Decimal(days) / Decimal(days_in_year)

        elif asset.depreciation_method == DepreciationMethod.UNIT_OF_PRODUCTION:
            # For UOP, we need actual units - skip for now
            dep_amount = Decimal("0.00")

        else:
            dep_amount = Decimal("0.00")

        return dep_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    async def _get_run_by_period(
        self,
        organization_id: UUID,
        period: str,
    ) -> Optional[DepreciationRun]:
        """Get depreciation run by period."""
        result = await self.session.execute(
            select(DepreciationRun).where(
                DepreciationRun.organization_id == organization_id,
                DepreciationRun.depreciation_period == period,
            )
        )
        return result.scalar_one_or_none()

    async def _get_depreciation_by_asset_period(
        self,
        asset_id: UUID,
        period: str,
    ) -> Optional[Depreciation]:
        """Get depreciation entry by asset and period."""
        result = await self.session.execute(
            select(Depreciation).where(
                Depreciation.asset_id == asset_id,
                Depreciation.depreciation_period == period,
                Depreciation.depreciation_type == DepreciationType.REGULAR,
                Depreciation.is_reversed == False,
            )
        )
        return result.scalar_one_or_none()

    async def _post_depreciation_gl(
        self,
        organization_id: UUID,
        depreciation_period: str,
        period_to: date,
        category_totals: Dict[UUID, Dict[str, Any]],
        run_id: UUID,
        posted_by: Optional[UUID] = None,
    ) -> Optional[UUID]:
        """Create GL entries for depreciation run grouped by category."""
        if not category_totals:
            return None

        # Get financial year and period
        fy = await self.fy_repo.get_by_date(organization_id, period_to)
        if not fy:
            raise ValueError(f"No financial year found for date {period_to}")
        if fy.is_closed:
            raise ValueError("Cannot post to a closed financial year")

        period = await self.period_repo.get_by_date(fy.id, period_to)
        if not period:
            raise ValueError(f"No period found for date {period_to}")
        if period.is_closed:
            raise ValueError("Cannot post to a closed period")

        # Build GL entry lines - one pair per category
        gl_lines: List[Dict[str, Any]] = []

        for cat_id, data in category_totals.items():
            category: AssetCategory = data["category"]
            dep_amount: Decimal = data["depreciation_amount"]

            if not category or dep_amount <= 0:
                continue

            if not category.gl_dep_expense_account_id:
                raise ValueError(
                    f"Depreciation expense account is not configured for category '{category.category_name}'"
                )
            if not category.gl_accum_dep_account_id:
                raise ValueError(
                    f"Accumulated depreciation account is not configured for category '{category.category_name}'"
                )

            # Debit: Depreciation Expense
            gl_lines.append({
                "account_id": category.gl_dep_expense_account_id,
                "debit_amount": dep_amount,
                "credit_amount": Decimal("0.00"),
                "narration": f"Depreciation for {depreciation_period} - {category.category_name}",
            })

            # Credit: Accumulated Depreciation
            gl_lines.append({
                "account_id": category.gl_accum_dep_account_id,
                "debit_amount": Decimal("0.00"),
                "credit_amount": dep_amount,
                "narration": f"Accumulated Depreciation for {depreciation_period} - {category.category_name}",
            })

        if not gl_lines:
            raise ValueError(
                f"No GL lines generated for depreciation run {depreciation_period}"
            )

        # Post GL entries
        entries = await self.gl_posting_service.post_from_source(
            source_type=GLEntrySourceType.DEPRECIATION,
            source_id=run_id,
            source_reference=f"DEP-{depreciation_period}",
            organization_id=organization_id,
            financial_year_id=fy.id,
            period_id=period.id,
            voucher_date=period_to,
            narration=f"Depreciation Run for {depreciation_period}",
            lines=gl_lines,
            posted_by=posted_by,
        )

        return entries[0].voucher_id if entries else None
