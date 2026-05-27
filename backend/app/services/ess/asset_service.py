"""Employee self-service asset queries."""

from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import AssetStatus
from app.models.fixed_assets.fixed_asset import FixedAsset
from app.schemas.ess.operations import ESSAssetResponse, ESSAssignedAssetsResponse


class ESSAssetService:
    """Read-only asset views for ESS."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_assigned_assets(self, employee_id: UUID) -> ESSAssignedAssetsResponse:
        result = await self.db.execute(
            select(FixedAsset)
            .where(
                FixedAsset.custodian_employee_id == employee_id,
                FixedAsset.deleted_at.is_(None),
                FixedAsset.status != AssetStatus.DISPOSED,
            )
            .options(
                selectinload(FixedAsset.category),
                selectinload(FixedAsset.location),
                selectinload(FixedAsset.department),
            )
            .order_by(FixedAsset.asset_code.asc())
        )
        assets = list(result.scalars().all())
        items = [
            ESSAssetResponse(
                id=asset.id,
                asset_code=asset.asset_code,
                asset_name=asset.asset_name,
                category=asset.category.category_name if asset.category else "Uncategorized",
                status=asset.status.value if hasattr(asset.status, "value") else str(asset.status),
                serial_number=asset.serial_number,
                assigned_date=asset.put_to_use_date or asset.acquisition_date,
                location=asset.location.name if asset.location else None,
                department=asset.department.name if asset.department else None,
                total_cost=float(asset.total_cost),
                warranty_expiry_date=asset.warranty_expiry_date,
                insurance_expiry_date=asset.insurance_expiry_date,
                return_required=asset.status in {AssetStatus.ACTIVE, AssetStatus.UNDER_MAINTENANCE},
            )
            for asset in assets
        ]
        total_asset_value = float(sum((asset.total_cost for asset in assets), Decimal("0")))
        return ESSAssignedAssetsResponse(
            items=items,
            total_assets=len(items),
            total_asset_value=total_asset_value,
        )
