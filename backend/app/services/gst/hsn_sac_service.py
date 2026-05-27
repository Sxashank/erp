"""HSN/SAC service."""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.gst.hsn_sac import HSNSAC
from app.schemas.gst.hsn_sac import HSNSACCreate, HSNSACUpdate
from app.repositories.gst.hsn_sac_repo import HSNSACRepository
from app.core.constants import HSNSACType
from app.core.exceptions import NotFoundException, ConflictException


class HSNSACService:
    """Service for HSN/SAC operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = HSNSACRepository(session)

    async def create(self, data: HSNSACCreate, created_by: UUID) -> HSNSAC:
        """Create a new HSN/SAC code."""
        existing = await self.repo.get_by_code(data.code)
        if existing:
            raise ConflictException(f"HSN/SAC code '{data.code}' already exists")

        hsn_sac = HSNSAC(
            **data.model_dump(),
            created_by=created_by,
        )
        self.session.add(hsn_sac)
        await self.session.flush()
        await self.session.refresh(hsn_sac)
        await self.session.commit()
        return hsn_sac

    async def update(
        self,
        id: UUID,
        data: HSNSACUpdate,
        updated_by: UUID,
    ) -> HSNSAC:
        """Update an HSN/SAC code."""
        hsn_sac = await self.repo.get(id)
        if not hsn_sac:
            raise NotFoundException("HSN/SAC code not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(hsn_sac, field, value)
        hsn_sac.updated_by = updated_by

        await self.session.flush()
        await self.session.refresh(hsn_sac)
        await self.session.commit()
        return hsn_sac

    async def get(self, id: UUID) -> HSNSAC:
        """Get HSN/SAC by ID."""
        hsn_sac = await self.repo.get(id)
        if not hsn_sac:
            raise NotFoundException("HSN/SAC code not found")
        return hsn_sac

    async def get_by_code(self, code: str) -> HSNSAC:
        """Get HSN/SAC by code."""
        hsn_sac = await self.repo.get_by_code(code)
        if not hsn_sac:
            raise NotFoundException(f"HSN/SAC code '{code}' not found")
        return hsn_sac

    async def search(
        self,
        search_term: str = "",
        hsn_sac_type: Optional[HSNSACType] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[HSNSAC], int]:
        """Search HSN/SAC codes."""
        return await self.repo.search(search_term, hsn_sac_type, skip, limit)

    async def delete(self, id: UUID, deleted_by: UUID) -> None:
        """Soft delete an HSN/SAC code."""
        hsn_sac = await self.repo.get(id)
        if not hsn_sac:
            raise NotFoundException("HSN/SAC code not found")
        hsn_sac.soft_delete(deleted_by)
        await self.session.flush()
        await self.session.commit()
