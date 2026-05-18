"""Bulk Operations Service for Fixed Assets.

This service handles:
- Bulk asset import
- Bulk asset update
- Bulk transfer
- Bulk disposal
- Export to various formats
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fixed_assets.asset_category import AssetCategory
from app.models.fixed_assets.fixed_asset import FixedAsset
from app.models.fixed_assets.asset_transfer import AssetTransfer
from app.core.constants import AssetStatus, AssetTransferStatus, DepreciationMethod
from app.core.exceptions import ConcurrentModificationError
from app.schemas.fixed_assets.bulk_operations import (
    BulkAssetImportRequest,
    BulkAssetImportResponse,
    BulkAssetUpdateRequest,
    BulkAssetUpdateResponse,
    BulkTransferRequest,
    BulkTransferResponse,
    BulkDisposeRequest,
    BulkDisposeResponse,
    BulkImportError,
    ExportFilters,
)
from app.schemas.fixed_assets.fixed_asset import (
    FixedAssetCreate,
    AssetDisposeRequest,
)
from app.services.fixed_assets.asset_service import AssetService


class BulkOperationsService:
    """Service for bulk Fixed Asset operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.asset_service = AssetService(session)

    async def bulk_import(
        self,
        data: BulkAssetImportRequest,
        created_by: UUID,
    ) -> BulkAssetImportResponse:
        """
        Import multiple assets in bulk.

        Supports validation-only mode to check data before actual import.
        """
        errors: List[BulkImportError] = []
        created_ids: List[UUID] = []
        successful = 0
        failed = 0

        # Pre-fetch all categories for validation
        categories = await self._get_categories_map(data.organization_id)

        for idx, asset_row in enumerate(data.assets, start=1):
            try:
                # Validate category
                if asset_row.category_id not in categories:
                    errors.append(BulkImportError(
                        row=idx,
                        field="category_id",
                        error=f"Category {asset_row.category_id} not found",
                    ))
                    failed += 1
                    continue

                category = categories[asset_row.category_id]

                # Validate dates
                if asset_row.put_to_use_date and asset_row.put_to_use_date < asset_row.acquisition_date:
                    errors.append(BulkImportError(
                        row=idx,
                        field="put_to_use_date",
                        error="Put to use date cannot be before acquisition date",
                    ))
                    failed += 1
                    continue

                # Validate cost
                total_cost = asset_row.acquisition_cost + asset_row.installation_cost + asset_row.other_costs
                if total_cost <= 0:
                    errors.append(BulkImportError(
                        row=idx,
                        field="acquisition_cost",
                        error="Total cost must be greater than zero",
                    ))
                    failed += 1
                    continue

                # If validation only, just mark as successful
                if data.validation_only:
                    successful += 1
                    continue

                # Create the asset
                create_data = FixedAssetCreate(
                    organization_id=data.organization_id,
                    asset_name=asset_row.asset_name,
                    category_id=asset_row.category_id,
                    acquisition_date=asset_row.acquisition_date,
                    acquisition_cost=asset_row.acquisition_cost,
                    installation_cost=asset_row.installation_cost,
                    other_costs=asset_row.other_costs,
                    description=asset_row.description,
                    location_id=asset_row.location_id,
                    department_id=asset_row.department_id,
                    custodian_employee_id=asset_row.custodian_employee_id,
                    put_to_use_date=asset_row.put_to_use_date,
                    vendor_id=asset_row.vendor_id,
                    invoice_number=asset_row.invoice_number,
                    invoice_date=asset_row.invoice_date,
                    residual_value=asset_row.residual_value,
                    useful_life_months=asset_row.useful_life_months,
                    make=asset_row.make,
                    model=asset_row.model,
                    serial_number=asset_row.serial_number,
                    quantity=asset_row.quantity,
                )

                asset = await self.asset_service.create(create_data, created_by)
                created_ids.append(asset.id)
                successful += 1

            except Exception as e:
                errors.append(BulkImportError(
                    row=idx,
                    error=str(e),
                ))
                failed += 1

        return BulkAssetImportResponse(
            total=len(data.assets),
            successful=successful,
            failed=failed,
            validation_only=data.validation_only,
            errors=errors,
            created_asset_ids=created_ids,
        )

    async def bulk_update(
        self,
        data: BulkAssetUpdateRequest,
        updated_by: UUID,
    ) -> BulkAssetUpdateResponse:
        """
        Update multiple assets in bulk.

        Uses optimistic locking to prevent concurrent modification issues.
        """
        errors: List[BulkImportError] = []
        updated_ids: List[UUID] = []
        successful = 0
        failed = 0

        for idx, update_row in enumerate(data.assets, start=1):
            try:
                # Get asset
                asset = await self.asset_service.get(update_row.asset_id)
                if not asset:
                    errors.append(BulkImportError(
                        row=idx,
                        field="asset_id",
                        error=f"Asset {update_row.asset_id} not found",
                    ))
                    failed += 1
                    continue

                # Check organization
                if asset.organization_id != data.organization_id:
                    errors.append(BulkImportError(
                        row=idx,
                        field="asset_id",
                        error="Asset belongs to different organization",
                    ))
                    failed += 1
                    continue

                # Check version (optimistic locking)
                if asset.version != update_row.version:
                    errors.append(BulkImportError(
                        row=idx,
                        field="version",
                        error=f"Asset {asset.asset_code} was modified. Expected version {update_row.version}, found {asset.version}",
                    ))
                    failed += 1
                    continue

                if data.validation_only:
                    successful += 1
                    continue

                # Update fields
                update_data = update_row.model_dump(
                    exclude={"asset_id", "version"},
                    exclude_unset=True,
                )

                for field, value in update_data.items():
                    if value is not None:
                        setattr(asset, field, value)

                asset.updated_by = updated_by
                asset.version += 1

                await self.session.flush()
                updated_ids.append(asset.id)
                successful += 1

            except ConcurrentModificationError as e:
                errors.append(BulkImportError(
                    row=idx,
                    field="version",
                    error=str(e),
                ))
                failed += 1
            except Exception as e:
                errors.append(BulkImportError(
                    row=idx,
                    error=str(e),
                ))
                failed += 1

        if not data.validation_only:
            await self.session.flush()

        return BulkAssetUpdateResponse(
            total=len(data.assets),
            successful=successful,
            failed=failed,
            errors=errors,
            updated_asset_ids=updated_ids,
        )

    async def bulk_transfer(
        self,
        data: BulkTransferRequest,
        transferred_by: UUID,
    ) -> BulkTransferResponse:
        """
        Initiate bulk asset transfers.

        Creates pending transfer requests for all specified assets.
        """
        errors: List[BulkImportError] = []
        transfer_ids: List[UUID] = []
        successful = 0
        failed = 0

        for idx, transfer_row in enumerate(data.assets, start=1):
            try:
                # Get asset
                asset = await self.asset_service.get(transfer_row.asset_id)
                if not asset:
                    errors.append(BulkImportError(
                        row=idx,
                        field="asset_id",
                        error=f"Asset {transfer_row.asset_id} not found",
                    ))
                    failed += 1
                    continue

                # Check organization
                if asset.organization_id != data.organization_id:
                    errors.append(BulkImportError(
                        row=idx,
                        field="asset_id",
                        error="Asset belongs to different organization",
                    ))
                    failed += 1
                    continue

                # Check status
                if asset.status != AssetStatus.ACTIVE:
                    errors.append(BulkImportError(
                        row=idx,
                        field="asset_id",
                        error=f"Asset {asset.asset_code} is not active (status: {asset.status.value})",
                    ))
                    failed += 1
                    continue

                # Validate at least one transfer target is specified
                if not any([
                    transfer_row.to_location_id,
                    transfer_row.to_department_id,
                    transfer_row.to_custodian_id,
                ]):
                    errors.append(BulkImportError(
                        row=idx,
                        error="At least one transfer target must be specified",
                    ))
                    failed += 1
                    continue

                # Create transfer request
                reason = data.reason or transfer_row.reason or "Bulk transfer"
                transfer = AssetTransfer(
                    asset_id=transfer_row.asset_id,
                    transfer_date=data.transfer_date,
                    from_location_id=asset.location_id,
                    from_department_id=asset.department_id,
                    from_custodian_id=asset.custodian_employee_id,
                    to_location_id=transfer_row.to_location_id,
                    to_department_id=transfer_row.to_department_id,
                    to_custodian_id=transfer_row.to_custodian_id,
                    reason=reason,
                    status=AssetTransferStatus.PENDING,
                    requested_by=transferred_by,
                    created_by=transferred_by,
                )

                self.session.add(transfer)
                await self.session.flush()
                transfer_ids.append(transfer.id)
                successful += 1

            except Exception as e:
                errors.append(BulkImportError(
                    row=idx,
                    error=str(e),
                ))
                failed += 1

        await self.session.flush()

        return BulkTransferResponse(
            total=len(data.assets),
            successful=successful,
            failed=failed,
            errors=errors,
            transfer_ids=transfer_ids,
        )

    async def bulk_dispose(
        self,
        data: BulkDisposeRequest,
        disposed_by: UUID,
    ) -> BulkDisposeResponse:
        """
        Dispose multiple assets in bulk.

        Creates disposal entries for all specified assets.
        """
        errors: List[BulkImportError] = []
        disposed_ids: List[UUID] = []
        successful = 0
        failed = 0

        for idx, dispose_row in enumerate(data.assets, start=1):
            try:
                # Get asset
                asset = await self.asset_service.get(dispose_row.asset_id)
                if not asset:
                    errors.append(BulkImportError(
                        row=idx,
                        field="asset_id",
                        error=f"Asset {dispose_row.asset_id} not found",
                    ))
                    failed += 1
                    continue

                # Check organization
                if asset.organization_id != data.organization_id:
                    errors.append(BulkImportError(
                        row=idx,
                        field="asset_id",
                        error="Asset belongs to different organization",
                    ))
                    failed += 1
                    continue

                # Check status
                if asset.status not in [AssetStatus.ACTIVE, AssetStatus.FULLY_DEPRECIATED]:
                    errors.append(BulkImportError(
                        row=idx,
                        field="asset_id",
                        error=f"Asset {asset.asset_code} cannot be disposed (status: {asset.status.value})",
                    ))
                    failed += 1
                    continue

                # Dispose asset
                disposal_type = data.common_disposal_type or dispose_row.disposal_type
                dispose_request = AssetDisposeRequest(
                    disposal_date=data.disposal_date,
                    disposal_type=disposal_type,
                    disposal_value=dispose_row.disposal_value,
                    disposal_remarks=dispose_row.disposal_remarks or f"Bulk disposal",
                )

                await self.asset_service.dispose(
                    dispose_row.asset_id,
                    dispose_request,
                    disposed_by,
                )

                disposed_ids.append(dispose_row.asset_id)
                successful += 1

            except Exception as e:
                errors.append(BulkImportError(
                    row=idx,
                    error=str(e),
                ))
                failed += 1

        return BulkDisposeResponse(
            total=len(data.assets),
            successful=successful,
            failed=failed,
            errors=errors,
            disposed_asset_ids=disposed_ids,
        )

    async def export_assets(
        self,
        filters: ExportFilters,
        format: str = "xlsx",
    ) -> Tuple[List[dict], int]:
        """
        Export assets based on filters.

        Returns a list of asset dictionaries ready for export.
        """
        query = select(FixedAsset).where(
            FixedAsset.organization_id == filters.organization_id,
            FixedAsset.is_active == True,
        )

        if filters.category_id:
            query = query.where(FixedAsset.category_id == filters.category_id)
        if filters.location_id:
            query = query.where(FixedAsset.location_id == filters.location_id)
        if filters.department_id:
            query = query.where(FixedAsset.department_id == filters.department_id)
        if filters.status:
            query = query.where(FixedAsset.status == filters.status)
        if not filters.include_disposed:
            query = query.where(FixedAsset.status != AssetStatus.DISPOSED)
        if filters.acquisition_date_from:
            query = query.where(FixedAsset.acquisition_date >= filters.acquisition_date_from)
        if filters.acquisition_date_to:
            query = query.where(FixedAsset.acquisition_date <= filters.acquisition_date_to)

        result = await self.session.execute(query.order_by(FixedAsset.asset_code))
        assets = list(result.scalars().all())

        # Convert to export format
        export_data = []
        for asset in assets:
            export_data.append({
                "Asset Code": asset.asset_code,
                "Asset Name": asset.asset_name,
                "Description": asset.description,
                "Status": asset.status.value if asset.status else "",
                "Acquisition Date": asset.acquisition_date.isoformat() if asset.acquisition_date else "",
                "Acquisition Cost": float(asset.acquisition_cost),
                "Installation Cost": float(asset.installation_cost),
                "Other Costs": float(asset.other_costs),
                "Total Cost": float(asset.total_cost),
                "Residual Value": float(asset.residual_value),
                "Useful Life (Months)": asset.useful_life_months,
                "Depreciation Method": asset.depreciation_method.value if asset.depreciation_method else "",
                "Depreciation Rate": float(asset.depreciation_rate),
                "Accumulated Depreciation": float(asset.accumulated_depreciation),
                "WDV": float(asset.wdv_value),
                "Make": asset.make,
                "Model": asset.model,
                "Serial Number": asset.serial_number,
                "Quantity": asset.quantity,
            })

        return export_data, len(export_data)

    async def _get_categories_map(
        self,
        organization_id: UUID,
    ) -> dict:
        """Get all categories for an organization as a map."""
        result = await self.session.execute(
            select(AssetCategory).where(
                AssetCategory.organization_id == organization_id,
                AssetCategory.is_active == True,
            )
        )
        categories = result.scalars().all()
        return {cat.id: cat for cat in categories}
