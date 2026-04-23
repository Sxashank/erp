"""Fixed Assets Configuration Service."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ConflictException
from app.models.fixed_assets.fa_config import FAConfiguration
from app.schemas.fixed_assets.fa_config import (
    FAConfigurationCreate,
    FAConfigurationUpdate,
)


class FAConfigurationService:
    """Service for managing Fixed Assets configuration."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_organization(
        self,
        organization_id: UUID,
    ) -> Optional[FAConfiguration]:
        """Get FA configuration for an organization."""
        query = select(FAConfiguration).where(
            FAConfiguration.organization_id == organization_id,
            FAConfiguration.is_active == True,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_or_create_default(
        self,
        organization_id: UUID,
        created_by: Optional[UUID] = None,
    ) -> FAConfiguration:
        """Get configuration or create with defaults."""
        config = await self.get_by_organization(organization_id)
        if config:
            return config

        # Create default configuration
        data = FAConfigurationCreate(organization_id=organization_id)
        return await self.create(data, created_by)

    async def create(
        self,
        data: FAConfigurationCreate,
        created_by: Optional[UUID] = None,
    ) -> FAConfiguration:
        """Create FA configuration for an organization."""
        # Check if config already exists
        existing = await self.get_by_organization(data.organization_id)
        if existing:
            raise ConflictException(
                "FA configuration already exists for this organization"
            )

        config = FAConfiguration(
            organization_id=data.organization_id,
            asset_code_prefix=data.asset_code_prefix,
            asset_code_format=data.asset_code_format,
            asset_code_separator=data.asset_code_separator,
            auto_generate_code=data.auto_generate_code,
            fy_start_month=data.fy_start_month,
            fy_start_day=data.fy_start_day,
            creation_approval_threshold=data.creation_approval_threshold,
            disposal_approval_threshold=data.disposal_approval_threshold,
            revaluation_approval_threshold=data.revaluation_approval_threshold,
            transfer_requires_approval=data.transfer_requires_approval,
            days_in_year=data.days_in_year,
            pro_rata_method=data.pro_rata_method,
            min_asset_value_for_depreciation=data.min_asset_value_for_depreciation,
            depreciation_posting_auto_approve=data.depreciation_posting_auto_approve,
            amc_expiry_reminder_days=data.amc_expiry_reminder_days,
            insurance_expiry_reminder_days=data.insurance_expiry_reminder_days,
            warranty_expiry_reminder_days=data.warranty_expiry_reminder_days,
            lease_expiry_reminder_days=data.lease_expiry_reminder_days,
            lease_payment_reminder_days=data.lease_payment_reminder_days,
            pv_frequency_months=data.pv_frequency_months,
            pv_tolerance_percentage=data.pv_tolerance_percentage,
            auto_post_capitalization=data.auto_post_capitalization,
            auto_post_disposal=data.auto_post_disposal,
            auto_post_depreciation=data.auto_post_depreciation,
            default_page_size=data.default_page_size,
            max_page_size=data.max_page_size,
            custom_settings=data.custom_settings,
            notification_emails=data.notification_emails,
            created_by=created_by,
        )

        self.session.add(config)
        await self.session.flush()
        await self.session.refresh(config)
        return config

    async def update(
        self,
        organization_id: UUID,
        data: FAConfigurationUpdate,
        updated_by: Optional[UUID] = None,
    ) -> FAConfiguration:
        """Update FA configuration."""
        config = await self.get_by_organization(organization_id)
        if not config:
            raise NotFoundException("FA configuration not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(config, field, value)

        config.updated_by = updated_by
        await self.session.flush()
        await self.session.refresh(config)
        return config

    async def delete(
        self,
        organization_id: UUID,
        deleted_by: Optional[UUID] = None,
    ) -> bool:
        """Soft delete FA configuration."""
        config = await self.get_by_organization(organization_id)
        if not config:
            return False

        config.soft_delete(deleted_by)
        await self.session.flush()
        return True
