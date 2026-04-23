"""IT Act Depreciation service for Fixed Assets module.

This service handles IT Act depreciation which is fundamentally different from
Companies Act depreciation:

1. Block-based: Assets are pooled into blocks based on asset type
2. Annual calculation: IT depreciation is calculated annually, not monthly
3. Half-rate first year: If asset is put to use for less than 180 days, half rate applies
4. Block extinguishment: When block WDV becomes nil/negative, any disposal proceeds are taxable
5. Additional depreciation: 20% additional depreciation for new manufacturing assets
"""

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
from app.models.fixed_assets.depreciation import (
    Depreciation,
    DepreciationRun,
    ITBlockSummary,
)
from app.core.constants import (
    AssetStatus,
    DepreciationBook,
    DepreciationType,
    ITActAssetBlock,
)
from app.schemas.fixed_assets.depreciation import (
    ITDepreciationRunCreate,
    ITBlockSummaryResponse,
    ITBlockDepreciationItem,
    ITDepreciationReportResponse,
    ITDepreciationScheduleItem,
    ITDepreciationScheduleResponse,
    AssetITDepreciationComparison,
    DepreciationComparisonResponse,
    IT_BLOCK_RATES,
    IT_BLOCK_NAMES,
)
from app.services.fixed_assets.asset_service import AssetService


class ITDepreciationService:
    """Service for IT Act depreciation operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.asset_service = AssetService(session)

    async def run_it_depreciation(
        self,
        data: ITDepreciationRunCreate,
        run_by: Optional[UUID] = None,
    ) -> DepreciationRun:
        """Run IT Act depreciation for all eligible assets for a financial year.

        IT Act depreciation is calculated annually at block level:
        1. Group assets by IT block
        2. Calculate block-level opening WDV
        3. Add acquisitions during the year
        4. Deduct disposals during the year
        5. Calculate depreciation on the net block value
        6. Apply half-rate for assets used less than 180 days
        """
        # Check if IT depreciation run already exists for this FY
        existing = await self._get_it_run_by_fy(
            data.organization_id, data.financial_year
        )
        if existing:
            raise ValueError(
                f"IT depreciation run already exists for FY {data.financial_year}"
            )

        # Parse financial year
        fy_start_year = int(data.financial_year.split("-")[0])
        fy_end_year = fy_start_year + 1
        fy_start = date(fy_start_year, 4, 1)  # Indian FY starts April 1
        fy_end = date(fy_end_year, 3, 31)

        # Create depreciation run
        dep_run = DepreciationRun(
            organization_id=data.organization_id,
            depreciation_book=DepreciationBook.IT_ACT,
            depreciation_period=data.financial_year,  # Using FY as period
            period_from=fy_start,
            period_to=fy_end,
            status="PROCESSING",
            run_started_at=datetime.now(timezone.utc),
            run_by=run_by,
            remarks=data.remarks,
        )
        if run_by:
            dep_run.created_by = run_by

        self.session.add(dep_run)
        await self.session.flush()

        # Get all active assets with IT block assigned
        assets = await self._get_assets_for_it_depreciation(
            data.organization_id, fy_end
        )

        # Group assets by block
        block_assets: Dict[ITActAssetBlock, List[FixedAsset]] = defaultdict(list)
        for asset in assets:
            if asset.it_act_block:
                block_assets[asset.it_act_block].append(asset)

        total_depreciation = Decimal("0.00")
        processed_count = 0
        skipped_count = 0

        # Process each block
        for block, block_asset_list in block_assets.items():
            block_result = await self._process_it_block(
                block=block,
                assets=block_asset_list,
                financial_year=data.financial_year,
                fy_start=fy_start,
                fy_end=fy_end,
                dep_run=dep_run,
                organization_id=data.organization_id,
                run_by=run_by,
            )

            total_depreciation += block_result["total_depreciation"]
            processed_count += block_result["processed_count"]
            skipped_count += block_result["skipped_count"]

        # Update run
        dep_run.total_assets = len(assets)
        dep_run.processed_assets = processed_count
        dep_run.skipped_assets = skipped_count
        dep_run.total_depreciation = total_depreciation
        dep_run.status = "COMPLETED"
        dep_run.run_completed_at = datetime.now(timezone.utc)

        await self.session.commit()
        await self.session.refresh(dep_run)
        return dep_run

    async def _process_it_block(
        self,
        block: ITActAssetBlock,
        assets: List[FixedAsset],
        financial_year: str,
        fy_start: date,
        fy_end: date,
        dep_run: DepreciationRun,
        organization_id: UUID,
        run_by: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """Process IT depreciation for a single block."""
        rate = IT_BLOCK_RATES.get(block, Decimal("15.00"))

        # Calculate block values
        opening_wdv = Decimal("0.00")
        additions = Decimal("0.00")
        disposals = Decimal("0.00")
        additional_dep_eligible = Decimal("0.00")

        total_depreciation = Decimal("0.00")
        processed_count = 0
        skipped_count = 0

        for asset in assets:
            # Check if IT depreciation already exists for this asset/FY
            existing = await self._get_it_depreciation_by_asset_fy(
                asset.id, financial_year
            )
            if existing:
                skipped_count += 1
                continue

            # Calculate opening WDV (from previous year or acquisition)
            asset_opening_wdv = asset.it_wdv_value

            # Check if acquired during this year
            is_new_acquisition = (
                asset.acquisition_date >= fy_start and
                asset.acquisition_date <= fy_end
            )

            if is_new_acquisition:
                additions += asset.total_cost
                asset_opening_wdv = Decimal("0.00")  # Opening is 0 for new assets
            else:
                opening_wdv += asset_opening_wdv

            # Check days in use for half-rate
            if asset.put_to_use_date:
                if asset.put_to_use_date >= fy_start:
                    days_in_use = (fy_end - asset.put_to_use_date).days + 1
                else:
                    days_in_use = 365
            else:
                days_in_use = (fy_end - asset.acquisition_date).days + 1

            # Determine applicable rate (half if < 180 days)
            applicable_rate = rate
            if is_new_acquisition and days_in_use < 180:
                applicable_rate = rate / 2

            # Calculate depreciation
            # For IT Act, depreciation = (Opening + Additions - Disposals) * Rate
            # But we calculate per asset and then aggregate
            depreciable_value = (
                asset_opening_wdv if not is_new_acquisition
                else asset.total_cost
            )

            dep_amount = (
                depreciable_value * applicable_rate / 100
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            # Additional depreciation for new manufacturing assets
            additional_dep = Decimal("0.00")
            if (
                asset.is_additional_depreciation_eligible and
                is_new_acquisition and
                asset.additional_depreciation_claimed < asset.total_cost * Decimal("0.20")
            ):
                # 20% additional depreciation in first year
                additional_dep = (asset.total_cost * Decimal("0.20")).quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                )
                if days_in_use < 180:
                    # Half additional dep if < 180 days
                    additional_dep = additional_dep / 2

                additional_dep_eligible += additional_dep

            # Calculate new values
            new_it_accumulated = asset.it_accumulated_depreciation + dep_amount + additional_dep
            new_it_wdv = asset.total_cost - new_it_accumulated
            if new_it_wdv < Decimal("0.00"):
                new_it_wdv = Decimal("0.00")

            # Create depreciation entry
            depreciation = Depreciation(
                asset_id=asset.id,
                depreciation_run_id=dep_run.id,
                depreciation_period=financial_year,
                period_from=fy_start,
                period_to=fy_end,
                days_in_period=days_in_use,
                opening_wdv=asset_opening_wdv if not is_new_acquisition else asset.total_cost,
                depreciation_rate=applicable_rate,
                depreciation_amount=dep_amount + additional_dep,
                accumulated_depreciation=new_it_accumulated,
                closing_wdv=new_it_wdv,
                depreciation_type=DepreciationType.REGULAR,
                depreciation_book=DepreciationBook.IT_ACT,
                is_posted=False,
                remarks=f"IT Block: {block.value}, Rate: {applicable_rate}%",
            )
            if run_by:
                depreciation.created_by = run_by

            self.session.add(depreciation)

            # Update asset IT values
            asset.it_accumulated_depreciation = new_it_accumulated
            asset.it_wdv_value = new_it_wdv
            asset.it_last_depreciation_date = fy_end
            asset.it_last_depreciation_fy = financial_year

            if additional_dep > 0:
                asset.additional_depreciation_claimed += additional_dep

            total_depreciation += dep_amount + additional_dep
            processed_count += 1

        # Create or update block summary
        block_summary = await self._get_or_create_block_summary(
            organization_id=organization_id,
            block=block,
            financial_year=financial_year,
        )

        block_summary.opening_wdv = opening_wdv
        block_summary.additions_during_year = additions
        block_summary.disposals_during_year = disposals
        block_summary.depreciation_rate = rate
        block_summary.depreciation_amount = total_depreciation - additional_dep_eligible
        block_summary.additional_depreciation = additional_dep_eligible
        block_summary.closing_wdv = opening_wdv + additions - disposals - total_depreciation
        if block_summary.closing_wdv < Decimal("0.00"):
            block_summary.closing_wdv = Decimal("0.00")
        block_summary.asset_count = len(assets)

        if run_by:
            block_summary.updated_by = run_by

        return {
            "total_depreciation": total_depreciation,
            "processed_count": processed_count,
            "skipped_count": skipped_count,
        }

    async def get_block_summary(
        self,
        organization_id: UUID,
        financial_year: str,
    ) -> List[ITBlockSummary]:
        """Get IT block summaries for a financial year."""
        result = await self.session.execute(
            select(ITBlockSummary)
            .where(
                ITBlockSummary.organization_id == organization_id,
                ITBlockSummary.financial_year == financial_year,
            )
            .order_by(ITBlockSummary.it_block)
        )
        return list(result.scalars().all())

    async def get_it_depreciation_report(
        self,
        organization_id: UUID,
        financial_year: str,
    ) -> ITDepreciationReportResponse:
        """Generate IT depreciation report for a financial year."""
        summaries = await self.get_block_summary(organization_id, financial_year)

        blocks = []
        total_opening = Decimal("0.00")
        total_additions = Decimal("0.00")
        total_disposals = Decimal("0.00")
        total_depreciation = Decimal("0.00")
        total_additional = Decimal("0.00")
        total_closing = Decimal("0.00")

        for summary in summaries:
            block_item = ITBlockDepreciationItem(
                it_block=summary.it_block,
                block_name=IT_BLOCK_NAMES.get(summary.it_block, str(summary.it_block)),
                depreciation_rate=summary.depreciation_rate,
                opening_wdv=summary.opening_wdv,
                additions=summary.additions_during_year,
                disposals=summary.disposals_during_year,
                total_before_depreciation=(
                    summary.opening_wdv +
                    summary.additions_during_year -
                    summary.disposals_during_year
                ),
                depreciation_amount=summary.depreciation_amount,
                additional_depreciation=summary.additional_depreciation,
                closing_wdv=summary.closing_wdv,
                asset_count=summary.asset_count,
            )
            blocks.append(block_item)

            total_opening += summary.opening_wdv
            total_additions += summary.additions_during_year
            total_disposals += summary.disposals_during_year
            total_depreciation += summary.depreciation_amount
            total_additional += summary.additional_depreciation
            total_closing += summary.closing_wdv

        return ITDepreciationReportResponse(
            organization_id=organization_id,
            financial_year=financial_year,
            blocks=blocks,
            total_opening_wdv=total_opening,
            total_additions=total_additions,
            total_disposals=total_disposals,
            total_depreciation=total_depreciation,
            total_additional_depreciation=total_additional,
            total_closing_wdv=total_closing,
        )

    async def get_depreciation_comparison(
        self,
        organization_id: UUID,
        financial_year: str,
        as_on_date: Optional[date] = None,
    ) -> DepreciationComparisonResponse:
        """Generate comparison report between Companies Act and IT Act depreciation."""
        if not as_on_date:
            fy_start_year = int(financial_year.split("-")[0])
            as_on_date = date(fy_start_year + 1, 3, 31)

        # Get all active assets
        result = await self.session.execute(
            select(FixedAsset)
            .options(selectinload(FixedAsset.category))
            .where(
                FixedAsset.organization_id == organization_id,
                FixedAsset.status.in_([
                    AssetStatus.ACTIVE,
                    AssetStatus.FULLY_DEPRECIATED
                ]),
            )
            .order_by(FixedAsset.asset_code)
        )
        assets = result.scalars().all()

        comparisons = []
        total_ca_accum = Decimal("0.00")
        total_it_accum = Decimal("0.00")
        total_ca_wdv = Decimal("0.00")
        total_it_wdv = Decimal("0.00")

        for asset in assets:
            comparison = AssetITDepreciationComparison(
                asset_id=asset.id,
                asset_code=asset.asset_code,
                asset_name=asset.asset_name,
                category_name=asset.category.category_name if asset.category else "",
                acquisition_date=asset.acquisition_date,
                acquisition_cost=asset.total_cost,
                ca_depreciation_method=asset.depreciation_method,
                ca_depreciation_rate=asset.depreciation_rate,
                ca_accumulated_depreciation=asset.accumulated_depreciation,
                ca_wdv=asset.wdv_value,
                it_block=asset.it_act_block,
                it_depreciation_rate=asset.it_act_rate,
                it_accumulated_depreciation=asset.it_accumulated_depreciation,
                it_wdv=asset.it_wdv_value,
                depreciation_difference=(
                    asset.accumulated_depreciation - asset.it_accumulated_depreciation
                ),
                wdv_difference=asset.wdv_value - asset.it_wdv_value,
            )
            comparisons.append(comparison)

            total_ca_accum += asset.accumulated_depreciation
            total_it_accum += asset.it_accumulated_depreciation
            total_ca_wdv += asset.wdv_value
            total_it_wdv += asset.it_wdv_value

        # Calculate deferred tax liability (approximate using 25% rate)
        tax_rate = Decimal("0.25")  # 25% corporate tax rate
        deferred_tax = abs(total_ca_accum - total_it_accum) * tax_rate

        return DepreciationComparisonResponse(
            organization_id=organization_id,
            as_on_date=as_on_date,
            financial_year=financial_year,
            assets=comparisons,
            total_ca_accumulated_depreciation=total_ca_accum,
            total_it_accumulated_depreciation=total_it_accum,
            total_depreciation_difference=total_ca_accum - total_it_accum,
            total_ca_wdv=total_ca_wdv,
            total_it_wdv=total_it_wdv,
            deferred_tax_liability=deferred_tax,
        )

    async def generate_it_depreciation_schedule(
        self,
        asset_id: UUID,
        years: int = 20,
    ) -> ITDepreciationScheduleResponse:
        """Generate projected IT depreciation schedule for an asset."""
        asset = await self.asset_service.get(asset_id)
        if not asset:
            raise ValueError("Asset not found")

        if not asset.it_act_block:
            raise ValueError("Asset does not have IT block assigned")

        rate = IT_BLOCK_RATES.get(asset.it_act_block, asset.it_act_rate)
        schedule = []
        current_it_wdv = asset.it_wdv_value

        # Determine start year
        if asset.it_last_depreciation_fy:
            start_year = int(asset.it_last_depreciation_fy.split("-")[0]) + 1
        else:
            start_year = asset.acquisition_date.year
            if asset.acquisition_date.month >= 4:
                start_year = asset.acquisition_date.year
            else:
                start_year = asset.acquisition_date.year - 1

        for i in range(years):
            fy_year = start_year + i
            fy_str = f"{fy_year}-{str(fy_year + 1)[-2:]}"

            # Check if block is extinguished
            if current_it_wdv <= Decimal("1.00"):
                schedule.append(ITDepreciationScheduleItem(
                    financial_year=fy_str,
                    opening_wdv=current_it_wdv,
                    depreciation_rate=rate,
                    depreciation_amount=Decimal("0.00"),
                    closing_wdv=current_it_wdv,
                    is_block_extinguished=True,
                ))
                break

            # Calculate depreciation
            dep_amount = (current_it_wdv * rate / 100).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

            new_wdv = current_it_wdv - dep_amount
            if new_wdv < Decimal("0.00"):
                new_wdv = Decimal("0.00")

            schedule.append(ITDepreciationScheduleItem(
                financial_year=fy_str,
                opening_wdv=current_it_wdv,
                depreciation_rate=rate,
                depreciation_amount=dep_amount,
                closing_wdv=new_wdv,
                is_block_extinguished=new_wdv <= Decimal("1.00"),
            ))

            current_it_wdv = new_wdv

        return ITDepreciationScheduleResponse(
            asset_id=asset.id,
            asset_code=asset.asset_code,
            asset_name=asset.asset_name,
            it_block=asset.it_act_block,
            it_block_name=IT_BLOCK_NAMES.get(asset.it_act_block, ""),
            total_cost=asset.total_cost,
            it_act_rate=rate,
            current_it_wdv=asset.it_wdv_value,
            current_it_accumulated_depreciation=asset.it_accumulated_depreciation,
            is_additional_depreciation_eligible=asset.is_additional_depreciation_eligible,
            additional_depreciation_claimed=asset.additional_depreciation_claimed,
            schedule=schedule,
        )

    async def finalize_block_summary(
        self,
        organization_id: UUID,
        financial_year: str,
        finalized_by: Optional[UUID] = None,
    ) -> List[ITBlockSummary]:
        """Finalize IT block summaries for a financial year."""
        summaries = await self.get_block_summary(organization_id, financial_year)

        for summary in summaries:
            summary.is_finalized = True
            summary.finalized_at = datetime.now(timezone.utc)
            summary.finalized_by = finalized_by

        await self.session.commit()
        return summaries

    async def get_run(self, run_id: UUID) -> Optional[DepreciationRun]:
        """Get depreciation run by ID."""
        result = await self.session.execute(
            select(DepreciationRun)
            .options(selectinload(DepreciationRun.entries))
            .where(DepreciationRun.id == run_id)
        )
        return result.scalar_one_or_none()

    async def list_it_runs(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[DepreciationRun], int]:
        """List IT Act depreciation runs."""
        query = select(DepreciationRun).where(
            DepreciationRun.organization_id == organization_id,
            DepreciationRun.depreciation_book == DepreciationBook.IT_ACT,
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

    async def _get_assets_for_it_depreciation(
        self,
        organization_id: UUID,
        as_on_date: date,
    ) -> List[FixedAsset]:
        """Get assets eligible for IT depreciation."""
        result = await self.session.execute(
            select(FixedAsset)
            .options(selectinload(FixedAsset.category))
            .where(
                FixedAsset.organization_id == organization_id,
                FixedAsset.status.in_([AssetStatus.ACTIVE, AssetStatus.FULLY_DEPRECIATED]),
                FixedAsset.it_act_block.isnot(None),
                FixedAsset.acquisition_date <= as_on_date,
            )
            .order_by(FixedAsset.it_act_block, FixedAsset.asset_code)
        )
        return list(result.scalars().all())

    async def _get_it_run_by_fy(
        self,
        organization_id: UUID,
        financial_year: str,
    ) -> Optional[DepreciationRun]:
        """Get IT depreciation run by financial year."""
        result = await self.session.execute(
            select(DepreciationRun).where(
                DepreciationRun.organization_id == organization_id,
                DepreciationRun.depreciation_period == financial_year,
                DepreciationRun.depreciation_book == DepreciationBook.IT_ACT,
            )
        )
        return result.scalar_one_or_none()

    async def _get_it_depreciation_by_asset_fy(
        self,
        asset_id: UUID,
        financial_year: str,
    ) -> Optional[Depreciation]:
        """Get IT depreciation entry by asset and financial year."""
        result = await self.session.execute(
            select(Depreciation).where(
                Depreciation.asset_id == asset_id,
                Depreciation.depreciation_period == financial_year,
                Depreciation.depreciation_book == DepreciationBook.IT_ACT,
                Depreciation.depreciation_type == DepreciationType.REGULAR,
                Depreciation.is_reversed == False,
            )
        )
        return result.scalar_one_or_none()

    async def _get_or_create_block_summary(
        self,
        organization_id: UUID,
        block: ITActAssetBlock,
        financial_year: str,
    ) -> ITBlockSummary:
        """Get or create IT block summary."""
        result = await self.session.execute(
            select(ITBlockSummary).where(
                ITBlockSummary.organization_id == organization_id,
                ITBlockSummary.it_block == block,
                ITBlockSummary.financial_year == financial_year,
            )
        )
        summary = result.scalar_one_or_none()

        if not summary:
            summary = ITBlockSummary(
                organization_id=organization_id,
                it_block=block,
                financial_year=financial_year,
                depreciation_rate=IT_BLOCK_RATES.get(block, Decimal("15.00")),
            )
            self.session.add(summary)
            await self.session.flush()

        return summary
