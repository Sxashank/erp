"""Reports service for Fixed Assets module."""

from datetime import date, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.fixed_assets.fixed_asset import FixedAsset
from app.models.fixed_assets.asset_category import AssetCategory
from app.models.fixed_assets.depreciation import Depreciation
from app.core.constants import AssetStatus, AssetType, DepreciationMethod
from app.schemas.fixed_assets.depreciation import (
    AssetRegisterItem,
    AssetRegisterResponse,
    DepreciationSummaryItem,
    DepreciationSummaryResponse,
)


class FAReportsService:
    """Service for Fixed Assets reports."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_asset_register(
        self,
        organization_id: UUID,
        as_on_date: date,
        category_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
        asset_type: Optional[AssetType] = None,
        status_filter: Optional[List[AssetStatus]] = None,
    ) -> AssetRegisterResponse:
        """Generate asset register report.

        This comprehensive report shows:
        - All assets with their cost, depreciation, and WDV
        - Category-wise grouping
        - Location-wise filtering
        - As-on-date values
        """
        query = (
            select(FixedAsset)
            .options(
                selectinload(FixedAsset.category),
                selectinload(FixedAsset.location),
                selectinload(FixedAsset.department),
            )
            .where(
                FixedAsset.organization_id == organization_id,
                FixedAsset.acquisition_date <= as_on_date,
            )
        )

        # Status filter
        if status_filter:
            query = query.where(FixedAsset.status.in_(status_filter))
        else:
            # Default: Active and Fully Depreciated assets
            query = query.where(
                FixedAsset.status.in_([
                    AssetStatus.ACTIVE,
                    AssetStatus.FULLY_DEPRECIATED,
                    AssetStatus.DISPOSED,
                ])
            )

        # Category filter
        if category_id:
            query = query.where(FixedAsset.category_id == category_id)

        # Location filter
        if location_id:
            query = query.where(FixedAsset.location_id == location_id)

        # Asset type filter (via category)
        if asset_type:
            query = query.join(AssetCategory).where(AssetCategory.asset_type == asset_type)

        result = await self.session.execute(
            query.order_by(FixedAsset.category_id, FixedAsset.asset_code)
        )
        assets = list(result.scalars().all())

        # Build asset register items
        items = []
        total_cost = Decimal("0.00")
        total_additions = Decimal("0.00")
        total_disposals = Decimal("0.00")
        total_revaluation = Decimal("0.00")
        total_depreciation = Decimal("0.00")
        total_accumulated = Decimal("0.00")
        total_wdv = Decimal("0.00")

        for asset in assets:
            # Calculate additions (assets acquired in current FY)
            additions = Decimal("0.00")
            if asset.acquisition_date >= date(as_on_date.year - (1 if as_on_date.month < 4 else 0), 4, 1):
                additions = asset.total_cost

            # Calculate disposals
            disposals = Decimal("0.00")
            if asset.status == AssetStatus.DISPOSED and asset.disposal_date:
                if asset.disposal_date <= as_on_date:
                    disposals = asset.total_cost

            # Get depreciation for the current period
            period_dep = await self._get_period_depreciation(
                asset.id, as_on_date
            )

            item = AssetRegisterItem(
                id=asset.id,
                asset_code=asset.asset_code,
                asset_name=asset.asset_name,
                category_code=asset.category.category_code if asset.category else "",
                category_name=asset.category.category_name if asset.category else "",
                location_name=asset.location.name if asset.location else None,
                department_name=asset.department.name if asset.department else None,
                acquisition_date=asset.acquisition_date,
                acquisition_cost=asset.total_cost,
                additions=additions,
                disposals=disposals,
                revaluation=asset.revaluation_amount,
                depreciation_for_period=period_dep,
                accumulated_depreciation=asset.accumulated_depreciation,
                wdv_value=asset.wdv_value,
                status=asset.status.value,
            )
            items.append(item)

            total_cost += asset.total_cost
            total_additions += additions
            total_disposals += disposals
            total_revaluation += asset.revaluation_amount
            total_depreciation += period_dep
            total_accumulated += asset.accumulated_depreciation
            total_wdv += asset.wdv_value

        return AssetRegisterResponse(
            organization_id=organization_id,
            as_on_date=as_on_date,
            total_cost=total_cost,
            total_additions=total_additions,
            total_disposals=total_disposals,
            total_revaluation=total_revaluation,
            total_depreciation=total_depreciation,
            total_accumulated_depreciation=total_accumulated,
            total_wdv=total_wdv,
            assets=items,
        )

    async def get_depreciation_summary(
        self,
        organization_id: UUID,
        depreciation_period: str,
    ) -> DepreciationSummaryResponse:
        """Generate depreciation summary report by category."""
        # Parse period
        year, month = map(int, depreciation_period.split("-"))
        period_from = date(year, month, 1)
        if month == 12:
            period_to = date(year + 1, 1, 1)
        else:
            period_to = date(year, month + 1, 1)
        period_to = date(period_to.year, period_to.month, 1) - timedelta(days=1)

        # Get depreciation entries grouped by category
        result = await self.session.execute(
            select(
                AssetCategory.id,
                AssetCategory.category_code,
                AssetCategory.category_name,
                func.count(Depreciation.id).label("asset_count"),
                func.sum(FixedAsset.total_cost).label("total_cost"),
                func.sum(Depreciation.depreciation_amount).label("depreciation"),
                func.sum(Depreciation.accumulated_depreciation).label("accumulated"),
                func.sum(Depreciation.closing_wdv).label("closing_wdv"),
            )
            .join(FixedAsset, Depreciation.asset_id == FixedAsset.id)
            .join(AssetCategory, FixedAsset.category_id == AssetCategory.id)
            .where(
                FixedAsset.organization_id == organization_id,
                Depreciation.depreciation_period == depreciation_period,
            )
            .group_by(
                AssetCategory.id,
                AssetCategory.category_code,
                AssetCategory.category_name,
            )
            .order_by(AssetCategory.category_code)
        )
        rows = result.all()

        items = []
        total_assets = 0
        total_depreciation = Decimal("0.00")

        for row in rows:
            item = DepreciationSummaryItem(
                category_id=row.id,
                category_code=row.category_code,
                category_name=row.category_name,
                asset_count=row.asset_count,
                total_cost=row.total_cost or Decimal("0.00"),
                total_depreciation=row.depreciation or Decimal("0.00"),
                accumulated_depreciation=row.accumulated or Decimal("0.00"),
                closing_wdv=row.closing_wdv or Decimal("0.00"),
            )
            items.append(item)
            total_assets += row.asset_count
            total_depreciation += row.depreciation or Decimal("0.00")

        return DepreciationSummaryResponse(
            organization_id=organization_id,
            depreciation_period=depreciation_period,
            period_from=period_from,
            period_to=period_to,
            total_assets=total_assets,
            total_depreciation=total_depreciation,
            by_category=items,
        )

    async def get_nbs7_schedule(
        self,
        organization_id: UUID,
        financial_year: str,
        quarter: int,
    ) -> dict:
        """Generate NBS-7 Schedule for quarterly regulatory filing.

        NBS-7 is a schedule required to be submitted quarterly by NBFCs
        showing fixed assets details as per RBI format.
        """
        # Parse financial year
        fy_start_year = int(financial_year.split("-")[0])

        # Calculate quarter dates
        quarter_dates = {
            1: (date(fy_start_year, 4, 1), date(fy_start_year, 6, 30)),  # Q1: Apr-Jun
            2: (date(fy_start_year, 7, 1), date(fy_start_year, 9, 30)),  # Q2: Jul-Sep
            3: (date(fy_start_year, 10, 1), date(fy_start_year, 12, 31)),  # Q3: Oct-Dec
            4: (date(fy_start_year + 1, 1, 1), date(fy_start_year + 1, 3, 31)),  # Q4: Jan-Mar
        }

        quarter_start, quarter_end = quarter_dates.get(quarter, (None, None))
        if not quarter_start:
            raise ValueError(f"Invalid quarter: {quarter}")

        # Get assets as on quarter end
        result = await self.session.execute(
            select(FixedAsset)
            .options(selectinload(FixedAsset.category))
            .where(
                FixedAsset.organization_id == organization_id,
                FixedAsset.status.in_([AssetStatus.ACTIVE, AssetStatus.FULLY_DEPRECIATED]),
                FixedAsset.acquisition_date <= quarter_end,
            )
        )
        assets = list(result.scalars().all())

        # Group by NBS-7 categories
        nbs7_categories = {
            "premises": {
                "name": "Premises",
                "types": [AssetType.TANGIBLE],
                "prefixes": ["BLDG", "LAND", "PREM"],
            },
            "furniture_fixtures": {
                "name": "Furniture and Fixtures",
                "types": [AssetType.TANGIBLE],
                "prefixes": ["FURN", "FIX"],
            },
            "vehicles": {
                "name": "Vehicles",
                "types": [AssetType.TANGIBLE],
                "prefixes": ["VEH", "CAR", "BIKE"],
            },
            "office_equipment": {
                "name": "Office Equipment",
                "types": [AssetType.TANGIBLE],
                "prefixes": ["OFFC", "EQUIP", "COMP"],
            },
            "other_assets": {
                "name": "Other Fixed Assets",
                "types": [AssetType.TANGIBLE],
                "prefixes": [],  # Catch-all
            },
            "intangible": {
                "name": "Intangible Assets",
                "types": [AssetType.INTANGIBLE, AssetType.RIGHT_OF_USE],
                "prefixes": [],
            },
        }

        schedule_data = []
        grand_total_cost = Decimal("0.00")
        grand_total_additions = Decimal("0.00")
        grand_total_deductions = Decimal("0.00")
        grand_total_depreciation = Decimal("0.00")
        grand_total_wdv = Decimal("0.00")

        for cat_key, cat_config in nbs7_categories.items():
            cat_assets = []
            for asset in assets:
                if asset.category:
                    # Check asset type
                    type_match = asset.category.asset_type in cat_config["types"]
                    # Check prefix match (if any prefixes defined)
                    prefix_match = (
                        not cat_config["prefixes"] or
                        any(asset.category.category_code.upper().startswith(p) for p in cat_config["prefixes"])
                    )

                    if type_match and prefix_match:
                        cat_assets.append(asset)
                        # Remove from main list to avoid double counting
                        if asset in assets:
                            pass  # Don't remove, just track

            # Calculate category totals
            total_cost = sum(a.total_cost for a in cat_assets)
            # Additions during quarter
            additions = sum(
                a.total_cost for a in cat_assets
                if a.acquisition_date >= quarter_start and a.acquisition_date <= quarter_end
            )
            # Deductions (disposals during quarter)
            deductions = sum(
                a.total_cost for a in cat_assets
                if a.status == AssetStatus.DISPOSED and
                a.disposal_date and
                a.disposal_date >= quarter_start and a.disposal_date <= quarter_end
            )
            # Depreciation during quarter
            depreciation = Decimal("0.00")
            for asset in cat_assets:
                dep = await self._get_quarter_depreciation(asset.id, quarter_start, quarter_end)
                depreciation += dep

            total_wdv = sum(a.wdv_value for a in cat_assets)

            schedule_data.append({
                "category": cat_config["name"],
                "opening_balance": total_cost - additions + deductions,
                "additions": additions,
                "deductions": deductions,
                "total_cost": total_cost,
                "depreciation_for_quarter": depreciation,
                "total_depreciation": sum(a.accumulated_depreciation for a in cat_assets),
                "closing_wdv": total_wdv,
                "asset_count": len(cat_assets),
            })

            grand_total_cost += total_cost
            grand_total_additions += additions
            grand_total_deductions += deductions
            grand_total_depreciation += depreciation
            grand_total_wdv += total_wdv

        return {
            "organization_id": str(organization_id),
            "financial_year": financial_year,
            "quarter": quarter,
            "quarter_start": quarter_start.isoformat(),
            "quarter_end": quarter_end.isoformat(),
            "schedule": schedule_data,
            "grand_totals": {
                "total_cost": float(grand_total_cost),
                "total_additions": float(grand_total_additions),
                "total_deductions": float(grand_total_deductions),
                "total_depreciation_for_quarter": float(grand_total_depreciation),
                "total_wdv": float(grand_total_wdv),
            },
            "generated_at": date.today().isoformat(),
        }

    async def _get_period_depreciation(
        self,
        asset_id: UUID,
        as_on_date: date,
    ) -> Decimal:
        """Get depreciation for current financial year up to as_on_date."""
        # Determine FY start
        if as_on_date.month >= 4:
            fy_start = date(as_on_date.year, 4, 1)
        else:
            fy_start = date(as_on_date.year - 1, 4, 1)

        result = await self.session.execute(
            select(func.coalesce(func.sum(Depreciation.depreciation_amount), 0))
            .where(
                Depreciation.asset_id == asset_id,
                Depreciation.period_to >= fy_start,
                Depreciation.period_to <= as_on_date,
            )
        )
        return result.scalar_one()

    async def _get_quarter_depreciation(
        self,
        asset_id: UUID,
        quarter_start: date,
        quarter_end: date,
    ) -> Decimal:
        """Get depreciation for a specific quarter."""
        result = await self.session.execute(
            select(func.coalesce(func.sum(Depreciation.depreciation_amount), 0))
            .where(
                Depreciation.asset_id == asset_id,
                Depreciation.period_to >= quarter_start,
                Depreciation.period_to <= quarter_end,
            )
        )
        return result.scalar_one()
