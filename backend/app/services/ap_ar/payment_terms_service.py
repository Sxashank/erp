"""Payment Terms service."""

from typing import List, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ap_ar.payment_terms import PaymentTerms
from app.schemas.ap_ar.payment_terms import PaymentTermsCreate, PaymentTermsUpdate
from app.repositories.ap_ar.payment_terms_repo import PaymentTermsRepository
from app.core.exceptions import NotFoundException, ConflictException


class PaymentTermsService:
    """Service for Payment Terms operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = PaymentTermsRepository(session)

    async def create(self, data: PaymentTermsCreate, created_by: UUID) -> PaymentTerms:
        """Create new payment terms."""
        # Check for duplicate code within organization
        existing = await self.repo.get_by_code(data.code, data.organization_id)
        if existing:
            raise ConflictException(f"Payment terms with code '{data.code}' already exists")

        payment_terms = PaymentTerms(
            **data.model_dump(),
            created_by=created_by,
        )
        self.session.add(payment_terms)
        await self.session.flush()
        await self.session.refresh(payment_terms)
        return payment_terms

    async def update(
        self,
        id: UUID,
        data: PaymentTermsUpdate,
        updated_by: UUID,
    ) -> PaymentTerms:
        """Update payment terms."""
        payment_terms = await self.repo.get(id)
        if not payment_terms:
            raise NotFoundException("Payment terms not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(payment_terms, field, value)
        payment_terms.updated_by = updated_by

        await self.session.flush()
        await self.session.refresh(payment_terms)
        return payment_terms

    async def get(self, id: UUID) -> PaymentTerms:
        """Get payment terms by ID."""
        payment_terms = await self.repo.get(id)
        if not payment_terms:
            raise NotFoundException("Payment terms not found")
        return payment_terms

    async def get_by_code(self, code: str, organization_id: UUID) -> PaymentTerms:
        """Get payment terms by code."""
        payment_terms = await self.repo.get_by_code(code, organization_id)
        if not payment_terms:
            raise NotFoundException(f"Payment terms with code '{code}' not found")
        return payment_terms

    async def get_all(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> Tuple[List[PaymentTerms], int]:
        """Get all payment terms for an organization."""
        return await self.repo.get_all_by_organization(
            organization_id, skip, limit, include_inactive
        )

    async def get_active(self, organization_id: UUID) -> List[PaymentTerms]:
        """Get active payment terms for dropdown lists."""
        return await self.repo.get_active_terms(organization_id)

    async def delete(self, id: UUID, deleted_by: UUID) -> None:
        """Soft delete payment terms."""
        payment_terms = await self.repo.get(id)
        if not payment_terms:
            raise NotFoundException("Payment terms not found")
        payment_terms.soft_delete(deleted_by)
        await self.session.flush()
