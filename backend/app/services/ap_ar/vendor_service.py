"""Vendor service."""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ap_ar.vendor import Vendor
from app.schemas.ap_ar.vendor import VendorCreate, VendorUpdate
from app.repositories.ap_ar.vendor_repo import VendorRepository
from app.core.exceptions import NotFoundException, ConflictException


class VendorService:
    """Service for Vendor operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = VendorRepository(session)

    async def create(self, data: VendorCreate, created_by: UUID) -> Vendor:
        """Create a new vendor."""
        # Check for duplicate code within organization
        existing = await self.repo.get_by_code(data.code, data.organization_id)
        if existing:
            raise ConflictException(f"Vendor with code '{data.code}' already exists")

        # Check for duplicate GSTIN if provided
        if data.gstin:
            existing_gstin = await self.repo.get_by_gstin(data.gstin, data.organization_id)
            if existing_gstin:
                raise ConflictException(f"Vendor with GSTIN '{data.gstin}' already exists")

        vendor = Vendor(
            **data.model_dump(),
            created_by=created_by,
        )
        self.session.add(vendor)
        await self.session.flush()
        await self.session.refresh(vendor)
        return vendor

    async def update(
        self,
        id: UUID,
        data: VendorUpdate,
        updated_by: UUID,
    ) -> Vendor:
        """Update a vendor."""
        vendor = await self.repo.get(id)
        if not vendor:
            raise NotFoundException("Vendor not found")

        # Check for duplicate GSTIN if being changed
        if data.gstin and data.gstin != vendor.gstin:
            existing_gstin = await self.repo.get_by_gstin(data.gstin, vendor.organization_id)
            if existing_gstin and existing_gstin.id != id:
                raise ConflictException(f"Vendor with GSTIN '{data.gstin}' already exists")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(vendor, field, value)
        vendor.updated_by = updated_by

        await self.session.flush()
        await self.session.refresh(vendor)
        return vendor

    async def get(self, id: UUID) -> Vendor:
        """Get vendor by ID."""
        vendor = await self.repo.get(id)
        if not vendor:
            raise NotFoundException("Vendor not found")
        return vendor

    async def get_by_code(self, code: str, organization_id: UUID) -> Vendor:
        """Get vendor by code."""
        vendor = await self.repo.get_by_code(code, organization_id)
        if not vendor:
            raise NotFoundException(f"Vendor with code '{code}' not found")
        return vendor

    async def get_all(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
        search: Optional[str] = None,
        vendor_type: Optional[str] = None,
    ) -> Tuple[List[Vendor], int]:
        """Get all vendors for an organization."""
        return await self.repo.get_all_by_organization(
            organization_id, skip, limit, include_inactive, search, vendor_type
        )

    async def get_active(self, organization_id: UUID) -> List[Vendor]:
        """Get active vendors for dropdown lists."""
        return await self.repo.get_active_vendors(organization_id)

    async def delete(self, id: UUID, deleted_by: UUID) -> None:
        """Soft delete a vendor."""
        vendor = await self.repo.get(id)
        if not vendor:
            raise NotFoundException("Vendor not found")
        vendor.soft_delete(deleted_by)
        await self.session.flush()

    async def generate_code(self, organization_id: UUID) -> str:
        """Generate next vendor code."""
        return await self.repo.generate_vendor_code(organization_id)
