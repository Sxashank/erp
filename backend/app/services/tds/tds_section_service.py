"""TDS Section service."""

from datetime import date
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tds.tds_section import TDSSection
from app.schemas.tds.tds_section import TDSSectionCreate, TDSSectionUpdate
from app.repositories.tds.tds_section_repo import TDSSectionRepository
from app.core.exceptions import NotFoundException, ConflictException


class TDSSectionService:
    """Service for TDS Section operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = TDSSectionRepository(session)

    async def create(self, data: TDSSectionCreate, created_by: UUID) -> TDSSection:
        """Create a new TDS section."""
        existing = await self.repo.get_by_code(data.section_code)
        if existing:
            raise ConflictException(f"TDS section '{data.section_code}' already exists")

        section = TDSSection(
            **data.model_dump(),
            created_by=created_by,
        )
        self.session.add(section)
        await self.session.flush()
        await self.session.refresh(section)
        return section

    async def update(
        self,
        id: UUID,
        data: TDSSectionUpdate,
        updated_by: UUID,
    ) -> TDSSection:
        """Update a TDS section."""
        section = await self.repo.get(id)
        if not section:
            raise NotFoundException("TDS section not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(section, field, value)
        section.updated_by = updated_by

        await self.session.flush()
        await self.session.refresh(section)
        return section

    async def get(self, id: UUID) -> TDSSection:
        """Get TDS section by ID."""
        section = await self.repo.get(id)
        if not section:
            raise NotFoundException("TDS section not found")
        return section

    async def get_by_code(self, section_code: str) -> TDSSection:
        """Get TDS section by code."""
        section = await self.repo.get_by_code(section_code)
        if not section:
            raise NotFoundException(f"TDS section '{section_code}' not found")
        return section

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
        return_form: Optional[str] = None,
    ) -> Tuple[List[TDSSection], int]:
        """Get all TDS sections."""
        return await self.repo.get_all_sections(skip, limit, include_inactive, return_form)

    async def get_active(
        self,
        as_of_date: Optional[date] = None,
        is_tcs: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[TDSSection], int]:
        """Get active TDS/TCS sections."""
        return await self.repo.get_active_sections(as_of_date, is_tcs, skip, limit)

    async def delete(self, id: UUID, deleted_by: UUID) -> None:
        """Soft delete a TDS section."""
        section = await self.repo.get(id)
        if not section:
            raise NotFoundException("TDS section not found")
        section.soft_delete(deleted_by)
        await self.session.flush()
