"""Vendor Registration Repositories."""

from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.repositories.base import BaseRepository
from app.models.vendor_portal.registration import (
    VendorRegistration,
    VendorRegistrationDocument,
)
from app.models.vendor_portal.enums import RegistrationStatus, RegistrationDocumentType


class VendorRegistrationRepository(BaseRepository[VendorRegistration]):
    """Repository for vendor registration operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(VendorRegistration, session)

    async def get_with_documents(self, id: UUID) -> Optional[VendorRegistration]:
        """Get registration with documents."""
        query = (
            select(self.model)
            .options(selectinload(self.model.documents))
            .where(
                and_(
                    self.model.id == id,
                    self.model.is_active == True,
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_pan(
        self, pan: str, organization_id: UUID
    ) -> Optional[VendorRegistration]:
        """Get registration by PAN."""
        query = select(self.model).where(
            and_(
                self.model.pan == pan,
                self.model.organization_id == organization_id,
                self.model.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_gstin(
        self, gstin: str, organization_id: UUID
    ) -> Optional[VendorRegistration]:
        """Get registration by GSTIN."""
        query = select(self.model).where(
            and_(
                self.model.gstin == gstin,
                self.model.organization_id == organization_id,
                self.model.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_email(
        self, email: str, organization_id: UUID
    ) -> Optional[VendorRegistration]:
        """Get registration by contact email."""
        query = select(self.model).where(
            and_(
                self.model.contact_email == email,
                self.model.organization_id == organization_id,
                self.model.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all_by_organization(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
        status: Optional[RegistrationStatus] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[VendorRegistration], int]:
        """Get all registrations for an organization with filters."""
        conditions = [
            self.model.organization_id == organization_id,
            self.model.is_active == True,
        ]

        if status:
            conditions.append(self.model.status == status)

        if search:
            search_term = f"%{search}%"
            conditions.append(
                or_(
                    self.model.company_name.ilike(search_term),
                    self.model.registration_number.ilike(search_term),
                    self.model.pan.ilike(search_term),
                    self.model.gstin.ilike(search_term),
                    self.model.contact_email.ilike(search_term),
                )
            )

        # Count query
        count_query = select(func.count(self.model.id)).where(and_(*conditions))
        count_result = await self.session.execute(count_query)
        total = count_result.scalar() or 0

        # Data query
        query = (
            select(self.model)
            .where(and_(*conditions))
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_pending_reviews(
        self, organization_id: UUID
    ) -> List[VendorRegistration]:
        """Get registrations pending review."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.organization_id == organization_id,
                    self.model.status == RegistrationStatus.SUBMITTED,
                    self.model.is_active == True,
                )
            )
            .order_by(self.model.submitted_at.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def generate_registration_number(
        self, organization_id: UUID
    ) -> str:
        """Generate unique registration number."""
        # Get count for the year
        year = datetime.now().year
        prefix = f"VR/{year}/"

        query = select(func.count(self.model.id)).where(
            and_(
                self.model.organization_id == organization_id,
                self.model.registration_number.like(f"{prefix}%"),
            )
        )
        result = await self.session.execute(query)
        count = (result.scalar() or 0) + 1

        return f"{prefix}{count:05d}"


class VendorRegistrationDocumentRepository(BaseRepository[VendorRegistrationDocument]):
    """Repository for registration document operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(VendorRegistrationDocument, session)

    async def get_by_registration(
        self, registration_id: UUID
    ) -> List[VendorRegistrationDocument]:
        """Get all documents for a registration."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.registration_id == registration_id,
                    self.model.is_active == True,
                )
            )
            .order_by(self.model.created_at.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_type(
        self, registration_id: UUID, document_type: RegistrationDocumentType
    ) -> Optional[VendorRegistrationDocument]:
        """Get document by type for a registration."""
        query = select(self.model).where(
            and_(
                self.model.registration_id == registration_id,
                self.model.document_type == document_type,
                self.model.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_pending_verification(
        self, registration_id: UUID
    ) -> List[VendorRegistrationDocument]:
        """Get documents pending verification."""
        query = (
            select(self.model)
            .where(
                and_(
                    self.model.registration_id == registration_id,
                    self.model.is_verified == False,
                    self.model.is_rejected == False,
                    self.model.is_active == True,
                )
            )
            .order_by(self.model.created_at.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
