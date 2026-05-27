"""Loan Product service for the lending module."""

from datetime import date
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lending.masters import (
    ChecklistItemCatalog,
    DayCountConvention as DayCountConventionMaster,
    LendingOption,
)
from app.models.lending.product import (
    LoanProduct,
    InterestRate,
    FeeMaster,
    ProductFee,
    DocumentChecklist,
)
from app.models.lending.enums import (
    FeeType,
    FeeCollectionStage,
    DocumentCategory,
    DocumentStage,
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

_DOCUMENT_CATEGORY_MAP: dict[str, DocumentCategory] = {
    "KYC": DocumentCategory.KYC,
    "FINANCIAL": DocumentCategory.FINANCIAL,
    "LEGAL": DocumentCategory.LEGAL,
    "INSURANCE": DocumentCategory.INSURANCE,
    "REGULATORY": DocumentCategory.REGULATORY,
    "PROPERTY": DocumentCategory.SECURITY,
    "VESSEL": DocumentCategory.SECURITY,
    "PORT": DocumentCategory.PROJECT,
    "OTHER": DocumentCategory.PROJECT,
}

_DOCUMENT_STAGE_MAP: dict[str, DocumentStage] = {stage.value: stage for stage in DocumentStage}


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

    async def create_fee_master(self, data: FeeMasterCreate, created_by: UUID) -> FeeMaster:
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

    async def _validate_lending_option(
        self,
        organization_id: UUID,
        option_group: str,
        code: str,
        label: str,
    ) -> str:
        """Ensure governed option values come from the tenant master catalog."""
        normalised_code = code.strip().upper()
        if not normalised_code:
            raise ValidationException(f"{label} is required")
        result = await self.session.execute(
            select(LendingOption.id).where(
                LendingOption.organization_id == organization_id,
                LendingOption.option_group == option_group,
                LendingOption.code == normalised_code,
                LendingOption.is_active == True,
                LendingOption.deleted_at.is_(None),
            )
        )
        if result.scalar_one_or_none() is None:
            raise ValidationException(
                f"{label} '{normalised_code}' is not configured in lending masters"
            )
        return normalised_code

    async def _validate_lending_options(
        self,
        organization_id: UUID,
        option_group: str,
        codes: list[str] | None,
        label: str,
    ) -> list[str] | None:
        if codes is None:
            return None
        normalised_codes = [code.strip().upper() for code in codes if code and code.strip()]
        if len(normalised_codes) != len(codes):
            raise ValidationException(f"{label} cannot contain blank values")
        for code in normalised_codes:
            await self._validate_lending_option(organization_id, option_group, code, label)
        return normalised_codes

    async def _validate_day_count_convention(self, organization_id: UUID, code: str) -> None:
        """Ensure day-count values come from the lending master table."""
        result = await self.session.execute(
            select(DayCountConventionMaster.id).where(
                DayCountConventionMaster.organization_id == organization_id,
                DayCountConventionMaster.code == code,
                DayCountConventionMaster.is_active == True,
                DayCountConventionMaster.deleted_at.is_(None),
            )
        )
        if result.scalar_one_or_none() is None:
            raise ValidationException(
                f"Day count convention '{code}' is not configured in lending masters"
            )

    async def create_product(self, data: LoanProductCreate, created_by: UUID) -> LoanProduct:
        """Create a new loan product."""
        existing = await self.product_repo.get_by_code(data.code, data.organization_id)
        if existing:
            raise ConflictException(f"Product with code '{data.code}' already exists")

        if data.organization_id is None:
            raise ValidationException("Product organization is required")
        data.category = await self._validate_lending_option(
            data.organization_id, "PRODUCT_CATEGORY", data.category, "Product category"
        )
        data.interest_type = await self._validate_lending_option(
            data.organization_id, "RATE_TYPE", data.interest_type, "Interest type"
        )
        await self._validate_day_count_convention(data.organization_id, data.day_count_convention)
        if data.rate_reset_frequency:
            data.rate_reset_frequency = await self._validate_lending_option(
                data.organization_id,
                "RATE_RESET_FREQUENCY",
                data.rate_reset_frequency,
                "Rate reset frequency",
            )
        data.allowed_repayment_frequencies = (
            await self._validate_lending_options(
                data.organization_id,
                "REPAYMENT_FREQUENCY",
                data.allowed_repayment_frequencies,
                "Repayment frequency",
            )
            or []
        )
        data.default_repayment_frequency = await self._validate_lending_option(
            data.organization_id,
            "REPAYMENT_FREQUENCY",
            data.default_repayment_frequency,
            "Default repayment frequency",
        )
        if data.default_repayment_frequency not in data.allowed_repayment_frequencies:
            raise ValidationException(
                "Default repayment frequency must be one of the allowed frequencies"
            )
        data.allowed_repayment_modes = (
            await self._validate_lending_options(
                data.organization_id,
                "REPAYMENT_MODE",
                data.allowed_repayment_modes,
                "Repayment mode",
            )
            or []
        )
        data.default_repayment_mode = await self._validate_lending_option(
            data.organization_id,
            "REPAYMENT_MODE",
            data.default_repayment_mode,
            "Default repayment mode",
        )
        if data.default_repayment_mode not in data.allowed_repayment_modes:
            raise ValidationException("Default repayment mode must be one of the allowed modes")
        data.eligible_entity_types = (
            await self._validate_lending_options(
                data.organization_id,
                "ENTITY_TYPE_CORPORATE",
                data.eligible_entity_types,
                "Eligible entity type",
            )
            or []
        )

        # Validate base rate exists if floating
        if data.interest_type == "FLOATING" and data.base_rate_id:
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
        self, organization_id: UUID, id: UUID, data: LoanProductUpdate, updated_by: UUID
    ) -> LoanProduct:
        """Update a loan product."""
        product = await self.product_repo.get_for_organization(id, organization_id)
        if not product:
            raise NotFoundException("Loan product not found")

        if data.category is not None:
            data.category = await self._validate_lending_option(
                product.organization_id, "PRODUCT_CATEGORY", data.category, "Product category"
            )
        if data.interest_type is not None:
            data.interest_type = await self._validate_lending_option(
                product.organization_id, "RATE_TYPE", data.interest_type, "Interest type"
            )
        if data.day_count_convention is not None:
            await self._validate_day_count_convention(
                product.organization_id, data.day_count_convention
            )
        if data.rate_reset_frequency is not None:
            data.rate_reset_frequency = await self._validate_lending_option(
                product.organization_id,
                "RATE_RESET_FREQUENCY",
                data.rate_reset_frequency,
                "Rate reset frequency",
            )

        next_allowed_frequencies = (
            data.allowed_repayment_frequencies
            if data.allowed_repayment_frequencies is not None
            else list(product.allowed_repayment_frequencies or [])
        )
        next_default_frequency = (
            data.default_repayment_frequency or product.default_repayment_frequency
        )
        if data.allowed_repayment_frequencies is not None:
            data.allowed_repayment_frequencies = (
                await self._validate_lending_options(
                    product.organization_id,
                    "REPAYMENT_FREQUENCY",
                    data.allowed_repayment_frequencies,
                    "Repayment frequency",
                )
                or []
            )
            next_allowed_frequencies = data.allowed_repayment_frequencies
        if data.default_repayment_frequency is not None:
            data.default_repayment_frequency = await self._validate_lending_option(
                product.organization_id,
                "REPAYMENT_FREQUENCY",
                data.default_repayment_frequency,
                "Default repayment frequency",
            )
            next_default_frequency = data.default_repayment_frequency
        if next_default_frequency not in next_allowed_frequencies:
            raise ValidationException(
                "Default repayment frequency must be one of the allowed frequencies"
            )

        next_allowed_modes = (
            data.allowed_repayment_modes
            if data.allowed_repayment_modes is not None
            else list(product.allowed_repayment_modes or [])
        )
        next_default_mode = data.default_repayment_mode or product.default_repayment_mode
        if data.allowed_repayment_modes is not None:
            data.allowed_repayment_modes = (
                await self._validate_lending_options(
                    product.organization_id,
                    "REPAYMENT_MODE",
                    data.allowed_repayment_modes,
                    "Repayment mode",
                )
                or []
            )
            next_allowed_modes = data.allowed_repayment_modes
        if data.default_repayment_mode is not None:
            data.default_repayment_mode = await self._validate_lending_option(
                product.organization_id,
                "REPAYMENT_MODE",
                data.default_repayment_mode,
                "Default repayment mode",
            )
            next_default_mode = data.default_repayment_mode
        if next_default_mode not in next_allowed_modes:
            raise ValidationException("Default repayment mode must be one of the allowed modes")
        if data.eligible_entity_types is not None:
            data.eligible_entity_types = (
                await self._validate_lending_options(
                    product.organization_id,
                    "ENTITY_TYPE_CORPORATE",
                    data.eligible_entity_types,
                    "Eligible entity type",
                )
                or []
            )

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

    async def get_product(self, organization_id: UUID, id: UUID) -> LoanProduct:
        """Get loan product by ID."""
        product = await self.product_repo.get_for_organization(id, organization_id)
        if not product:
            raise NotFoundException("Loan product not found")
        return product

    async def get_product_with_details(self, organization_id: UUID, id: UUID) -> LoanProduct:
        """Get loan product with fees and document checklist."""
        product = await self.product_repo.get_with_details_for_organization(id, organization_id)
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
        category: Optional[str] = None,
        interest_type: Optional[str] = None,
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
        category: Optional[str] = None,
    ) -> List[LoanProduct]:
        """Get active products for dropdowns."""
        return await self.product_repo.get_active_products(organization_id, category)

    async def get_eligible_products(
        self,
        organization_id: UUID,
        entity_type: str,
        amount: Optional[float] = None,
        tenure_months: Optional[int] = None,
    ) -> List[LoanProduct]:
        """Get products meeting eligibility criteria."""
        normalised_entity_type = await self._validate_lending_option(
            organization_id,
            "ENTITY_TYPE_CORPORATE",
            entity_type,
            "Entity type",
        )
        return await self.product_repo.get_eligible_products(
            organization_id=organization_id,
            entity_type=normalised_entity_type,
            amount=amount,
            tenure_months=tenure_months,
        )

    async def delete_product(self, organization_id: UUID, id: UUID, deleted_by: UUID) -> None:
        """Soft delete a loan product."""
        product = await self.product_repo.get_for_organization(id, organization_id)
        if not product:
            raise NotFoundException("Loan product not found")
        product.soft_delete(deleted_by)
        await self.session.flush()

    # =========================================================================
    # Product Fee Operations
    # =========================================================================

    async def add_product_fee(
        self, organization_id: UUID, data: ProductFeeCreate, created_by: UUID
    ) -> ProductFee:
        """Add a fee to a product."""
        product = await self.product_repo.get_for_organization(data.product_id, organization_id)
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
        self, organization_id: UUID, id: UUID, data: ProductFeeUpdate, updated_by: UUID
    ) -> ProductFee:
        """Update a product fee."""
        product_fee = await self.product_fee_repo.get(id)
        if not product_fee:
            raise NotFoundException("Product fee not found")
        product = await self.product_repo.get_for_organization(
            product_fee.product_id, organization_id
        )
        if not product:
            raise NotFoundException("Product fee not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(product_fee, field, value)
        product_fee.updated_by = updated_by

        await self.session.flush()
        await self.session.refresh(product_fee)
        return product_fee

    async def get_product_fees(
        self, organization_id: UUID, product_id: UUID, include_inactive: bool = False
    ) -> List[ProductFee]:
        """Get all fees for a product."""
        product = await self.product_repo.get_for_organization(product_id, organization_id)
        if not product:
            raise NotFoundException("Product not found")
        return await self.product_fee_repo.get_by_product(product_id, include_inactive)

    async def delete_product_fee(self, organization_id: UUID, id: UUID, deleted_by: UUID) -> None:
        """Soft delete a product fee."""
        product_fee = await self.product_fee_repo.get(id)
        if not product_fee:
            raise NotFoundException("Product fee not found")
        product = await self.product_repo.get_for_organization(
            product_fee.product_id, organization_id
        )
        if not product:
            raise NotFoundException("Product fee not found")
        product_fee.soft_delete(deleted_by)
        await self.session.flush()

    # =========================================================================
    # Document Checklist Operations
    # =========================================================================

    async def _get_catalog_item_for_product(
        self,
        product: LoanProduct,
        catalog_item_id: UUID,
    ) -> ChecklistItemCatalog:
        result = await self.session.execute(
            select(ChecklistItemCatalog).where(
                ChecklistItemCatalog.id == catalog_item_id,
                ChecklistItemCatalog.organization_id == product.organization_id,
                ChecklistItemCatalog.deleted_at.is_(None),
                ChecklistItemCatalog.is_active.is_(True),
            )
        )
        catalog_item = result.scalar_one_or_none()
        if catalog_item is None:
            raise NotFoundException("Checklist catalog item not found for this organization")
        return catalog_item

    def _document_fields_from_catalog(
        self, catalog_item: ChecklistItemCatalog
    ) -> dict[str, object]:
        category = _DOCUMENT_CATEGORY_MAP.get(catalog_item.category)
        if category is None:
            raise ValidationException(
                "Checklist catalog category "
                f"'{catalog_item.category}' cannot be used as a borrower document requirement"
            )
        required_at_stage = _DOCUMENT_STAGE_MAP.get(
            catalog_item.stage,
            DocumentStage.APPLICATION,
        )
        return {
            "catalog_item_id": catalog_item.id,
            "code": catalog_item.code,
            "name": catalog_item.label,
            "description": catalog_item.description,
            "category": category,
            "required_at_stage": required_at_stage,
        }

    async def add_document_checklist(
        self, organization_id: UUID, data: DocumentChecklistCreate, created_by: UUID
    ) -> DocumentChecklist:
        """Add a document to product checklist."""
        product = await self.product_repo.get_for_organization(data.product_id, organization_id)
        if not product:
            raise NotFoundException("Product not found")
        catalog_item = await self._get_catalog_item_for_product(
            product,
            data.catalog_item_id,
        )
        catalog_fields = self._document_fields_from_catalog(catalog_item)

        existing = await self.checklist_repo.get_by_code(
            str(catalog_fields["code"]), data.product_id
        )
        if existing:
            raise ConflictException(
                f"Document with code '{catalog_fields['code']}' already exists for this product"
            )

        payload = data.model_dump()
        payload["applicable_entity_types"] = await self._validate_lending_options(
            product.organization_id,
            "ENTITY_TYPE_CORPORATE",
            payload.get("applicable_entity_types"),
            "Applicable entity type",
        )
        payload.update(catalog_fields)
        checklist = DocumentChecklist(
            **payload,
            created_by=created_by,
        )
        self.session.add(checklist)
        await self.session.flush()
        await self.session.refresh(checklist)
        return checklist

    async def update_document_checklist(
        self, organization_id: UUID, id: UUID, data: DocumentChecklistUpdate, updated_by: UUID
    ) -> DocumentChecklist:
        """Update a document checklist item."""
        checklist = await self.checklist_repo.get(id)
        if not checklist:
            raise NotFoundException("Document checklist item not found")
        product = await self.product_repo.get_for_organization(
            checklist.product_id, organization_id
        )
        if not product:
            raise NotFoundException("Document checklist item not found")

        update_data = data.model_dump(exclude_unset=True)
        if "applicable_entity_types" in update_data:
            update_data["applicable_entity_types"] = await self._validate_lending_options(
                product.organization_id,
                "ENTITY_TYPE_CORPORATE",
                update_data.get("applicable_entity_types"),
                "Applicable entity type",
            )
        catalog_item_id = update_data.pop("catalog_item_id", None)
        if catalog_item_id is not None:
            catalog_item = await self._get_catalog_item_for_product(
                product,
                catalog_item_id,
            )
            update_data.update(self._document_fields_from_catalog(catalog_item))

        for field, value in update_data.items():
            setattr(checklist, field, value)
        checklist.updated_by = updated_by

        await self.session.flush()
        await self.session.refresh(checklist)
        return checklist

    async def get_product_checklist(
        self, organization_id: UUID, product_id: UUID, include_inactive: bool = False
    ) -> List[DocumentChecklist]:
        """Get document checklist for a product."""
        product = await self.product_repo.get_for_organization(product_id, organization_id)
        if not product:
            raise NotFoundException("Product not found")
        return await self.checklist_repo.get_by_product(product_id, include_inactive)

    async def get_checklist_by_stage(
        self,
        organization_id: UUID,
        product_id: UUID,
        stage: DocumentStage,
        entity_type: Optional[str] = None,
    ) -> List[DocumentChecklist]:
        """Get document checklist for a specific stage."""
        product = await self.product_repo.get_for_organization(product_id, organization_id)
        if not product:
            raise NotFoundException("Product not found")
        return await self.checklist_repo.get_by_stage(product_id, stage, entity_type)

    async def get_mandatory_documents(
        self,
        organization_id: UUID,
        product_id: UUID,
        stage: Optional[DocumentStage] = None,
        entity_type: Optional[str] = None,
    ) -> List[DocumentChecklist]:
        """Get mandatory documents for a product."""
        product = await self.product_repo.get_for_organization(product_id, organization_id)
        if not product:
            raise NotFoundException("Product not found")
        return await self.checklist_repo.get_mandatory_documents(product_id, stage, entity_type)

    async def delete_document_checklist(
        self, organization_id: UUID, id: UUID, deleted_by: UUID
    ) -> None:
        """Soft delete a document checklist item."""
        checklist = await self.checklist_repo.get(id)
        if not checklist:
            raise NotFoundException("Document checklist item not found")
        product = await self.product_repo.get_for_organization(
            checklist.product_id, organization_id
        )
        if not product:
            raise NotFoundException("Document checklist item not found")
        checklist.soft_delete(deleted_by)
        await self.session.flush()
