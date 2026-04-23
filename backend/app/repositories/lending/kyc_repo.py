"""KYC repositories for the lending module."""

from datetime import date
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lending.kyc import (
    KYCDocumentType,
    EntityKYCDocument,
    CKYCTransaction,
    BureauPull,
    BureauReport,
)
from app.models.lending.enums import (
    KYCDocCategory,
    KYCVerificationStatus,
    BureauType,
    BureauPullStatus,
    EntityType,
)
from app.repositories.base import BaseRepository


class KYCDocumentTypeRepository(BaseRepository[KYCDocumentType]):
    """Repository for KYCDocumentType operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(KYCDocumentType, session)

    async def get_by_code(
        self, code: str, organization_id: UUID
    ) -> Optional[KYCDocumentType]:
        """Get KYC document type by code."""
        query = select(KYCDocumentType).where(
            and_(
                KYCDocumentType.code == code,
                KYCDocumentType.organization_id == organization_id,
                KYCDocumentType.is_active == True,
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
        category: Optional[KYCDocCategory] = None,
        entity_type: Optional[EntityType] = None,
    ) -> Tuple[List[KYCDocumentType], int]:
        """Get all KYC document types for an organization."""
        base_query = select(KYCDocumentType).where(
            KYCDocumentType.organization_id == organization_id
        )

        if not include_inactive:
            base_query = base_query.where(KYCDocumentType.is_active == True)

        if category:
            base_query = base_query.where(KYCDocumentType.category == category)

        if entity_type:
            base_query = base_query.where(
                KYCDocumentType.applicable_entity_types.contains([entity_type.value])
            )

        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = base_query.order_by(KYCDocumentType.code).offset(skip).limit(limit)
        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_mandatory_documents(
        self,
        organization_id: UUID,
        entity_type: Optional[EntityType] = None,
    ) -> List[KYCDocumentType]:
        """Get mandatory KYC documents."""
        query = select(KYCDocumentType).where(
            and_(
                KYCDocumentType.organization_id == organization_id,
                KYCDocumentType.is_mandatory == True,
                KYCDocumentType.is_active == True,
            )
        )

        if entity_type:
            query = query.where(
                KYCDocumentType.applicable_entity_types.contains([entity_type.value])
            )

        result = await self.session.execute(query)
        return list(result.scalars().all())


class EntityKYCDocumentRepository(BaseRepository[EntityKYCDocument]):
    """Repository for EntityKYCDocument operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(EntityKYCDocument, session)

    async def get_by_entity(
        self, entity_id: UUID, include_inactive: bool = False
    ) -> List[EntityKYCDocument]:
        """Get all KYC documents for an entity."""
        query = select(EntityKYCDocument).where(
            EntityKYCDocument.entity_id == entity_id
        )
        if not include_inactive:
            query = query.where(EntityKYCDocument.is_active == True)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_verified_documents(
        self, entity_id: UUID
    ) -> List[EntityKYCDocument]:
        """Get verified KYC documents for an entity."""
        query = select(EntityKYCDocument).where(
            and_(
                EntityKYCDocument.entity_id == entity_id,
                EntityKYCDocument.verification_status == KYCVerificationStatus.VERIFIED,
                EntityKYCDocument.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pending_verification(
        self, entity_id: UUID
    ) -> List[EntityKYCDocument]:
        """Get documents pending verification for an entity."""
        query = select(EntityKYCDocument).where(
            and_(
                EntityKYCDocument.entity_id == entity_id,
                EntityKYCDocument.verification_status == KYCVerificationStatus.PENDING,
                EntityKYCDocument.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_expired_documents(
        self, entity_id: UUID, as_of_date: Optional[date] = None
    ) -> List[EntityKYCDocument]:
        """Get expired KYC documents for an entity."""
        if as_of_date is None:
            as_of_date = date.today()

        query = select(EntityKYCDocument).where(
            and_(
                EntityKYCDocument.entity_id == entity_id,
                EntityKYCDocument.expiry_date < as_of_date,
                EntityKYCDocument.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def check_kyc_complete(
        self,
        entity_id: UUID,
        mandatory_doc_type_ids: List[UUID],
    ) -> bool:
        """Check if all mandatory KYC documents are verified."""
        query = select(func.count(EntityKYCDocument.id)).where(
            and_(
                EntityKYCDocument.entity_id == entity_id,
                EntityKYCDocument.document_type_id.in_(mandatory_doc_type_ids),
                EntityKYCDocument.verification_status == KYCVerificationStatus.VERIFIED,
                EntityKYCDocument.is_active == True,
            )
        )
        result = await self.session.execute(query)
        verified_count = result.scalar() or 0
        return verified_count >= len(mandatory_doc_type_ids)


class CKYCTransactionRepository(BaseRepository[CKYCTransaction]):
    """Repository for CKYCTransaction operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(CKYCTransaction, session)

    async def get_by_entity(
        self, entity_id: UUID
    ) -> List[CKYCTransaction]:
        """Get all CKYC transactions for an entity."""
        query = (
            select(CKYCTransaction)
            .where(CKYCTransaction.entity_id == entity_id)
            .order_by(CKYCTransaction.initiated_at.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_latest_successful(
        self, entity_id: UUID
    ) -> Optional[CKYCTransaction]:
        """Get latest successful CKYC transaction for an entity."""
        query = (
            select(CKYCTransaction)
            .where(
                and_(
                    CKYCTransaction.entity_id == entity_id,
                    CKYCTransaction.status == "SUCCESS",
                )
            )
            .order_by(CKYCTransaction.completed_at.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class BureauPullRepository(BaseRepository[BureauPull]):
    """Repository for BureauPull operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(BureauPull, session)

    async def get_by_entity(
        self, entity_id: UUID, include_failed: bool = False
    ) -> List[BureauPull]:
        """Get all bureau pulls for an entity."""
        query = select(BureauPull).where(BureauPull.entity_id == entity_id)
        if not include_failed:
            query = query.where(
                BureauPull.status.in_([BureauPullStatus.SUCCESS, BureauPullStatus.PARTIAL])
            )
        query = query.order_by(BureauPull.initiated_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_latest_by_bureau(
        self, entity_id: UUID, bureau_type: BureauType
    ) -> Optional[BureauPull]:
        """Get latest bureau pull for an entity and bureau type."""
        query = (
            select(BureauPull)
            .where(
                and_(
                    BureauPull.entity_id == entity_id,
                    BureauPull.bureau_type == bureau_type,
                    BureauPull.status == BureauPullStatus.SUCCESS,
                )
            )
            .order_by(BureauPull.completed_at.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_valid_pulls(
        self, entity_id: UUID, as_of_date: Optional[date] = None
    ) -> List[BureauPull]:
        """Get bureau pulls that are still valid (not expired)."""
        if as_of_date is None:
            as_of_date = date.today()

        query = select(BureauPull).where(
            and_(
                BureauPull.entity_id == entity_id,
                BureauPull.status == BureauPullStatus.SUCCESS,
                or_(
                    BureauPull.report_valid_till.is_(None),
                    BureauPull.report_valid_till >= as_of_date,
                ),
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())


class BureauReportRepository(BaseRepository[BureauReport]):
    """Repository for BureauReport operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(BureauReport, session)

    async def get_by_pull(self, bureau_pull_id: UUID) -> Optional[BureauReport]:
        """Get bureau report by pull ID."""
        query = select(BureauReport).where(
            BureauReport.bureau_pull_id == bureau_pull_id
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_entity(
        self, entity_id: UUID
    ) -> List[BureauReport]:
        """Get all bureau reports for an entity (via bureau pulls)."""
        query = (
            select(BureauReport)
            .join(BureauPull, BureauReport.bureau_pull_id == BureauPull.id)
            .where(BureauPull.entity_id == entity_id)
            .order_by(BureauReport.report_date.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_latest_score(
        self, entity_id: UUID, bureau_type: Optional[BureauType] = None
    ) -> Optional[int]:
        """Get latest credit score for an entity."""
        query = (
            select(BureauReport.credit_score)
            .join(BureauPull, BureauReport.bureau_pull_id == BureauPull.id)
            .where(
                and_(
                    BureauPull.entity_id == entity_id,
                    BureauPull.status == BureauPullStatus.SUCCESS,
                    BureauReport.credit_score.isnot(None),
                )
            )
        )

        if bureau_type:
            query = query.where(BureauPull.bureau_type == bureau_type)

        query = query.order_by(BureauReport.report_date.desc()).limit(1)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
