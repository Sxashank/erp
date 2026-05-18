"""GST Registration service."""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.encryption import encrypt_value
from app.core.exceptions import ConflictException, NotFoundException
from app.models.gst.gst_registration import GSTRegistration
from app.repositories.gst.gst_registration_repo import GSTRegistrationRepository
from app.schemas.gst.gst_registration import GSTRegistrationCreate, GSTRegistrationUpdate


class GSTRegistrationService:
    """Service for GST Registration operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = GSTRegistrationRepository(session)

    async def create(self, data: GSTRegistrationCreate, created_by: UUID) -> GSTRegistration:
        """Create a new GST registration."""
        existing = await self.repo.get_by_gstin(data.gstin)
        if existing:
            raise ConflictException(f"GSTIN '{data.gstin}' already registered")

        # Never persist portal credentials in plaintext. Encrypt with Fernet via
        # app.core.encryption. See CLAUDE.md §6.8.
        create_data = data.model_dump(exclude={"e_invoice_password"})
        if data.e_invoice_password:
            create_data["e_invoice_password_encrypted"] = encrypt_value(data.e_invoice_password)

        registration = GSTRegistration(
            **create_data,
            created_by=created_by,
        )
        self.session.add(registration)
        await self.session.flush()
        await self.session.refresh(registration)
        return registration

    async def update(
        self,
        id: UUID,
        data: GSTRegistrationUpdate,
        updated_by: UUID,
    ) -> GSTRegistration:
        """Update a GST registration."""
        registration = await self.repo.get_with_details(id)
        if not registration:
            raise NotFoundException("GST registration not found")

        update_data = data.model_dump(exclude_unset=True, exclude={"e_invoice_password"})
        for field, value in update_data.items():
            setattr(registration, field, value)

        if data.e_invoice_password:
            registration.e_invoice_password_encrypted = encrypt_value(data.e_invoice_password)

        registration.updated_by = updated_by

        await self.session.flush()
        await self.session.refresh(registration)
        return registration

    async def get(self, id: UUID) -> GSTRegistration:
        """Get GST registration by ID."""
        registration = await self.repo.get_with_details(id)
        if not registration:
            raise NotFoundException("GST registration not found")
        return registration

    async def get_by_gstin(self, gstin: str) -> GSTRegistration:
        """Get GST registration by GSTIN."""
        registration = await self.repo.get_by_gstin(gstin)
        if not registration:
            raise NotFoundException(f"GSTIN '{gstin}' not found")
        return registration

    async def get_by_organization(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> Tuple[List[GSTRegistration], int]:
        """Get all GST registrations for an organization."""
        return await self.repo.get_by_organization(
            organization_id, skip, limit, include_inactive
        )

    async def get_by_unit(self, unit_id: UUID) -> Optional[GSTRegistration]:
        """Get GST registration for a unit."""
        return await self.repo.get_by_unit(unit_id)

    async def delete(self, id: UUID, deleted_by: UUID) -> None:
        """Soft delete a GST registration."""
        registration = await self.repo.get(id)
        if not registration:
            raise NotFoundException("GST registration not found")
        registration.soft_delete(deleted_by)
        await self.session.flush()
