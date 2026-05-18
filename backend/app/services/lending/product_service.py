"""Loan Product service for the lending module."""

from datetime import date
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lending.product import (
    LoanProduct,
    InterestRate,
    FeeMaster,
    ProductFee,
    DocumentChecklist,
)
from app.models.lending.enums import (
    ProductCategory,
    InterestType,
    FeeType,
    FeeCollectionStage,
    DocumentCategory,
    DocumentStage,
    EntityType,
)
from app.schemas.lending.product import (
    LoanProductCreate,
    LoanProductUpdate,
    InterestRateCreate,
    InterestRateUpdate,
    FeeMasterCreate,
    FeeMasterUpdate,
    ProductFeeCreate,
    ProductFeeUpdate,
    DocumentChecklistCreate,
    DocumentChecklistUpdate,
)
from app.repositories.lending.product_repo import (
    LoanProductRepository,
    InterestRateRepository,
    FeeMasterRepository,
    ProductFeeRepository,
    DocumentChecklistRepository,
)
from app.core.exceptions import NotFoundException, ConflictException, ValidationException


class ProductService:
    """Service for Loan Product operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.product_repo = LoanProductRepository(session)
        self.rate_repo = InterestRateRepository(session)
        self.fee_master_repo = FeeMasterRepository(session)
        self.product_fee_repo = ProductFeeRepository(session)
        self.checklist_repo = DocumentChecklistRepository(session)

    # =========================================================================
    # Interest Rate Operations
    # =========================================================================

    async def create_interest_rate(
        self, data: InterestRateCreate, created_by: UUID
    ) -> InterestRate:
        """Create a new interest rate."""
        existing = await self.rate_repo.get_by_code(data.code, data.organization_id)
        if existing:
            raise ConflictException(f"Interest rate with code '{data.code}' already exists")

        rate = InterestRate(
            **data.model_dump(),
            created_by=created_by,
        )
        self.session.add(rate)
        await self.session.flush()
        await self.session.refresh(rate)
        return rate

    async def update_interest_rate(
        self, id: UUID, data: InterestRateUpdate, updated_by: UUID
    ) -> InterestRate:
        """Update an interest rate."""
        rate = await self.rate_repo.get(id)
        if not rate:
            raise NotFoundException("Interest rate not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(rate, field, value)
        rate.updated_by = updated_by

        await self.session.flush()
        await self.session.refresh(rate)
        return rate

    async def get_interest_rate(self, id: UUID) -> InterestRate:
        """Get interest rate by ID."""
        rate = await self.rate_repo.get(id)
        if not rate:
            raise NotFoundException("Interest rate not found")
        return rate

    async def get_all_interest_rates(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
        effective_date: Optional[date] = None,
    ) -> Tuple[List[InterestRate], int]:
        """Get all interest rates."""
        return await self.rate_repo.get_all_by_organization(
            organization_id=organization_id,
            skip=skip,
            limit=limit,
            include_inactive=include_inactive,
            effective_date=effective_date,
        )

    # =========================================================================
    # Fee Master Operations
    # =========================================================================

    async def create_fee_master(
        self, data: FeeMasterCreate, created_by: UUID
    ) -> FeeMaster:
        """Create a new fee master."""
        existing = await self.fee_master_repo.get_by_code(data.code, data.organization_id)
        if existing:
            raise ConflictException(f"Fee with code '{data.code}' already exists")

        fee = FeeMaster(
            **data.model_dump(),
            created_by=created_by,
        )
        self.session.add(fee)
        await self.session.flush()
        await self.session.refresh(fee)
        return fee

    async def update_fee_master(
        self, id: UUID, data: FeeMasterUpdate, updated_by: UUID
    ) -> FeeMaster:
        """Update a fee master."""
        fee = await self.fee_master_repo.get(id)
        if not fee:
            raise NotFoundException("Fee master not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(fee, field, value)
        fee.updated_by = updated_by

        await self.session.flush()
        await self.session.refresh(fee)
        return fee

    async def get_fee_master(self, id: UUID) -> FeeMaster:
        """Get fee master by ID."""
        fee = await self.fee_master_repo.get(id)
        if not fee:
            raise NotFoundException("Fee master not found")
        return fee

    async def get_all_fee_masters(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
        fee_type: Optional[FeeType] = None,
    ) -> Tuple[List[FeeMaster], int]:
        """Get all fee masters."""
        return await self.fee_master_repo.get_all_by_organization(
            organization_id=organization_id,
            skip=skip,
            limit=limit,
            include_inactive=include_inactive,
            fee_type=fee_type,
        )

    # =========================================================================
    # Loan Product Operations
    # =========================================================================

    async def create_product(
        self, data: LoanProductCreate, created_by: UUID
    ) -> LoanProduct:
        """Create a new loan product."""
        existing = await self.product_repo.get_by_code(data.code, data.organization_id)
        if existing:
            raise ConflictException(f"Product with code '{data.code}' already exists")

        # Validate base rate exists if floating
        if data.interest_type == InterestType.FLOATING and data.base_rate_id:
            rate = await self.rate_repo.get(data.base_rate_id)
            if not rate:
                raise NotFoundException("Base rate not found")

        product = LoanProduct(
            **data.model_dump(),
            created_by=created_by,
        )
        self.session.add(product)
        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def update_product(
        self, id: UUID, data: LoanProductUpdate, updated_by: UUID
    ) -> LoanProduct:
        """Update a loan product."""
        product = await self.product_repo.get(id)
        if not product:
            raise NotFoundException("Loan product not found")

        # Validate base rate if being changed
        if data.base_rate_id:
            rate = await self.rate_repo.get(data.base_rate_id)
            if not rate:
                raise NotFoundException("Base rate not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product, field, value)
        product.updated_by = updated_by

        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def get_product(self, id: UUID) -> LoanProduct:
        """Get loan product by ID."""
        product = await self.product_repo.get(id)
        if not product:
            raise NotFoundException("Loan product not found")
        return product

    async def get_product_with_details(self, id: UUID) -> LoanProduct:
        """Get loan product with fees and document checklist."""
        product = await self.product_repo.get_with_details(id)
        if not product:
            raise NotFoundException("Loan product not found")
        return product

    async def get_all_products(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
        search: Optional[str] = None,
        category: Optional[ProductCategory] = None,
        interest_type: Optional[InterestType] = None,
    ) -> Tuple[List[LoanProduct], int]:
        """Get all loan products."""
        return await self.product_repo.get_all_by_organization(
            organization_id=organization_id,
            skip=skip,
            limit=limit,
            include_inactive=include_inactive,
            search=search,
            category=category,
            interest_type=interest_type,
        )

    async def get_active_products(
        self,
        organization_id: UUID,
        category: Optional[ProductCategory] = None,
    ) -> List[LoanProduct]:
        """Get active products for dropdowns."""
        return await self.product_repo.get_active_products(organization_id, category)

    async def get_eligible_products(
        self,
        organization_id: UUID,
        entity_type: EntityType,
        amount: Optional[float] = None,
        tenure_months: Optional[int] = None,
    ) -> List[LoanProduct]:
        """Get products meeting eligibility criteria."""
        return await self.product_repo.get_eligible_products(
            organization_id=organization_id,
            entity_type=entity_type,
            amount=amount,
            tenure_months=tenure_months,
        )

    async def delete_product(self, id: UUID, deleted_by: UUID) -> None:
        """Soft delete a loan product."""
        product = await self.product_repo.get(id)
        if not product:
            raise NotFoundException("Loan product not found")
        product.soft_delete(deleted_by)
        await self.session.flush()

    # =========================================================================
    # Product Fee Operations
    # =========================================================================

    async def add_product_fee(
        self, data: ProductFeeCreate, created_by: UUID
    ) -> ProductFee:
        """Add a fee to a product."""
        product = await self.product_repo.get(data.product_id)
        if not product:
            raise NotFoundException("Product not found")

        fee_master = await self.fee_master_repo.get(data.fee_master_id)
        if not fee_master:
            raise NotFoundException("Fee master not found")

        product_fee = ProductFee(
            **data.model_dump(),
            created_by=created_by,
        )
        self.session.add(product_fee)
        await self.session.flush()
        await self.session.refresh(product_fee)
        return product_fee

    async def update_product_fee(
        self, id: UUID, data: ProductFeeUpdate, updated_by: UUID
    ) -> ProductFee:
        """Update a product fee."""
        product_fee = await self.product_fee_repo.get(id)
        if not product_fee:
            raise NotFoundException("Product fee not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product_fee, field, value)
        product_fee.updated_by = updated_by

        await self.session.flush()
        await self.session.refresh(product_fee)
        return product_fee

    async def get_product_fees(
        self, product_id: UUID, include_inactive: bool = False
    ) -> List[ProductFee]:
        """Get all fees for a product."""
        return await self.product_fee_repo.get_by_product(product_id, include_inactive)

    async def delete_product_fee(self, id: UUID, deleted_by: UUID) -> None:
        """Soft delete a product fee."""
        product_fee = await self.product_fee_repo.get(id)
        if not product_fee:
            raise NotFoundException("Product fee not found")
        product_fee.soft_delete(deleted_by)
        await self.session.flush()

    # =========================================================================
    # Document Checklist Operations
    # =========================================================================

    async def add_document_checklist(
        self, data: DocumentChecklistCreate, created_by: UUID
    ) -> DocumentChecklist:
        """Add a document to product checklist."""
        product = await self.product_repo.get(data.product_id)
        if not product:
            raise NotFoundException("Product not found")

        existing = await self.checklist_repo.get_by_code(
            data.document_code, data.product_id
        )
        if existing:
            raise ConflictException(
                f"Document with code '{data.document_code}' already exists for this product"
            )

        checklist = DocumentChecklist(
            **data.model_dump(),
            created_by=created_by,
        )
        self.session.add(checklist)
        await self.session.flush()
        await self.session.refresh(checklist)
        return checklist

    async def update_document_checklist(
        self, id: UUID, data: DocumentChecklistUpdate, updated_by: UUID
    ) -> DocumentChecklist:
        """Update a document checklist item."""
        checklist = await self.checklist_repo.get(id)
        if not checklist:
            raise NotFoundException("Document checklist item not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(checklist, field, value)
        checklist.updated_by = updated_by

        await self.session.flush()
        await self.session.refresh(checklist)
        return checklist

    async def get_product_checklist(
        self, product_id: UUID, include_inactive: bool = False
    ) -> List[DocumentChecklist]:
        """Get document checklist for a product."""
        return await self.checklist_repo.get_by_product(product_id, include_inactive)

    async def get_checklist_by_stage(
        self,
        product_id: UUID,
        stage: DocumentStage,
        entity_type: Optional[EntityType] = None,
    ) -> List[DocumentChecklist]:
        """Get document checklist for a specific stage."""
        return await self.checklist_repo.get_by_stage(product_id, stage, entity_type)

    async def get_mandatory_documents(
        self,
        product_id: UUID,
        stage: Optional[DocumentStage] = None,
        entity_type: Optional[EntityType] = None,
    ) -> List[DocumentChecklist]:
        """Get mandatory documents for a product."""
        return await self.checklist_repo.get_mandatory_documents(
            product_id, stage, entity_type
        )

    async def delete_document_checklist(self, id: UUID, deleted_by: UUID) -> None:
        """Soft delete a document checklist item."""
        checklist = await self.checklist_repo.get(id)
        if not checklist:
            raise NotFoundException("Document checklist item not found")
        checklist.soft_delete(deleted_by)
        await self.session.flush()
