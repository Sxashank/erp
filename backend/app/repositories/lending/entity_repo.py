"""Entity/Borrower repositories for the lending module."""

from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.lending.entity import (
    Entity,
    EntityAddress,
    EntityBankAccount,
    EntityContact,
    EntityFinancial,
    EntityRelation,
)
from app.models.lending.enums import EntityStatus, EntityType, RiskCategory
from app.repositories.base import BaseRepository


class EntityRepository(BaseRepository[Entity]):
    """Repository for Entity/Borrower operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(Entity, session)

    async def get_by_code(self, entity_code: str, organization_id: UUID) -> Entity | None:
        """Get entity by code within an organization."""
        query = select(Entity).where(
            and_(
                Entity.entity_code == entity_code,
                Entity.organization_id == organization_id,
                Entity.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_pan(self, pan: str, organization_id: UUID) -> Entity | None:
        """Get entity by PAN within an organization."""
        query = select(Entity).where(
            and_(
                Entity.pan == pan.upper(),
                Entity.organization_id == organization_id,
                Entity.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_cin(self, cin: str, organization_id: UUID) -> Entity | None:
        """Get entity by CIN within an organization."""
        query = select(Entity).where(
            and_(
                Entity.cin == cin.upper(),
                Entity.organization_id == organization_id,
                Entity.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_gstin(self, gstin: str, organization_id: UUID) -> Entity | None:
        """Get entity by GSTIN within an organization."""
        query = select(Entity).where(
            and_(
                Entity.gstin == gstin.upper(),
                Entity.organization_id == organization_id,
                Entity.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_with_details(self, entity_id: UUID) -> Entity | None:
        """Get entity with all related data (contacts, addresses, etc.)."""
        query = (
            select(Entity)
            .options(
                selectinload(Entity.contacts),
                selectinload(Entity.addresses),
                selectinload(Entity.bank_accounts),
                selectinload(Entity.relations),
                selectinload(Entity.financials),
            )
            .where(
                and_(
                    Entity.id == entity_id,
                    Entity.is_active == True,
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
        entity_type: EntityType | None = None,
        status: EntityStatus | None = None,
        risk_category: RiskCategory | None = None,
        relationship_manager_id: UUID | None = None,
    ) -> tuple[list[Entity], int]:
        """Get all entities for an organization with filters."""
        base_query = select(Entity).where(Entity.organization_id == organization_id)

        if not include_inactive:
            base_query = base_query.where(Entity.is_active == True)

        if search:
            search_term = f"%{search}%"
            base_query = base_query.where(
                or_(
                    Entity.entity_code.ilike(search_term),
                    Entity.legal_name.ilike(search_term),
                    Entity.trade_name.ilike(search_term),
                    Entity.pan.ilike(search_term),
                    Entity.gstin.ilike(search_term),
                    Entity.cin.ilike(search_term),
                )
            )

        if entity_type:
            base_query = base_query.where(Entity.entity_type == entity_type)

        if status:
            base_query = base_query.where(Entity.status == status)

        if risk_category:
            base_query = base_query.where(Entity.risk_category == risk_category)

        if relationship_manager_id:
            base_query = base_query.where(Entity.relationship_manager_id == relationship_manager_id)

        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = base_query.order_by(Entity.entity_code).offset(skip).limit(limit)
        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_active_entities(
        self,
        organization_id: UUID,
        entity_type: EntityType | None = None,
    ) -> list[Entity]:
        """Get all active entities for dropdown lists."""
        query = select(Entity).where(
            and_(
                Entity.organization_id == organization_id,
                Entity.is_active == True,
                Entity.status == EntityStatus.ACTIVE,
            )
        )

        if entity_type:
            query = query.where(Entity.entity_type == entity_type)

        query = query.order_by(Entity.legal_name)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def generate_entity_code(self, organization_id: UUID, prefix: str = "ENT") -> str:
        """Generate next entity code."""
        import datetime

        year = datetime.date.today().year
        pattern = f"{prefix}/{year}/%"

        query = select(func.max(Entity.entity_code)).where(
            and_(
                Entity.organization_id == organization_id,
                Entity.entity_code.like(pattern),
            )
        )
        result = await self.session.execute(query)
        max_code = result.scalar()

        if max_code:
            try:
                num = int(max_code.split("/")[-1]) + 1
            except ValueError:
                num = 1
        else:
            num = 1

        return f"{prefix}/{year}/{num:05d}"


class EntityContactRepository(BaseRepository[EntityContact]):
    """Repository for EntityContact operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(EntityContact, session)

    async def get_by_entity(
        self, entity_id: UUID, include_inactive: bool = False
    ) -> list[EntityContact]:
        """Get all contacts for an entity."""
        query = select(EntityContact).where(EntityContact.entity_id == entity_id)
        if not include_inactive:
            query = query.where(EntityContact.is_active == True)
        query = query.order_by(EntityContact.first_name, EntityContact.last_name)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_authorized_signatories(self, entity_id: UUID) -> list[EntityContact]:
        """Get authorized signatories for an entity."""
        query = select(EntityContact).where(
            and_(
                EntityContact.entity_id == entity_id,
                EntityContact.is_authorized_signatory == True,
                EntityContact.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())


class EntityAddressRepository(BaseRepository[EntityAddress]):
    """Repository for EntityAddress operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(EntityAddress, session)

    async def get_by_entity(
        self, entity_id: UUID, include_inactive: bool = False
    ) -> list[EntityAddress]:
        """Get all addresses for an entity."""
        query = select(EntityAddress).where(EntityAddress.entity_id == entity_id)
        if not include_inactive:
            query = query.where(EntityAddress.is_active == True)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_registered_address(self, entity_id: UUID) -> EntityAddress | None:
        """Get registered address for an entity."""
        from app.models.lending.enums import AddressType

        query = select(EntityAddress).where(
            and_(
                EntityAddress.entity_id == entity_id,
                EntityAddress.address_type == AddressType.REGISTERED,
                EntityAddress.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class EntityBankAccountRepository(BaseRepository[EntityBankAccount]):
    """Repository for EntityBankAccount operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(EntityBankAccount, session)

    async def get_by_entity(
        self, entity_id: UUID, include_inactive: bool = False
    ) -> list[EntityBankAccount]:
        """Get all bank accounts for an entity."""
        query = select(EntityBankAccount).where(EntityBankAccount.entity_id == entity_id)
        if not include_inactive:
            query = query.where(EntityBankAccount.is_active == True)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_primary_account(self, entity_id: UUID) -> EntityBankAccount | None:
        """Get primary bank account for an entity."""
        query = select(EntityBankAccount).where(
            and_(
                EntityBankAccount.entity_id == entity_id,
                EntityBankAccount.is_primary == True,
                EntityBankAccount.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_disbursement_account(self, entity_id: UUID) -> EntityBankAccount | None:
        """Get disbursement account for an entity."""
        query = select(EntityBankAccount).where(
            and_(
                EntityBankAccount.entity_id == entity_id,
                EntityBankAccount.is_disbursement_account == True,
                EntityBankAccount.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class EntityRelationRepository(BaseRepository[EntityRelation]):
    """Repository for EntityRelation operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(EntityRelation, session)

    async def get_by_entity(
        self, entity_id: UUID, include_inactive: bool = False
    ) -> list[EntityRelation]:
        """Get all relations for an entity."""
        query = select(EntityRelation).where(EntityRelation.entity_id == entity_id)
        if not include_inactive:
            query = query.where(EntityRelation.is_active == True)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_group_companies(self, entity_id: UUID) -> list[EntityRelation]:
        """Get group companies for an entity."""
        from app.models.lending.enums import RelationType

        query = select(EntityRelation).where(
            and_(
                EntityRelation.entity_id == entity_id,
                EntityRelation.relation_type.in_(
                    [
                        RelationType.PARENT,
                        RelationType.SUBSIDIARY,
                        RelationType.GROUP_COMPANY,
                        RelationType.HOLDING,
                    ]
                ),
                EntityRelation.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())


class EntityFinancialRepository(BaseRepository[EntityFinancial]):
    """Repository for EntityFinancial operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(EntityFinancial, session)

    async def get_by_entity(
        self, entity_id: UUID, include_inactive: bool = False
    ) -> list[EntityFinancial]:
        """Get all financials for an entity."""
        query = select(EntityFinancial).where(EntityFinancial.entity_id == entity_id)
        if not include_inactive:
            query = query.where(EntityFinancial.is_active == True)
        query = query.order_by(EntityFinancial.financial_year.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_latest_financial(self, entity_id: UUID) -> EntityFinancial | None:
        """Get latest financial year data for an entity."""
        query = (
            select(EntityFinancial)
            .where(
                and_(
                    EntityFinancial.entity_id == entity_id,
                    EntityFinancial.is_active == True,
                )
            )
            .order_by(EntityFinancial.financial_year.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_financial_year(
        self, entity_id: UUID, financial_year: str
    ) -> EntityFinancial | None:
        """Get financial data for a specific year."""
        query = select(EntityFinancial).where(
            and_(
                EntityFinancial.entity_id == entity_id,
                EntityFinancial.financial_year == financial_year,
                EntityFinancial.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
