"""Credit Rating repositories for the lending module."""

from datetime import date
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.lending.rating import (
    RiskCategory,
    RiskParameter,
    RatingMatrix,
    EntityRating,
    RatingScoreDetail,
)
from app.models.lending.enums import (
    RiskCategoryType,
    RatingGrade,
    RatingType,
    RatingStatus,
)
from app.repositories.base import BaseRepository


class RiskCategoryRepository(BaseRepository[RiskCategory]):
    """Repository for RiskCategory operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(RiskCategory, session)

    async def get_by_code(
        self, code: str, organization_id: UUID
    ) -> Optional[RiskCategory]:
        """Get risk category by code."""
        query = select(RiskCategory).where(
            and_(
                RiskCategory.code == code,
                RiskCategory.organization_id == organization_id,
                RiskCategory.is_active == True,
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
        category_type: Optional[RiskCategoryType] = None,
    ) -> Tuple[List[RiskCategory], int]:
        """Get all risk categories for an organization."""
        base_query = select(RiskCategory).where(
            RiskCategory.organization_id == organization_id
        )

        if not include_inactive:
            base_query = base_query.where(RiskCategory.is_active == True)

        if category_type:
            base_query = base_query.where(RiskCategory.category_type == category_type)

        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results
        query = (
            base_query.order_by(RiskCategory.display_order, RiskCategory.code)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_with_parameters(
        self, category_id: UUID
    ) -> Optional[RiskCategory]:
        """Get risk category with its parameters."""
        query = (
            select(RiskCategory)
            .options(selectinload(RiskCategory.parameters))
            .where(
                and_(
                    RiskCategory.id == category_id,
                    RiskCategory.is_active == True,
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_total_weightage(self, organization_id: UUID) -> float:
        """Get total weightage of all active categories."""
        query = select(func.sum(RiskCategory.weightage)).where(
            and_(
                RiskCategory.organization_id == organization_id,
                RiskCategory.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return float(result.scalar() or 0)


class RiskParameterRepository(BaseRepository[RiskParameter]):
    """Repository for RiskParameter operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(RiskParameter, session)

    async def get_by_code(
        self, code: str, risk_category_id: UUID
    ) -> Optional[RiskParameter]:
        """Get risk parameter by code within a category."""
        query = select(RiskParameter).where(
            and_(
                RiskParameter.code == code,
                RiskParameter.risk_category_id == risk_category_id,
                RiskParameter.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_category(
        self, risk_category_id: UUID, include_inactive: bool = False
    ) -> List[RiskParameter]:
        """Get all parameters for a risk category."""
        query = select(RiskParameter).where(
            RiskParameter.risk_category_id == risk_category_id
        )
        if not include_inactive:
            query = query.where(RiskParameter.is_active == True)
        query = query.order_by(RiskParameter.display_order, RiskParameter.code)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_total_weightage(self, risk_category_id: UUID) -> float:
        """Get total weightage of parameters in a category."""
        query = select(func.sum(RiskParameter.weightage)).where(
            and_(
                RiskParameter.risk_category_id == risk_category_id,
                RiskParameter.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return float(result.scalar() or 0)


class RatingMatrixRepository(BaseRepository[RatingMatrix]):
    """Repository for RatingMatrix operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(RatingMatrix, session)

    async def get_all_by_organization(
        self,
        organization_id: UUID,
        include_inactive: bool = False,
    ) -> List[RatingMatrix]:
        """Get all rating matrix entries for an organization."""
        query = select(RatingMatrix).where(
            RatingMatrix.organization_id == organization_id
        )
        if not include_inactive:
            query = query.where(RatingMatrix.is_active == True)
        query = query.order_by(RatingMatrix.max_score.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_grade_for_score(
        self, organization_id: UUID, score: float
    ) -> Optional[RatingGrade]:
        """Get rating grade for a given score."""
        query = (
            select(RatingMatrix.grade)
            .where(
                and_(
                    RatingMatrix.organization_id == organization_id,
                    RatingMatrix.min_score <= score,
                    RatingMatrix.max_score >= score,
                    RatingMatrix.is_active == True,
                )
            )
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_grade(
        self, organization_id: UUID, grade: RatingGrade
    ) -> Optional[RatingMatrix]:
        """Get rating matrix entry by grade."""
        query = select(RatingMatrix).where(
            and_(
                RatingMatrix.organization_id == organization_id,
                RatingMatrix.grade == grade,
                RatingMatrix.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class EntityRatingRepository(BaseRepository[EntityRating]):
    """Repository for EntityRating operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(EntityRating, session)

    async def get_by_entity(
        self, entity_id: UUID, include_inactive: bool = False
    ) -> List[EntityRating]:
        """Get all ratings for an entity."""
        query = select(EntityRating).where(EntityRating.entity_id == entity_id)
        if not include_inactive:
            query = query.where(EntityRating.is_active == True)
        query = query.order_by(EntityRating.rating_as_of_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_with_details(self, rating_id: UUID) -> Optional[EntityRating]:
        """Get entity rating with score details."""
        query = (
            select(EntityRating)
            .options(selectinload(EntityRating.score_details))
            .where(
                and_(
                    EntityRating.id == rating_id,
                    EntityRating.is_active == True,
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_current_rating(
        self, entity_id: UUID, as_of_date: Optional[date] = None
    ) -> Optional[EntityRating]:
        """Get current valid rating for an entity."""
        if as_of_date is None:
            as_of_date = date.today()

        query = (
            select(EntityRating)
            .where(
                and_(
                    EntityRating.entity_id == entity_id,
                    EntityRating.status == RatingStatus.APPROVED,
                    EntityRating.valid_from <= as_of_date,
                    EntityRating.valid_till >= as_of_date,
                    EntityRating.is_active == True,
                )
            )
            .order_by(EntityRating.rating_as_of_date.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_latest_approved(
        self, entity_id: UUID
    ) -> Optional[EntityRating]:
        """Get latest approved rating for an entity."""
        query = (
            select(EntityRating)
            .where(
                and_(
                    EntityRating.entity_id == entity_id,
                    EntityRating.status == RatingStatus.APPROVED,
                    EntityRating.is_active == True,
                )
            )
            .order_by(EntityRating.rating_as_of_date.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_pending_approval(
        self, organization_id: UUID
    ) -> List[EntityRating]:
        """Get all ratings pending approval."""
        from app.models.lending.entity import Entity

        query = (
            select(EntityRating)
            .join(Entity, EntityRating.entity_id == Entity.id)
            .where(
                and_(
                    Entity.organization_id == organization_id,
                    EntityRating.status == RatingStatus.PENDING_APPROVAL,
                    EntityRating.is_active == True,
                )
            )
            .order_by(EntityRating.created_at.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def generate_reference_number(
        self, organization_id: UUID, prefix: str = "RTG"
    ) -> str:
        """Generate rating reference number."""
        import datetime
        from app.models.lending.entity import Entity

        year = datetime.date.today().year
        pattern = f"{prefix}/{year}/%"

        query = (
            select(func.max(EntityRating.rating_reference_number))
            .join(Entity, EntityRating.entity_id == Entity.id)
            .where(
                and_(
                    Entity.organization_id == organization_id,
                    EntityRating.rating_reference_number.like(pattern),
                )
            )
        )
        result = await self.session.execute(query)
        max_ref = result.scalar()

        if max_ref:
            try:
                num = int(max_ref.split("/")[-1]) + 1
            except ValueError:
                num = 1
        else:
            num = 1

        return f"{prefix}/{year}/{num:05d}"


class RatingScoreDetailRepository(BaseRepository[RatingScoreDetail]):
    """Repository for RatingScoreDetail operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(RatingScoreDetail, session)

    async def get_by_rating(
        self, entity_rating_id: UUID
    ) -> List[RatingScoreDetail]:
        """Get all score details for a rating."""
        query = (
            select(RatingScoreDetail)
            .where(RatingScoreDetail.entity_rating_id == entity_rating_id)
            .order_by(RatingScoreDetail.created_at)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def bulk_create(
        self,
        entity_rating_id: UUID,
        score_details: List[dict],
    ) -> List[RatingScoreDetail]:
        """Bulk create score details for a rating."""
        details = []
        for detail in score_details:
            detail["entity_rating_id"] = entity_rating_id
            db_obj = RatingScoreDetail(**detail)
            self.session.add(db_obj)
            details.append(db_obj)

        await self.session.flush()
        return details
