"""
Fixed Deposit Product Service
"""

from datetime import date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.fixed_deposits.fd_product import (
    FDProduct,
    FDInterestSlab,
    FDCustomerCategory,
)
from app.schemas.fixed_deposits.fd_product import (
    FDProductCreate,
    FDProductUpdate,
    FDProductResponse,
    FDProductListResponse,
    FDInterestSlabCreate,
    FDInterestSlabUpdate,
)


class FDProductService:
    """Service for FD Product operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_product(self, data: FDProductCreate) -> FDProduct:
        """Create a new FD product with interest slabs."""
        # Create product
        product_data = data.model_dump(exclude={"interest_slabs"})
        product = FDProduct(**product_data)
        self.db.add(product)
        await self.db.flush()

        # Create interest slabs
        if data.interest_slabs:
            for slab_data in data.interest_slabs:
                slab = FDInterestSlab(
                    product_id=product.id,
                    **slab_data.model_dump(),
                )
                self.db.add(slab)

        await self.db.flush()
        await self.db.refresh(product)

        # Load relationships
        result = await self.db.execute(
            select(FDProduct)
            .options(selectinload(FDProduct.interest_slabs))
            .where(FDProduct.id == product.id)
        )
        return result.scalar_one()

    async def get_product(self, product_id: UUID) -> Optional[FDProduct]:
        """Get FD product by ID."""
        result = await self.db.execute(
            select(FDProduct)
            .options(selectinload(FDProduct.interest_slabs))
            .where(FDProduct.id == product_id)
        )
        return result.scalar_one_or_none()

    async def update_product(
        self, product_id: UUID, data: FDProductUpdate
    ) -> Optional[FDProduct]:
        """Update an FD product."""
        product = await self.get_product(product_id)
        if not product:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)

        await self.db.flush()
        await self.db.refresh(product)
        return product

    async def delete_product(self, product_id: UUID) -> bool:
        """Soft delete an FD product."""
        product = await self.get_product(product_id)
        if not product:
            return False

        product.is_active = False
        await self.db.flush()
        return True

    async def list_products(
        self,
        organization_id: UUID,
        active_only: bool = True,
        skip: int = 0,
        limit: int = 100,
    ) -> FDProductListResponse:
        """List FD products with filtering."""
        query = select(FDProduct).where(
            FDProduct.organization_id == organization_id
        )

        if active_only:
            query = query.where(FDProduct.is_active == True)

        # Get total count
        count_result = await self.db.execute(
            select(FDProduct.id).where(
                FDProduct.organization_id == organization_id,
                FDProduct.is_active == True if active_only else True,
            )
        )
        total = len(count_result.all())

        # Get paginated results
        result = await self.db.execute(
            query
            .options(selectinload(FDProduct.interest_slabs))
            .order_by(FDProduct.product_code)
            .offset(skip)
            .limit(limit)
        )
        products = result.scalars().all()

        return FDProductListResponse(
            items=[FDProductResponse.model_validate(p) for p in products],
            total=total,
        )

    # Interest Slab Operations
    async def add_interest_slab(
        self, product_id: UUID, data: FDInterestSlabCreate
    ) -> FDInterestSlab:
        """Add interest slab to a product."""
        slab = FDInterestSlab(
            product_id=product_id,
            **data.model_dump(),
        )
        self.db.add(slab)
        await self.db.flush()
        await self.db.refresh(slab)
        return slab

    async def update_interest_slab(
        self, slab_id: UUID, data: FDInterestSlabUpdate
    ) -> Optional[FDInterestSlab]:
        """Update an interest slab."""
        result = await self.db.execute(
            select(FDInterestSlab).where(FDInterestSlab.id == slab_id)
        )
        slab = result.scalar_one_or_none()
        if not slab:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(slab, field, value)

        await self.db.flush()
        await self.db.refresh(slab)
        return slab

    async def delete_interest_slab(self, slab_id: UUID) -> bool:
        """Delete an interest slab."""
        result = await self.db.execute(
            select(FDInterestSlab).where(FDInterestSlab.id == slab_id)
        )
        slab = result.scalar_one_or_none()
        if not slab:
            return False

        await self.db.delete(slab)
        await self.db.flush()
        return True

    async def get_applicable_rate(
        self,
        product_id: UUID,
        tenure_days: int,
        amount: Decimal,
        customer_category: FDCustomerCategory,
        as_of_date: Optional[date] = None,
    ) -> Optional[Decimal]:
        """Get applicable interest rate for given parameters."""
        if as_of_date is None:
            as_of_date = date.today()

        query = select(FDInterestSlab).where(
            and_(
                FDInterestSlab.product_id == product_id,
                FDInterestSlab.customer_category == customer_category,
                FDInterestSlab.min_tenure_days <= tenure_days,
                FDInterestSlab.max_tenure_days >= tenure_days,
                FDInterestSlab.effective_from <= as_of_date,
                or_(
                    FDInterestSlab.effective_to.is_(None),
                    FDInterestSlab.effective_to >= as_of_date,
                ),
                FDInterestSlab.is_active == True,
            )
        )

        # Add amount filter if specified in slab
        result = await self.db.execute(query.order_by(FDInterestSlab.min_amount.desc()))
        slabs = result.scalars().all()

        for slab in slabs:
            # Check amount range if specified
            if slab.min_amount and amount < slab.min_amount:
                continue
            if slab.max_amount and amount > slab.max_amount:
                continue
            return slab.interest_rate

        return None
