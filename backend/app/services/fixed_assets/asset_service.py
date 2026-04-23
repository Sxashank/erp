"""Fixed Asset service."""

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.fixed_assets.asset_category import AssetCategory
from app.models.fixed_assets.fixed_asset import FixedAsset
from app.models.fixed_assets.asset_transfer import AssetTransfer
from app.models.fixed_assets.asset_revaluation import AssetRevaluation
from app.core.constants import (
    AssetStatus,
    AssetDisposalType,
    AssetTransferStatus,
    RevaluationType,
    DepreciationMethod,
    GLEntrySourceType,
    PartyType,
)
from app.schemas.fixed_assets.fixed_asset import (
    FixedAssetCreate,
    FixedAssetUpdate,
    AssetCapitalizeRequest,
    AssetDisposeRequest,
    AssetTransferRequest,
    AssetRevalueRequest,
    AssetImpairRequest,
)
from app.services.finance.gl_posting_service import GLPostingService
from app.repositories.finance.financial_year_repo import (
    FinancialYearRepository,
    FinancialPeriodRepository,
)
from app.services.common.audit_service import AuditService, model_to_dict
from app.models.common.audit_log import EntityType, AuditAction
from app.core.optimistic_lock import increment_version
from app.core.exceptions import ConcurrentModificationError


class AssetService:
    """Service for Fixed Asset operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.gl_posting_service = GLPostingService(session)
        self.fy_repo = FinancialYearRepository(session)
        self.period_repo = FinancialPeriodRepository(session)
        self.audit_service = AuditService(session)

    async def create(
        self,
        data: FixedAssetCreate,
        created_by: Optional[UUID] = None,
    ) -> FixedAsset:
        """Create a new fixed asset."""
        # Get category for defaults
        category = await self._get_category(data.category_id)
        if not category:
            raise ValueError("Asset category not found")
        if category.organization_id != data.organization_id:
            raise ValueError("Category belongs to different organization")

        # Generate asset code
        asset_code = await self._generate_asset_code(
            data.organization_id, category.category_code
        )

        # Calculate total cost
        total_cost = data.acquisition_cost + data.installation_cost + data.other_costs

        # Use category defaults if not provided
        useful_life_months = data.useful_life_months or (category.useful_life_years * 12)
        depreciation_method = data.depreciation_method or category.depreciation_method

        # Calculate depreciation rate
        if data.depreciation_rate:
            depreciation_rate = data.depreciation_rate
        elif depreciation_method == DepreciationMethod.SLM:
            depreciation_rate = category.depreciation_rate_slm
        elif depreciation_method == DepreciationMethod.WDV:
            depreciation_rate = category.depreciation_rate_wdv
        else:
            depreciation_rate = Decimal("0.00")

        # Calculate residual value
        if data.residual_value is not None:
            residual_value = data.residual_value
        else:
            residual_value = total_cost * category.residual_value_pct / 100

        # Calculate depreciable value
        depreciable_value = total_cost - residual_value

        # Create asset
        asset_data = data.model_dump(exclude={"residual_value", "useful_life_months", "depreciation_method", "depreciation_rate"})
        asset_data.update({
            "asset_code": asset_code,
            "total_cost": total_cost,
            "residual_value": residual_value,
            "depreciable_value": depreciable_value,
            "useful_life_months": useful_life_months,
            "depreciation_method": depreciation_method,
            "depreciation_rate": depreciation_rate,
            "wdv_value": total_cost,  # Initially WDV = total cost
            "accumulated_depreciation": Decimal("0.00"),
            "status": AssetStatus.DRAFT,
        })
        if created_by:
            asset_data["created_by"] = created_by

        asset = FixedAsset(**asset_data)
        self.session.add(asset)
        await self.session.commit()
        await self.session.refresh(asset)

        # Audit trail - log creation
        await self.audit_service.log_create(
            organization_id=asset.organization_id,
            entity_type=EntityType.FIXED_ASSET.value,
            entity_id=asset.id,
            entity_reference=asset.asset_code,
            new_values=model_to_dict(asset),
            user_id=created_by or asset.created_by,
        )

        return asset

    async def get(self, id: UUID) -> Optional[FixedAsset]:
        """Get asset by ID."""
        result = await self.session.execute(
            select(FixedAsset)
            .options(
                selectinload(FixedAsset.category),
                selectinload(FixedAsset.location),
                selectinload(FixedAsset.department),
                selectinload(FixedAsset.vendor),
            )
            .where(FixedAsset.id == id, FixedAsset.is_active == True)
        )
        return result.scalar_one_or_none()

    async def update(
        self,
        id: UUID,
        data: FixedAssetUpdate,
        updated_by: Optional[UUID] = None,
        expected_version: Optional[int] = None,
    ) -> Optional[FixedAsset]:
        """Update a fixed asset.

        Args:
            id: Asset UUID
            data: Update data
            updated_by: User performing the update
            expected_version: If provided, enables optimistic locking.
                              Update will fail if current version doesn't match.
        """
        asset = await self.get(id)
        if not asset:
            return None

        # Optimistic locking check
        if expected_version is not None and asset.version != expected_version:
            raise ConcurrentModificationError(
                f"Asset {asset.asset_code} was modified by another user. "
                "Please refresh and try again."
            )

        # Capture old values for audit trail
        old_values = model_to_dict(asset)

        # Only allow updates on DRAFT assets for core fields
        if asset.status != AssetStatus.DRAFT:
            # For active assets, only allow certain field updates
            allowed_fields = {
                "asset_name", "description", "location_id", "department_id",
                "custodian_employee_id", "make", "model", "serial_number",
                "warranty_start_date", "warranty_expiry_date",
                "insurance_policy_number", "insurance_provider",
                "insurance_expiry_date", "insured_value",
                "amc_vendor_id", "amc_start_date", "amc_expiry_date", "amc_value",
                "tags",
            }
            update_data = {
                k: v for k, v in data.model_dump(exclude_unset=True).items()
                if k in allowed_fields
            }
        else:
            update_data = data.model_dump(exclude_unset=True)

        # Update fields
        for key, value in update_data.items():
            setattr(asset, key, value)
        if updated_by:
            asset.updated_by = updated_by

        # Increment version for optimistic locking
        increment_version(asset)

        await self.session.commit()
        await self.session.refresh(asset)

        # Audit trail - log update
        await self.audit_service.log_update(
            organization_id=asset.organization_id,
            entity_type=EntityType.FIXED_ASSET.value,
            entity_id=asset.id,
            entity_reference=asset.asset_code,
            old_values=old_values,
            new_values=model_to_dict(asset),
            user_id=updated_by or asset.updated_by,
        )

        return asset

    async def delete(
        self,
        id: UUID,
        deleted_by: Optional[UUID] = None,
    ) -> bool:
        """Soft delete an asset (only DRAFT assets)."""
        asset = await self.get(id)
        if not asset:
            return False

        if asset.status != AssetStatus.DRAFT:
            raise ValueError("Only draft assets can be deleted")

        # Capture old values for audit trail
        old_values = model_to_dict(asset)
        org_id = asset.organization_id
        asset_code = asset.asset_code
        asset_id = asset.id

        asset.soft_delete(deleted_by)
        await self.session.commit()

        # Audit trail - log deletion
        await self.audit_service.log_delete(
            organization_id=org_id,
            entity_type=EntityType.FIXED_ASSET.value,
            entity_id=asset_id,
            entity_reference=asset_code,
            old_values=old_values,
            user_id=deleted_by,
        )

        return True

    async def capitalize(
        self,
        id: UUID,
        data: AssetCapitalizeRequest,
        capitalized_by: Optional[UUID] = None,
    ) -> FixedAsset:
        """Capitalize an asset (move from DRAFT to ACTIVE)."""
        asset = await self.get(id)
        if not asset:
            raise ValueError("Asset not found")

        if asset.status != AssetStatus.DRAFT:
            raise ValueError("Only draft assets can be capitalized")

        # Capture old values for audit trail
        old_values = model_to_dict(asset)

        # Validate total cost meets capitalization threshold
        category = await self._get_category(asset.category_id)
        if category and asset.total_cost < category.capitalization_threshold:
            raise ValueError(
                f"Asset value {asset.total_cost} is below capitalization threshold {category.capitalization_threshold}"
            )

        # Update asset
        asset.status = AssetStatus.ACTIVE
        if data.put_to_use_date:
            asset.put_to_use_date = data.put_to_use_date
        asset.depreciation_start_date = data.depreciation_start_date or data.put_to_use_date or data.capitalization_date

        if capitalized_by:
            asset.updated_by = capitalized_by

        # Create GL voucher for capitalization
        # Dr Asset Account, Cr Vendor Payable/Bank
        await self._post_capitalization_gl(
            asset=asset,
            category=category,
            capitalization_date=data.capitalization_date or data.put_to_use_date or date.today(),
            posted_by=capitalized_by,
        )

        await self.session.commit()
        await self.session.refresh(asset)

        # Audit trail - log capitalization
        await self.audit_service.log_action(
            organization_id=asset.organization_id,
            entity_type=EntityType.FIXED_ASSET.value,
            entity_id=asset.id,
            entity_reference=asset.asset_code,
            action=AuditAction.CAPITALIZE.value,
            user_id=capitalized_by or asset.updated_by,
            old_values=old_values,
            new_values=model_to_dict(asset),
            change_reason=f"Asset capitalized on {data.capitalization_date or date.today()}",
        )

        return asset

    async def dispose(
        self,
        id: UUID,
        data: AssetDisposeRequest,
        disposed_by: Optional[UUID] = None,
    ) -> FixedAsset:
        """Dispose an asset."""
        asset = await self.get(id)
        if not asset:
            raise ValueError("Asset not found")

        if asset.status not in [AssetStatus.ACTIVE, AssetStatus.FULLY_DEPRECIATED]:
            raise ValueError("Only active or fully depreciated assets can be disposed")

        # Capture old values for audit trail
        old_values = model_to_dict(asset)

        # Calculate gain/loss
        book_value = asset.wdv_value
        disposal_gain_loss = data.disposal_value - book_value

        # Update asset
        asset.status = AssetStatus.DISPOSED
        asset.disposal_date = data.disposal_date
        asset.disposal_type = data.disposal_type
        asset.disposal_value = data.disposal_value
        asset.disposal_gain_loss = disposal_gain_loss
        asset.disposal_remarks = data.disposal_remarks

        if disposed_by:
            asset.updated_by = disposed_by

        # Create GL voucher for disposal
        # Dr Accumulated Depreciation (full amount)
        # Dr Bank/Cash (disposal value)
        # Dr/Cr Gain/Loss on Disposal
        # Cr Asset Account (original cost)
        category = await self._get_category(asset.category_id)
        await self._post_disposal_gl(
            asset=asset,
            category=category,
            disposal_date=data.disposal_date,
            disposal_value=data.disposal_value,
            disposal_gain_loss=disposal_gain_loss,
            posted_by=disposed_by,
        )

        await self.session.commit()
        await self.session.refresh(asset)

        # Audit trail - log disposal
        await self.audit_service.log_action(
            organization_id=asset.organization_id,
            entity_type=EntityType.FIXED_ASSET.value,
            entity_id=asset.id,
            entity_reference=asset.asset_code,
            action=AuditAction.DISPOSE.value,
            user_id=disposed_by or asset.updated_by,
            old_values=old_values,
            new_values=model_to_dict(asset),
            change_reason=f"Asset disposed via {data.disposal_type.value} on {data.disposal_date}. {data.disposal_remarks or ''}",
        )

        return asset

    async def transfer(
        self,
        id: UUID,
        data: AssetTransferRequest,
        transferred_by: Optional[UUID] = None,
    ) -> AssetTransfer:
        """Initiate asset transfer."""
        asset = await self.get(id)
        if not asset:
            raise ValueError("Asset not found")

        if asset.status != AssetStatus.ACTIVE:
            raise ValueError("Only active assets can be transferred")

        # Create transfer record
        transfer = AssetTransfer(
            asset_id=id,
            transfer_date=data.transfer_date,
            from_location_id=asset.location_id,
            from_department_id=asset.department_id,
            from_custodian_id=asset.custodian_employee_id,
            to_location_id=data.to_location_id,
            to_department_id=data.to_department_id,
            to_custodian_id=data.to_custodian_id,
            reason=data.reason,
            status=AssetTransferStatus.PENDING,
            requested_by=transferred_by,
        )
        if transferred_by:
            transfer.created_by = transferred_by

        self.session.add(transfer)
        await self.session.commit()
        await self.session.refresh(transfer)

        # Audit trail - log transfer request
        await self.audit_service.log_action(
            organization_id=asset.organization_id,
            entity_type=EntityType.FIXED_ASSET.value,
            entity_id=asset.id,
            entity_reference=asset.asset_code,
            action=AuditAction.TRANSFER.value,
            user_id=transferred_by,
            old_values={"location_id": str(asset.location_id) if asset.location_id else None,
                       "department_id": str(asset.department_id) if asset.department_id else None,
                       "custodian_employee_id": str(asset.custodian_employee_id) if asset.custodian_employee_id else None},
            new_values={"to_location_id": str(data.to_location_id) if data.to_location_id else None,
                       "to_department_id": str(data.to_department_id) if data.to_department_id else None,
                       "to_custodian_id": str(data.to_custodian_id) if data.to_custodian_id else None,
                       "transfer_status": "PENDING"},
            change_reason=f"Transfer requested: {data.reason or 'No reason provided'}",
        )

        return transfer

    async def complete_transfer(
        self,
        transfer_id: UUID,
        completed_by: Optional[UUID] = None,
    ) -> AssetTransfer:
        """Complete an approved transfer."""
        result = await self.session.execute(
            select(AssetTransfer).where(AssetTransfer.id == transfer_id)
        )
        transfer = result.scalar_one_or_none()
        if not transfer:
            raise ValueError("Transfer not found")

        if transfer.status != AssetTransferStatus.APPROVED:
            raise ValueError("Transfer must be approved before completion")

        # Update asset
        asset = await self.get(transfer.asset_id)
        if asset:
            asset.location_id = transfer.to_location_id
            asset.department_id = transfer.to_department_id
            asset.custodian_employee_id = transfer.to_custodian_id
            if completed_by:
                asset.updated_by = completed_by

        # Complete transfer
        transfer.status = AssetTransferStatus.COMPLETED
        transfer.completed_by = completed_by
        from datetime import datetime, timezone
        transfer.completed_at = datetime.now(timezone.utc)

        await self.session.commit()
        await self.session.refresh(transfer)
        return transfer

    async def revalue(
        self,
        id: UUID,
        data: AssetRevalueRequest,
        revalued_by: Optional[UUID] = None,
    ) -> AssetRevaluation:
        """Revalue an asset."""
        asset = await self.get(id)
        if not asset:
            raise ValueError("Asset not found")

        if asset.status != AssetStatus.ACTIVE:
            raise ValueError("Only active assets can be revalued")

        # Capture old values for audit trail
        old_values = model_to_dict(asset)

        # Determine revaluation type
        previous_value = asset.wdv_value
        revaluation_amount = abs(data.new_value - previous_value)
        if data.new_value > previous_value:
            revaluation_type = RevaluationType.INCREASE
        else:
            revaluation_type = RevaluationType.DECREASE

        # Create revaluation record
        revaluation = AssetRevaluation(
            asset_id=id,
            revaluation_date=data.revaluation_date,
            revaluation_type=revaluation_type,
            previous_value=previous_value,
            new_value=data.new_value,
            revaluation_amount=revaluation_amount,
            previous_accumulated_depreciation=asset.accumulated_depreciation,
            new_accumulated_depreciation=asset.accumulated_depreciation,  # No change
            valuer_name=data.valuer_name,
            valuation_report_number=data.valuation_report_number,
            valuation_report_date=data.valuation_report_date,
            valuation_method=data.valuation_method,
            reason=data.reason,
        )
        if revalued_by:
            revaluation.created_by = revalued_by

        # Update asset
        asset.wdv_value = data.new_value
        asset.revaluation_amount += revaluation_amount if revaluation_type == RevaluationType.INCREASE else -revaluation_amount
        if revalued_by:
            asset.updated_by = revalued_by

        # Create GL voucher for revaluation
        # If increase: Dr Asset, Cr Revaluation Reserve
        # If decrease: Dr Revaluation Reserve (or P&L), Cr Asset
        category = await self._get_category(asset.category_id)
        voucher_id = await self._post_revaluation_gl(
            asset=asset,
            category=category,
            revaluation_date=data.revaluation_date,
            revaluation_type=revaluation_type,
            revaluation_amount=revaluation_amount,
            posted_by=revalued_by,
        )
        revaluation.voucher_id = voucher_id

        self.session.add(revaluation)
        await self.session.commit()
        await self.session.refresh(revaluation)

        # Audit trail - log revaluation
        await self.audit_service.log_action(
            organization_id=asset.organization_id,
            entity_type=EntityType.FIXED_ASSET.value,
            entity_id=asset.id,
            entity_reference=asset.asset_code,
            action=AuditAction.REVALUE.value,
            user_id=revalued_by or asset.updated_by,
            old_values=old_values,
            new_values=model_to_dict(asset),
            change_reason=f"Asset revalued ({revaluation_type.value}) from {previous_value} to {data.new_value}. Valuer: {data.valuer_name or 'N/A'}. {data.reason or ''}",
        )

        return revaluation

    async def impair(
        self,
        id: UUID,
        data: AssetImpairRequest,
        impaired_by: Optional[UUID] = None,
    ) -> AssetRevaluation:
        """Record impairment on an asset."""
        asset = await self.get(id)
        if not asset:
            raise ValueError("Asset not found")

        if asset.status != AssetStatus.ACTIVE:
            raise ValueError("Only active assets can be impaired")

        if data.impairment_amount > asset.wdv_value:
            raise ValueError("Impairment amount cannot exceed book value")

        # Capture old values for audit trail
        old_values = model_to_dict(asset)

        # Create revaluation record (impairment)
        previous_value = asset.wdv_value
        new_value = previous_value - data.impairment_amount

        revaluation = AssetRevaluation(
            asset_id=id,
            revaluation_date=data.impairment_date,
            revaluation_type=RevaluationType.IMPAIRMENT,
            previous_value=previous_value,
            new_value=new_value,
            revaluation_amount=data.impairment_amount,
            previous_accumulated_depreciation=asset.accumulated_depreciation,
            new_accumulated_depreciation=asset.accumulated_depreciation,
            reason=data.reason,
        )
        if impaired_by:
            revaluation.created_by = impaired_by

        # Update asset
        asset.wdv_value = new_value
        asset.impairment_amount += data.impairment_amount
        if impaired_by:
            asset.updated_by = impaired_by

        # Create GL voucher for impairment
        # Dr Impairment Loss, Cr Asset
        category = await self._get_category(asset.category_id)
        voucher_id = await self._post_impairment_gl(
            asset=asset,
            category=category,
            impairment_date=data.impairment_date,
            impairment_amount=data.impairment_amount,
            posted_by=impaired_by,
        )
        revaluation.voucher_id = voucher_id

        self.session.add(revaluation)
        await self.session.commit()
        await self.session.refresh(revaluation)

        # Audit trail - log impairment
        await self.audit_service.log_action(
            organization_id=asset.organization_id,
            entity_type=EntityType.FIXED_ASSET.value,
            entity_id=asset.id,
            entity_reference=asset.asset_code,
            action=AuditAction.IMPAIR.value,
            user_id=impaired_by or asset.updated_by,
            old_values=old_values,
            new_values=model_to_dict(asset),
            change_reason=f"Asset impaired by {data.impairment_amount}. New book value: {new_value}. {data.reason or ''}",
        )

        return revaluation

    async def list_by_organization(
        self,
        organization_id: UUID,
        category_id: Optional[UUID] = None,
        location_id: Optional[UUID] = None,
        status: Optional[AssetStatus] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[FixedAsset], int]:
        """List assets with filters."""
        query = select(FixedAsset).where(
            FixedAsset.organization_id == organization_id,
            FixedAsset.is_active == True,
        )

        if category_id:
            query = query.where(FixedAsset.category_id == category_id)
        if location_id:
            query = query.where(FixedAsset.location_id == location_id)
        if status:
            query = query.where(FixedAsset.status == status)
        if search:
            search_filter = f"%{search}%"
            query = query.where(
                (FixedAsset.asset_code.ilike(search_filter)) |
                (FixedAsset.asset_name.ilike(search_filter)) |
                (FixedAsset.serial_number.ilike(search_filter))
            )

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.session.execute(count_query)
        total = count_result.scalar_one()

        # Fetch with pagination
        query = query.options(
            selectinload(FixedAsset.category),
            selectinload(FixedAsset.location),
            selectinload(FixedAsset.department),
        ).order_by(FixedAsset.asset_code).offset(skip).limit(limit)

        result = await self.session.execute(query)
        assets = list(result.scalars().all())

        return assets, total

    async def get_assets_for_depreciation(
        self,
        organization_id: UUID,
        as_on_date: date,
    ) -> List[FixedAsset]:
        """Get all active assets eligible for depreciation."""
        result = await self.session.execute(
            select(FixedAsset)
            .options(selectinload(FixedAsset.category))
            .where(
                FixedAsset.organization_id == organization_id,
                FixedAsset.status == AssetStatus.ACTIVE,
                FixedAsset.is_active == True,
                FixedAsset.depreciation_method != DepreciationMethod.NO_DEPRECIATION,
                FixedAsset.wdv_value > FixedAsset.residual_value,
                (FixedAsset.depreciation_start_date <= as_on_date) | (FixedAsset.depreciation_start_date == None),
            )
        )
        return list(result.scalars().all())

    async def _get_category(self, category_id: UUID) -> Optional[AssetCategory]:
        """Get asset category by ID."""
        result = await self.session.execute(
            select(AssetCategory).where(
                AssetCategory.id == category_id,
                AssetCategory.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def _generate_asset_code(
        self,
        organization_id: UUID,
        category_code: str,
    ) -> str:
        """Generate unique asset code."""
        from datetime import datetime
        year = datetime.now().year

        # Get count for this category/year
        result = await self.session.execute(
            select(func.count(FixedAsset.id)).where(
                FixedAsset.organization_id == organization_id,
                FixedAsset.asset_code.like(f"FA/{category_code}/{year}/%"),
            )
        )
        count = result.scalar_one() + 1

        return f"FA/{category_code}/{year}/{count:05d}"

    async def _get_fy_and_period(
        self,
        organization_id: UUID,
        transaction_date: date,
    ) -> Tuple[UUID, UUID]:
        """Get financial year and period for a transaction date."""
        fy = await self.fy_repo.get_by_date(organization_id, transaction_date)
        if not fy:
            raise ValueError(f"No financial year found for date {transaction_date}")
        if fy.is_closed:
            raise ValueError("Cannot post to a closed financial year")

        period = await self.period_repo.get_by_date(fy.id, transaction_date)
        if not period:
            raise ValueError(f"No period found for date {transaction_date}")
        if period.is_closed:
            raise ValueError("Cannot post to a closed period")

        return fy.id, period.id

    async def _post_capitalization_gl(
        self,
        asset: FixedAsset,
        category: AssetCategory,
        capitalization_date: date,
        posted_by: Optional[UUID] = None,
    ) -> List:
        """Create GL entries for asset capitalization."""
        if not category or not category.gl_asset_account_id:
            # Skip GL posting if category doesn't have GL accounts configured
            return []

        # Get financial year and period
        fy_id, period_id = await self._get_fy_and_period(
            asset.organization_id, capitalization_date
        )

        # Build GL entry lines
        # Dr Fixed Asset Account (total cost)
        # Cr Vendor Payable (if vendor exists) or Cash/Bank
        gl_lines: List[Dict[str, Any]] = []

        # Debit: Fixed Asset Account
        gl_lines.append({
            "account_id": category.gl_asset_account_id,
            "debit_amount": asset.total_cost,
            "credit_amount": Decimal("0.00"),
            "narration": f"Capitalization of {asset.asset_code} - {asset.asset_name}",
        })

        # Credit: Vendor Payable or sundry account
        # For now, use the asset account as contra (will be offset by purchase bill)
        # In a complete implementation, this would be linked to a purchase bill or CWIP
        if asset.vendor_id:
            # If vendor exists, credit vendor payable (sub-ledger)
            from app.repositories.ap_ar.vendor_repo import VendorRepository
            vendor_repo = VendorRepository(self.session)
            vendor = await vendor_repo.get(asset.vendor_id)
            if vendor and vendor.payable_account_id:
                gl_lines.append({
                    "account_id": vendor.payable_account_id,
                    "debit_amount": Decimal("0.00"),
                    "credit_amount": asset.total_cost,
                    "party_type": PartyType.VENDOR,
                    "party_id": asset.vendor_id,
                    "narration": f"Capitalization of {asset.asset_code} - Vendor: {vendor.name}",
                })
            else:
                # Fallback: Use a suspense/CWIP account (category's asset account as placeholder)
                gl_lines.append({
                    "account_id": category.gl_asset_account_id,
                    "debit_amount": Decimal("0.00"),
                    "credit_amount": asset.total_cost,
                    "narration": f"Capitalization of {asset.asset_code} - Pending allocation",
                })
        else:
            # No vendor - use suspense entry (debit and credit same account nets to zero)
            # In practice, this should be linked to a purchase entry
            gl_lines.append({
                "account_id": category.gl_asset_account_id,
                "debit_amount": Decimal("0.00"),
                "credit_amount": asset.total_cost,
                "narration": f"Capitalization of {asset.asset_code} - Pending allocation",
            })

        # Post GL entries
        return await self.gl_posting_service.post_from_source(
            source_type=GLEntrySourceType.FIXED_ASSET_CAPITALIZE,
            source_id=asset.id,
            source_reference=f"CAP-{asset.asset_code}",
            organization_id=asset.organization_id,
            financial_year_id=fy_id,
            period_id=period_id,
            voucher_date=capitalization_date,
            narration=f"Asset Capitalization: {asset.asset_code} - {asset.asset_name}",
            lines=gl_lines,
            posted_by=posted_by,
            unit_id=asset.location_id,
        )

    async def _post_disposal_gl(
        self,
        asset: FixedAsset,
        category: Optional[AssetCategory],
        disposal_date: date,
        disposal_value: Decimal,
        disposal_gain_loss: Decimal,
        posted_by: Optional[UUID] = None,
    ) -> List:
        """Create GL entries for asset disposal."""
        if not category:
            return []

        # Get financial year and period
        fy_id, period_id = await self._get_fy_and_period(
            asset.organization_id, disposal_date
        )

        gl_lines: List[Dict[str, Any]] = []

        # Dr Accumulated Depreciation (reverse the accumulated amount)
        if category.gl_accumulated_depreciation_account_id and asset.accumulated_depreciation > 0:
            gl_lines.append({
                "account_id": category.gl_accumulated_depreciation_account_id,
                "debit_amount": asset.accumulated_depreciation,
                "credit_amount": Decimal("0.00"),
                "narration": f"Disposal of {asset.asset_code} - Accumulated Depreciation",
            })

        # Dr Bank/Cash (disposal proceeds)
        if disposal_value > 0 and category.gl_disposal_account_id:
            gl_lines.append({
                "account_id": category.gl_disposal_account_id,
                "debit_amount": disposal_value,
                "credit_amount": Decimal("0.00"),
                "narration": f"Disposal proceeds of {asset.asset_code}",
            })

        # Dr/Cr Gain or Loss on Disposal
        if disposal_gain_loss != 0 and category.gl_disposal_account_id:
            if disposal_gain_loss < 0:
                # Loss on disposal (debit)
                gl_lines.append({
                    "account_id": category.gl_disposal_account_id,
                    "debit_amount": abs(disposal_gain_loss),
                    "credit_amount": Decimal("0.00"),
                    "narration": f"Loss on disposal of {asset.asset_code}",
                })
            else:
                # Gain on disposal (credit)
                gl_lines.append({
                    "account_id": category.gl_disposal_account_id,
                    "debit_amount": Decimal("0.00"),
                    "credit_amount": disposal_gain_loss,
                    "narration": f"Gain on disposal of {asset.asset_code}",
                })

        # Cr Fixed Asset Account (original cost)
        if category.gl_asset_account_id:
            gl_lines.append({
                "account_id": category.gl_asset_account_id,
                "debit_amount": Decimal("0.00"),
                "credit_amount": asset.total_cost,
                "narration": f"Disposal of {asset.asset_code} - Asset Cost",
            })

        if not gl_lines:
            return []

        # Post GL entries
        return await self.gl_posting_service.post_from_source(
            source_type=GLEntrySourceType.FIXED_ASSET_DISPOSAL,
            source_id=asset.id,
            source_reference=f"DSP-{asset.asset_code}",
            organization_id=asset.organization_id,
            financial_year_id=fy_id,
            period_id=period_id,
            voucher_date=disposal_date,
            narration=f"Asset Disposal: {asset.asset_code} - {asset.asset_name}",
            lines=gl_lines,
            posted_by=posted_by,
            unit_id=asset.location_id,
        )

    async def _post_revaluation_gl(
        self,
        asset: FixedAsset,
        category: Optional[AssetCategory],
        revaluation_date: date,
        revaluation_type: RevaluationType,
        revaluation_amount: Decimal,
        posted_by: Optional[UUID] = None,
    ) -> Optional[UUID]:
        """Create GL entries for asset revaluation."""
        if not category or not category.gl_asset_account_id:
            return None

        # Get financial year and period
        fy_id, period_id = await self._get_fy_and_period(
            asset.organization_id, revaluation_date
        )

        gl_lines: List[Dict[str, Any]] = []

        # Get or use revaluation reserve account (use disposal account as fallback)
        revaluation_reserve_account = category.gl_disposal_account_id or category.gl_asset_account_id

        if revaluation_type == RevaluationType.INCREASE:
            # Dr Asset Account, Cr Revaluation Reserve
            gl_lines.append({
                "account_id": category.gl_asset_account_id,
                "debit_amount": revaluation_amount,
                "credit_amount": Decimal("0.00"),
                "narration": f"Revaluation increase of {asset.asset_code}",
            })
            gl_lines.append({
                "account_id": revaluation_reserve_account,
                "debit_amount": Decimal("0.00"),
                "credit_amount": revaluation_amount,
                "narration": f"Revaluation reserve for {asset.asset_code}",
            })
        else:
            # Dr Revaluation Reserve (or P&L), Cr Asset Account
            gl_lines.append({
                "account_id": revaluation_reserve_account,
                "debit_amount": revaluation_amount,
                "credit_amount": Decimal("0.00"),
                "narration": f"Revaluation decrease of {asset.asset_code}",
            })
            gl_lines.append({
                "account_id": category.gl_asset_account_id,
                "debit_amount": Decimal("0.00"),
                "credit_amount": revaluation_amount,
                "narration": f"Revaluation of {asset.asset_code}",
            })

        # Post GL entries
        entries = await self.gl_posting_service.post_from_source(
            source_type=GLEntrySourceType.FIXED_ASSET_REVALUATION,
            source_id=asset.id,
            source_reference=f"RVL-{asset.asset_code}",
            organization_id=asset.organization_id,
            financial_year_id=fy_id,
            period_id=period_id,
            voucher_date=revaluation_date,
            narration=f"Asset Revaluation: {asset.asset_code} - {asset.asset_name}",
            lines=gl_lines,
            posted_by=posted_by,
            unit_id=asset.location_id,
        )

        # Return the voucher_id (source_id used as pseudo-voucher)
        return asset.id if entries else None

    async def _post_impairment_gl(
        self,
        asset: FixedAsset,
        category: Optional[AssetCategory],
        impairment_date: date,
        impairment_amount: Decimal,
        posted_by: Optional[UUID] = None,
    ) -> Optional[UUID]:
        """Create GL entries for asset impairment."""
        if not category or not category.gl_asset_account_id:
            return None

        # Get financial year and period
        fy_id, period_id = await self._get_fy_and_period(
            asset.organization_id, impairment_date
        )

        gl_lines: List[Dict[str, Any]] = []

        # Use depreciation expense account for impairment loss (or disposal account)
        impairment_loss_account = (
            category.gl_depreciation_expense_account_id or
            category.gl_disposal_account_id or
            category.gl_asset_account_id
        )

        # Dr Impairment Loss, Cr Asset Account
        gl_lines.append({
            "account_id": impairment_loss_account,
            "debit_amount": impairment_amount,
            "credit_amount": Decimal("0.00"),
            "narration": f"Impairment loss on {asset.asset_code}",
        })
        gl_lines.append({
            "account_id": category.gl_asset_account_id,
            "debit_amount": Decimal("0.00"),
            "credit_amount": impairment_amount,
            "narration": f"Impairment of {asset.asset_code}",
        })

        # Post GL entries
        entries = await self.gl_posting_service.post_from_source(
            source_type=GLEntrySourceType.FIXED_ASSET_IMPAIRMENT,
            source_id=asset.id,
            source_reference=f"IMP-{asset.asset_code}",
            organization_id=asset.organization_id,
            financial_year_id=fy_id,
            period_id=period_id,
            voucher_date=impairment_date,
            narration=f"Asset Impairment: {asset.asset_code} - {asset.asset_name}",
            lines=gl_lines,
            posted_by=posted_by,
            unit_id=asset.location_id,
        )

        return asset.id if entries else None
