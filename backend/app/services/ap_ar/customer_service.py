"""Customer service."""

from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ap_ar.customer import Customer
from app.repositories.ap_ar.customer_repo import CustomerRepository
from app.schemas.ap_ar.customer import CustomerCreate, CustomerUpdate


class CustomerService:
    """Service for customer operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CustomerRepository(db)

    async def get_all(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 50,
        include_inactive: bool = False,
        search: Optional[str] = None,
        customer_type: Optional[str] = None,
    ) -> Tuple[List[Customer], int]:
        """Get all customers with filters."""
        return await self.repo.get_all(
            organization_id, skip, limit, include_inactive, search, customer_type
        )

    async def get_active(self, organization_id: UUID) -> List[Customer]:
        """Get active customers for dropdown lists."""
        return await self.repo.get_active(organization_id)

    async def get(self, customer_id: UUID) -> Customer:
        """Get customer by ID."""
        customer = await self.repo.get(customer_id)
        if not customer or customer.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found",
            )
        return customer

    async def generate_code(self, organization_id: UUID) -> str:
        """Generate next customer code."""
        return await self.repo.get_next_code(organization_id)

    async def create(self, data: CustomerCreate, user_id: UUID) -> Customer:
        """Create a new customer."""
        # Check for duplicate code
        existing = await self.repo.get_by_code(data.organization_id, data.code)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Customer with code '{data.code}' already exists",
            )

        # Check for duplicate GSTIN if provided
        if data.gstin:
            existing_gstin = await self.repo.get_by_gstin(
                data.organization_id, data.gstin
            )
            if existing_gstin:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Customer with GSTIN '{data.gstin}' already exists",
                )

        # Create customer
        customer_data = data.model_dump()
        customer_data["created_by"] = user_id
        customer_data["current_balance"] = data.opening_balance
        customer_data["current_balance_type"] = data.opening_balance_type

        customer = await self.repo.create(customer_data)
        await self.db.flush()
        await self.db.refresh(customer)
        return customer

    async def update(
        self, customer_id: UUID, data: CustomerUpdate, user_id: UUID
    ) -> Customer:
        """Update a customer."""
        customer = await self.get(customer_id)

        # Check for duplicate GSTIN if being changed
        if data.gstin and data.gstin != customer.gstin:
            existing_gstin = await self.repo.get_by_gstin(
                customer.organization_id, data.gstin
            )
            if existing_gstin and existing_gstin.id != customer_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Customer with GSTIN '{data.gstin}' already exists",
                )

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by"] = user_id
        update_data["updated_at"] = datetime.now(timezone.utc)

        customer = await self.repo.update(customer, update_data)
        await self.db.flush()
        await self.db.refresh(customer)
        return customer

    async def delete(self, customer_id: UUID, user_id: UUID) -> None:
        """Soft delete a customer."""
        customer = await self.get(customer_id)

        # Check if customer has any transactions
        # TODO: Add check for invoices and receipts

        await self.repo.soft_delete(customer, user_id)
        await self.db.flush()
