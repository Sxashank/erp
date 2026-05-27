"""Loan Product repositories for the lending module."""

from datetime import date
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.lending.enums import (
    DocumentStage,
    FeeCollectionStage,
    FeeType,
)
from app.models.lending.product import (
    DocumentChecklist,
    FeeMaster,
    InterestRate,
    LoanProduct,
    ProductFee,
)
from app.repositories.base import BaseRepository


class InterestRateRepository(BaseRepository[InterestRate]):
    """Repository for InterestRate operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(InterestRate, session)

    async def get_by_code(self, code: str, organization_id: UUID) -> InterestRate | None:
        """Get interest rate by code."""
        query = select(InterestRate).where(
            and_(
                InterestRate.code == code,
                InterestRate.organization_id == organization_id,
                InterestRate.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all_by_organization(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
        effective_date: date | None = None,
    ) -> tuple[list[InterestRate], int]:
        """Get all interest rates for an organization."""
        base_query = select(InterestRate).where(InterestRate.organization_id == organization_id)

        if not include_inactive:
            base_query = base_query.where(InterestRate.is_active == True)

        if effective_date:
            base_query = base_query.where(
                and_(
                    InterestRate.effective_from <= effective_date,
                    or_(
                        InterestRate.effective_till.is_(None),
                        InterestRate.effective_till >= effective_date,
                    ),
                )
            )

        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = base_query.order_by(InterestRate.code).offset(skip).limit(limit)
        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_current_rate(
        self, rate_id: UUID, as_of_date: date | None = None
    ) -> InterestRate | None:
        """Get current rate as of a specific date."""
        if as_of_date is None:
            as_of_date = date.today()

        query = select(InterestRate).where(
            and_(
                InterestRate.id == rate_id,
                InterestRate.effective_from <= as_of_date,
                or_(
                    InterestRate.effective_till.is_(None),
                    InterestRate.effective_till >= as_of_date,
                ),
                InterestRate.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class FeeMasterRepository(BaseRepository[FeeMaster]):
    """Repository for FeeMaster operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(FeeMaster, session)

    async def get_by_code(self, code: str, organization_id: UUID) -> FeeMaster | None:
        """Get fee master by code."""
        query = select(FeeMaster).where(
            and_(
                FeeMaster.code == code,
                FeeMaster.organization_id == organization_id,
                FeeMaster.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all_by_organization(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
        fee_type: FeeType | None = None,
    ) -> tuple[list[FeeMaster], int]:
        """Get all fee masters for an organization."""
        base_query = select(FeeMaster).where(FeeMaster.organization_id == organization_id)

        if not include_inactive:
            base_query = base_query.where(FeeMaster.is_active == True)

        if fee_type:
            base_query = base_query.where(FeeMaster.fee_type == fee_type)

        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = base_query.order_by(FeeMaster.code).offset(skip).limit(limit)
        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_by_fee_type(
        self,
        organization_id: UUID,
        fee_type: FeeType,
    ) -> list[FeeMaster]:
        """Get all fee masters of a specific type."""
        query = select(FeeMaster).where(
            and_(
                FeeMaster.organization_id == organization_id,
                FeeMaster.fee_type == fee_type,
                FeeMaster.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())


class ProductFeeRepository(BaseRepository[ProductFee]):
    """Repository for ProductFee operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(ProductFee, session)

    async def get_by_product(
        self, product_id: UUID, include_inactive: bool = False
    ) -> list[ProductFee]:
        """Get all fees for a product."""
        query = select(ProductFee).where(ProductFee.product_id == product_id)
        if not include_inactive:
            query = query.where(ProductFee.is_active == True)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_stage(
        self, product_id: UUID, collection_stage: FeeCollectionStage
    ) -> list[ProductFee]:
        """Get fees for a product at a specific collection stage."""
        query = select(ProductFee).where(
            and_(
                ProductFee.product_id == product_id,
                ProductFee.collection_stage == collection_stage,
                ProductFee.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_mandatory_fees(self, product_id: UUID) -> list[ProductFee]:
        """Get mandatory fees for a product."""
        query = select(ProductFee).where(
            and_(
                ProductFee.product_id == product_id,
                ProductFee.is_mandatory == True,
                ProductFee.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())


class DocumentChecklistRepository(BaseRepository[DocumentChecklist]):
    """Repository for DocumentChecklist operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(DocumentChecklist, session)

    async def get_by_code(self, document_code: str, product_id: UUID) -> DocumentChecklist | None:
        """Get document checklist by code within a product."""
        query = select(DocumentChecklist).where(
            and_(
                DocumentChecklist.code == document_code,
                DocumentChecklist.product_id == product_id,
                DocumentChecklist.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_product(
        self, product_id: UUID, include_inactive: bool = False
    ) -> list[DocumentChecklist]:
        """Get all document checklist items for a product."""
        query = select(DocumentChecklist).where(DocumentChecklist.product_id == product_id)
        if not include_inactive:
            query = query.where(DocumentChecklist.is_active == True)
        query = query.order_by(DocumentChecklist.required_at_stage, DocumentChecklist.display_order)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_stage(
        self,
        product_id: UUID,
        stage: DocumentStage,
        entity_type: str | None = None,
    ) -> list[DocumentChecklist]:
        """Get document checklist for a specific stage."""
        query = select(DocumentChecklist).where(
            and_(
                DocumentChecklist.product_id == product_id,
                DocumentChecklist.required_at_stage == stage,
                DocumentChecklist.is_active == True,
            )
        )

        if entity_type:
            query = query.where(DocumentChecklist.applicable_entity_types.contains([entity_type]))

        query = query.order_by(DocumentChecklist.display_order)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_mandatory_documents(
        self,
        product_id: UUID,
        stage: DocumentStage | None = None,
        entity_type: str | None = None,
    ) -> list[DocumentChecklist]:
        """Get mandatory documents for a product."""
        query = select(DocumentChecklist).where(
            and_(
                DocumentChecklist.product_id == product_id,
                DocumentChecklist.is_mandatory == True,
                DocumentChecklist.is_active == True,
            )
        )

        if stage:
            query = query.where(DocumentChecklist.required_at_stage == stage)

        if entity_type:
            query = query.where(DocumentChecklist.applicable_entity_types.contains([entity_type]))

        result = await self.session.execute(query)
        return list(result.scalars().all())


class LoanProductRepository(BaseRepository[LoanProduct]):
    """Repository for LoanProduct operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(LoanProduct, session)

    async def get_by_code(self, code: str, organization_id: UUID) -> LoanProduct | None:
        """Get loan product by code."""
        query = select(LoanProduct).where(
            and_(
                LoanProduct.code == code,
                LoanProduct.organization_id == organization_id,
                LoanProduct.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_for_organization(
        self, product_id: UUID, organization_id: UUID
    ) -> LoanProduct | None:
        """Get loan product by ID within one tenant."""
        query = select(LoanProduct).where(
            and_(
                LoanProduct.id == product_id,
                LoanProduct.organization_id == organization_id,
                LoanProduct.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_with_details(self, product_id: UUID) -> LoanProduct | None:
        """Get loan product with fees and document checklist."""
        query = (
            select(LoanProduct)
            .options(
                selectinload(LoanProduct.fee_configurations),
                selectinload(LoanProduct.document_checklist),
                selectinload(LoanProduct.base_rate),
            )
            .where(
                and_(
                    LoanProduct.id == product_id,
                    LoanProduct.is_active == True,
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_with_details_for_organization(
        self, product_id: UUID, organization_id: UUID
    ) -> LoanProduct | None:
        """Get loan product with details within one tenant."""
        query = (
            select(LoanProduct)
            .options(
                selectinload(LoanProduct.fee_configurations),
                selectinload(LoanProduct.document_checklist),
                selectinload(LoanProduct.base_rate),
            )
            .where(
                and_(
                    LoanProduct.id == product_id,
                    LoanProduct.organization_id == organization_id,
                    LoanProduct.is_active == True,
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_all_by_organization(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
        search: str | None = None,
        category: str | None = None,
        interest_type: str | None = None,
    ) -> tuple[list[LoanProduct], int]:
        """Get all loan products for an organization with filters."""
        base_query = select(LoanProduct).where(LoanProduct.organization_id == organization_id)

        if not include_inactive:
            base_query = base_query.where(LoanProduct.is_active == True)

        if search:
            search_term = f"%{search}%"
            base_query = base_query.where(
                or_(
                    LoanProduct.code.ilike(search_term),
                    LoanProduct.name.ilike(search_term),
                )
            )

        if category:
            base_query = base_query.where(LoanProduct.category == category)

        if interest_type:
            base_query = base_query.where(LoanProduct.interest_type == interest_type)

        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results — eager-load base_rate so the list response
        # can surface base_rate_value without N+1 queries.
        query = (
            base_query.options(selectinload(LoanProduct.base_rate))
            .order_by(LoanProduct.code)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_active_products(
        self,
        organization_id: UUID,
        category: str | None = None,
    ) -> list[LoanProduct]:
        """Get all active loan products for dropdown lists."""
        query = select(LoanProduct).where(
            and_(
                LoanProduct.organization_id == organization_id,
                LoanProduct.is_active == True,
            )
        )

        if category:
            query = query.where(LoanProduct.category == category)

        query = query.order_by(LoanProduct.name)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_eligible_products(
        self,
        organization_id: UUID,
        entity_type: str,
        amount: float | None = None,
        tenure_months: int | None = None,
    ) -> list[LoanProduct]:
        """Get products that meet eligibility criteria."""
        query = select(LoanProduct).where(
            and_(
                LoanProduct.organization_id == organization_id,
                LoanProduct.eligible_entity_types.contains([entity_type]),
                LoanProduct.is_active == True,
            )
        )

        if amount:
            query = query.where(
                and_(
                    LoanProduct.min_amount <= amount,
                    LoanProduct.max_amount >= amount,
                )
            )

        if tenure_months:
            query = query.where(
                and_(
                    LoanProduct.min_tenure_months <= tenure_months,
                    LoanProduct.max_tenure_months >= tenure_months,
                )
            )

        result = await self.session.execute(query)
        return list(result.scalars().all())
