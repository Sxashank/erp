"""Entity/Borrower service for the lending module."""

from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lending.entity import (
    Entity,
    EntityContact,
    EntityAddress,
    EntityBankAccount,
    EntityRelation,
    EntityFinancial,
)
from app.models.lending.enums import EntityType, EntityStatus, RiskCategory
from app.schemas.lending.entity import (
    EntityCreate,
    EntityUpdate,
    EntityContactCreate,
    EntityContactUpdate,
    EntityAddressCreate,
    EntityAddressUpdate,
    EntityBankAccountCreate,
    EntityBankAccountUpdate,
    EntityRelationCreate,
    EntityRelationUpdate,
    EntityFinancialCreate,
    EntityFinancialUpdate,
)
from app.repositories.lending.entity_repo import (
    EntityRepository,
    EntityContactRepository,
    EntityAddressRepository,
    EntityBankAccountRepository,
    EntityRelationRepository,
    EntityFinancialRepository,
)
from app.core.exceptions import NotFoundException, ConflictException, ValidationException


class EntityService:
    """Service for Entity/Borrower operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = EntityRepository(session)
        self.contact_repo = EntityContactRepository(session)
        self.address_repo = EntityAddressRepository(session)
        self.bank_account_repo = EntityBankAccountRepository(session)
        self.relation_repo = EntityRelationRepository(session)
        self.financial_repo = EntityFinancialRepository(session)

    # =========================================================================
    # Entity CRUD
    # =========================================================================

    async def create_entity(
        self, data: EntityCreate, created_by: UUID
    ) -> Entity:
        """Create a new entity/borrower."""
        # Validate PAN uniqueness
        existing_pan = await self.repo.get_by_pan(data.pan, data.organization_id)
        if existing_pan:
            raise ConflictException(f"Entity with PAN '{data.pan}' already exists")

        # Validate CIN uniqueness for corporates
        if data.cin:
            existing_cin = await self.repo.get_by_cin(data.cin, data.organization_id)
            if existing_cin:
                raise ConflictException(f"Entity with CIN '{data.cin}' already exists")

        # Validate GSTIN uniqueness
        if data.gstin:
            existing_gstin = await self.repo.get_by_gstin(data.gstin, data.organization_id)
            if existing_gstin:
                raise ConflictException(f"Entity with GSTIN '{data.gstin}' already exists")

        # Generate entity code
        entity_code = await self.repo.generate_entity_code(data.organization_id)

        entity = Entity(
            **data.model_dump(),
            entity_code=entity_code,
            created_by=created_by,
        )
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def update_entity(
        self, id: UUID, data: EntityUpdate, updated_by: UUID
    ) -> Entity:
        """Update an entity."""
        entity = await self.repo.get(id)
        if not entity:
            raise NotFoundException("Entity not found")

        # Validate PAN uniqueness if changed
        if data.pan and data.pan != entity.pan:
            existing_pan = await self.repo.get_by_pan(data.pan, entity.organization_id)
            if existing_pan and existing_pan.id != id:
                raise ConflictException(f"Entity with PAN '{data.pan}' already exists")

        # Validate CIN uniqueness if changed
        if data.cin and data.cin != entity.cin:
            existing_cin = await self.repo.get_by_cin(data.cin, entity.organization_id)
            if existing_cin and existing_cin.id != id:
                raise ConflictException(f"Entity with CIN '{data.cin}' already exists")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(entity, field, value)
        entity.updated_by = updated_by

        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def get_entity(self, id: UUID) -> Entity:
        """Get entity by ID."""
        entity = await self.repo.get(id)
        if not entity:
            raise NotFoundException("Entity not found")
        return entity

    async def get_entity_with_details(self, id: UUID) -> Entity:
        """Get entity with all related data."""
        entity = await self.repo.get_with_details(id)
        if not entity:
            raise NotFoundException("Entity not found")
        return entity

    async def get_entity_by_code(
        self, entity_code: str, organization_id: UUID
    ) -> Entity:
        """Get entity by code."""
        entity = await self.repo.get_by_code(entity_code, organization_id)
        if not entity:
            raise NotFoundException(f"Entity with code '{entity_code}' not found")
        return entity

    async def get_all_entities(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
        search: Optional[str] = None,
        entity_type: Optional[EntityType] = None,
        status: Optional[EntityStatus] = None,
        risk_category: Optional[RiskCategory] = None,
        relationship_manager_id: Optional[UUID] = None,
    ) -> Tuple[List[Entity], int]:
        """Get all entities for an organization."""
        return await self.repo.get_all_by_organization(
            organization_id=organization_id,
            skip=skip,
            limit=limit,
            include_inactive=include_inactive,
            search=search,
            entity_type=entity_type,
            status=status,
            risk_category=risk_category,
            relationship_manager_id=relationship_manager_id,
        )

    async def get_active_entities(
        self,
        organization_id: UUID,
        entity_type: Optional[EntityType] = None,
    ) -> List[Entity]:
        """Get active entities for dropdowns."""
        return await self.repo.get_active_entities(organization_id, entity_type)

    async def delete_entity(self, id: UUID, deleted_by: UUID) -> None:
        """Soft delete an entity."""
        entity = await self.repo.get(id)
        if not entity:
            raise NotFoundException("Entity not found")
        entity.soft_delete(deleted_by)
        await self.session.commit()

    # =========================================================================
    # Entity Contact Operations
    # =========================================================================

    async def add_contact(
        self, data: EntityContactCreate, created_by: UUID
    ) -> EntityContact:
        """Add a contact to an entity."""
        # Verify entity exists
        entity = await self.repo.get(data.entity_id)
        if not entity:
            raise NotFoundException("Entity not found")

        contact = EntityContact(
            **data.model_dump(),
            created_by=created_by,
        )
        self.session.add(contact)
        await self.session.commit()
        await self.session.refresh(contact)
        return contact

    async def update_contact(
        self, id: UUID, data: EntityContactUpdate, updated_by: UUID
    ) -> EntityContact:
        """Update an entity contact."""
        contact = await self.contact_repo.get(id)
        if not contact:
            raise NotFoundException("Contact not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(contact, field, value)
        contact.updated_by = updated_by

        await self.session.commit()
        await self.session.refresh(contact)
        return contact

    async def get_entity_contacts(
        self, entity_id: UUID, include_inactive: bool = False
    ) -> List[EntityContact]:
        """Get all contacts for an entity."""
        return await self.contact_repo.get_by_entity(entity_id, include_inactive)

    async def delete_contact(self, id: UUID, deleted_by: UUID) -> None:
        """Soft delete a contact."""
        contact = await self.contact_repo.get(id)
        if not contact:
            raise NotFoundException("Contact not found")
        contact.soft_delete(deleted_by)
        await self.session.commit()

    # =========================================================================
    # Entity Address Operations
    # =========================================================================

    async def add_address(
        self, data: EntityAddressCreate, created_by: UUID
    ) -> EntityAddress:
        """Add an address to an entity."""
        entity = await self.repo.get(data.entity_id)
        if not entity:
            raise NotFoundException("Entity not found")

        address = EntityAddress(
            **data.model_dump(),
            created_by=created_by,
        )
        self.session.add(address)
        await self.session.commit()
        await self.session.refresh(address)
        return address

    async def update_address(
        self, id: UUID, data: EntityAddressUpdate, updated_by: UUID
    ) -> EntityAddress:
        """Update an entity address."""
        address = await self.address_repo.get(id)
        if not address:
            raise NotFoundException("Address not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(address, field, value)
        address.updated_by = updated_by

        await self.session.commit()
        await self.session.refresh(address)
        return address

    async def get_entity_addresses(
        self, entity_id: UUID, include_inactive: bool = False
    ) -> List[EntityAddress]:
        """Get all addresses for an entity."""
        return await self.address_repo.get_by_entity(entity_id, include_inactive)

    async def delete_address(self, id: UUID, deleted_by: UUID) -> None:
        """Soft delete an address."""
        address = await self.address_repo.get(id)
        if not address:
            raise NotFoundException("Address not found")
        address.soft_delete(deleted_by)
        await self.session.commit()

    # =========================================================================
    # Entity Bank Account Operations
    # =========================================================================

    async def add_bank_account(
        self, data: EntityBankAccountCreate, created_by: UUID
    ) -> EntityBankAccount:
        """Add a bank account to an entity."""
        entity = await self.repo.get(data.entity_id)
        if not entity:
            raise NotFoundException("Entity not found")

        # If setting as primary, unset other primary accounts
        if data.is_primary:
            existing_accounts = await self.bank_account_repo.get_by_entity(data.entity_id)
            for account in existing_accounts:
                if account.is_primary:
                    account.is_primary = False

        bank_account = EntityBankAccount(
            **data.model_dump(),
            created_by=created_by,
        )
        self.session.add(bank_account)
        await self.session.commit()
        await self.session.refresh(bank_account)
        return bank_account

    async def update_bank_account(
        self, id: UUID, data: EntityBankAccountUpdate, updated_by: UUID
    ) -> EntityBankAccount:
        """Update a bank account."""
        bank_account = await self.bank_account_repo.get(id)
        if not bank_account:
            raise NotFoundException("Bank account not found")

        # If setting as primary, unset other primary accounts
        if data.is_primary:
            existing_accounts = await self.bank_account_repo.get_by_entity(
                bank_account.entity_id
            )
            for account in existing_accounts:
                if account.id != id and account.is_primary:
                    account.is_primary = False

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(bank_account, field, value)
        bank_account.updated_by = updated_by

        await self.session.commit()
        await self.session.refresh(bank_account)
        return bank_account

    async def get_entity_bank_accounts(
        self, entity_id: UUID, include_inactive: bool = False
    ) -> List[EntityBankAccount]:
        """Get all bank accounts for an entity."""
        return await self.bank_account_repo.get_by_entity(entity_id, include_inactive)

    async def delete_bank_account(self, id: UUID, deleted_by: UUID) -> None:
        """Soft delete a bank account."""
        bank_account = await self.bank_account_repo.get(id)
        if not bank_account:
            raise NotFoundException("Bank account not found")
        bank_account.soft_delete(deleted_by)
        await self.session.commit()

    # =========================================================================
    # Entity Relation Operations
    # =========================================================================

    async def add_relation(
        self, data: EntityRelationCreate, created_by: UUID
    ) -> EntityRelation:
        """Add a relation to an entity."""
        entity = await self.repo.get(data.entity_id)
        if not entity:
            raise NotFoundException("Entity not found")

        relation = EntityRelation(
            **data.model_dump(),
            created_by=created_by,
        )
        self.session.add(relation)
        await self.session.commit()
        await self.session.refresh(relation)
        return relation

    async def update_relation(
        self, id: UUID, data: EntityRelationUpdate, updated_by: UUID
    ) -> EntityRelation:
        """Update an entity relation."""
        relation = await self.relation_repo.get(id)
        if not relation:
            raise NotFoundException("Relation not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(relation, field, value)
        relation.updated_by = updated_by

        await self.session.commit()
        await self.session.refresh(relation)
        return relation

    async def get_entity_relations(
        self, entity_id: UUID, include_inactive: bool = False
    ) -> List[EntityRelation]:
        """Get all relations for an entity."""
        return await self.relation_repo.get_by_entity(entity_id, include_inactive)

    async def delete_relation(self, id: UUID, deleted_by: UUID) -> None:
        """Soft delete a relation."""
        relation = await self.relation_repo.get(id)
        if not relation:
            raise NotFoundException("Relation not found")
        relation.soft_delete(deleted_by)
        await self.session.commit()

    # =========================================================================
    # Entity Financial Operations
    # =========================================================================

    async def add_financial(
        self, data: EntityFinancialCreate, created_by: UUID
    ) -> EntityFinancial:
        """Add financial data for an entity."""
        entity = await self.repo.get(data.entity_id)
        if not entity:
            raise NotFoundException("Entity not found")

        # Check if financial for this year already exists
        existing = await self.financial_repo.get_by_financial_year(
            data.entity_id, data.financial_year
        )
        if existing:
            raise ConflictException(
                f"Financial data for year '{data.financial_year}' already exists"
            )

        financial = EntityFinancial(
            **data.model_dump(),
            created_by=created_by,
        )
        self.session.add(financial)
        await self.session.commit()
        await self.session.refresh(financial)
        return financial

    async def update_financial(
        self, id: UUID, data: EntityFinancialUpdate, updated_by: UUID
    ) -> EntityFinancial:
        """Update entity financial data."""
        financial = await self.financial_repo.get(id)
        if not financial:
            raise NotFoundException("Financial data not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(financial, field, value)
        financial.updated_by = updated_by

        await self.session.commit()
        await self.session.refresh(financial)
        return financial

    async def get_entity_financials(
        self, entity_id: UUID, include_inactive: bool = False
    ) -> List[EntityFinancial]:
        """Get all financial data for an entity."""
        return await self.financial_repo.get_by_entity(entity_id, include_inactive)

    async def get_latest_financial(
        self, entity_id: UUID
    ) -> Optional[EntityFinancial]:
        """Get latest financial data for an entity."""
        return await self.financial_repo.get_latest_financial(entity_id)

    async def delete_financial(self, id: UUID, deleted_by: UUID) -> None:
        """Soft delete financial data."""
        financial = await self.financial_repo.get(id)
        if not financial:
            raise NotFoundException("Financial data not found")
        financial.soft_delete(deleted_by)
        await self.session.commit()
