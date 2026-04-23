"""Voucher Type service."""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ConflictException, BadRequestException
from app.models.finance.voucher_type import VoucherType
from app.repositories.finance.voucher_type_repo import VoucherTypeRepository
from app.repositories.masters.organization_repo import OrganizationRepository
from app.schemas.finance.voucher_type import VoucherTypeCreate, VoucherTypeUpdate
from app.core.constants import VoucherClass


class VoucherTypeService:
    """Service for voucher type management."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = VoucherTypeRepository(session)
        self.org_repo = OrganizationRepository(session)

    async def create(
        self,
        data: VoucherTypeCreate,
        created_by: Optional[UUID] = None,
    ) -> VoucherType:
        """Create a new voucher type."""
        # Check if code exists in organization
        if await self.repo.code_exists(data.code, data.organization_id):
            raise ConflictException(f"Voucher type code '{data.code}' already exists")

        # Verify organization exists
        org = await self.org_repo.get(data.organization_id)
        if not org:
            raise NotFoundException("Organization not found")

        vtype_data = data.model_dump()
        vtype_data["created_by"] = created_by
        vtype_data["current_number"] = 0

        return await self.repo.create(vtype_data)

    async def update(
        self,
        id: UUID,
        data: VoucherTypeUpdate,
        updated_by: Optional[UUID] = None,
    ) -> VoucherType:
        """Update a voucher type."""
        vtype = await self.repo.get(id)
        if not vtype:
            raise NotFoundException("Voucher type not found")

        if vtype.is_system:
            raise BadRequestException("Cannot update system-defined voucher type")

        # Check code uniqueness if being updated
        if data.code and data.code != vtype.code:
            if await self.repo.code_exists(data.code, vtype.organization_id, exclude_id=id):
                raise ConflictException(f"Voucher type code '{data.code}' already exists")

        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by"] = updated_by

        return await self.repo.update(vtype, update_data)

    async def get(self, id: UUID) -> VoucherType:
        """Get voucher type by ID."""
        vtype = await self.repo.get(id)
        if not vtype:
            raise NotFoundException("Voucher type not found")
        return vtype

    async def get_by_code(
        self,
        code: str,
        organization_id: UUID,
    ) -> VoucherType:
        """Get voucher type by code."""
        vtype = await self.repo.get_by_code(code, organization_id)
        if not vtype:
            raise NotFoundException(f"Voucher type '{code}' not found")
        return vtype

    async def get_all(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> Tuple[List[VoucherType], int]:
        """Get all voucher types for an organization."""
        vtypes = await self.repo.get_by_organization(organization_id, include_inactive)
        total = len(vtypes)
        return vtypes[skip:skip + limit], total

    async def get_by_class(
        self,
        organization_id: UUID,
        voucher_class: VoucherClass,
    ) -> List[VoucherType]:
        """Get voucher types by class."""
        return await self.repo.get_by_class(organization_id, voucher_class)

    async def delete(
        self,
        id: UUID,
        deleted_by: Optional[UUID] = None,
    ) -> VoucherType:
        """Soft delete a voucher type."""
        vtype = await self.repo.get(id)
        if not vtype:
            raise NotFoundException("Voucher type not found")

        if vtype.is_system:
            raise BadRequestException("Cannot delete system-defined voucher type")

        # TODO: Check if voucher type has vouchers

        return await self.repo.soft_delete(id, deleted_by)
