"""Credit Rating service for the lending module."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

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
from app.schemas.lending.rating import (
    RiskCategoryCreate,
    RiskCategoryUpdate,
    RiskParameterCreate,
    RiskParameterUpdate,
    RatingMatrixCreate,
    RatingMatrixUpdate,
    EntityRatingCreate,
    EntityRatingUpdate,
    RatingScoreDetailCreate,
)
from app.repositories.lending.rating_repo import (
    RiskCategoryRepository,
    RiskParameterRepository,
    RatingMatrixRepository,
    EntityRatingRepository,
    RatingScoreDetailRepository,
)
from app.repositories.lending.entity_repo import EntityRepository
from app.core.exceptions import NotFoundException, ConflictException, ValidationException


class RatingService:
    """Service for Credit Rating operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.category_repo = RiskCategoryRepository(session)
        self.parameter_repo = RiskParameterRepository(session)
        self.matrix_repo = RatingMatrixRepository(session)
        self.rating_repo = EntityRatingRepository(session)
        self.score_detail_repo = RatingScoreDetailRepository(session)
        self.entity_repo = EntityRepository(session)

    # =========================================================================
    # Risk Category Operations
    # =========================================================================

    async def create_risk_category(
        self, data: RiskCategoryCreate, created_by: UUID
    ) -> RiskCategory:
        """Create a new risk category."""
        existing = await self.category_repo.get_by_code(data.code, data.organization_id)
        if existing:
            raise ConflictException(f"Risk category with code '{data.code}' already exists")

        # Validate total weightage doesn't exceed 100%
        current_total = await self.category_repo.get_total_weightage(data.organization_id)
        if current_total + float(data.weightage) > 100:
            raise ValidationException(
                f"Total category weightage would exceed 100% (current: {current_total}%)"
            )

        category = RiskCategory(
            **data.model_dump(),
            created_by=created_by,
        )
        self.session.add(category)
        await self.session.commit()
        await self.session.refresh(category)
        return category

    async def update_risk_category(
        self, id: UUID, data: RiskCategoryUpdate, updated_by: UUID
    ) -> RiskCategory:
        """Update a risk category."""
        category = await self.category_repo.get(id)
        if not category:
            raise NotFoundException("Risk category not found")

        # Validate weightage if being updated
        if data.weightage is not None:
            current_total = await self.category_repo.get_total_weightage(
                category.organization_id
            )
            new_total = current_total - float(category.weightage) + float(data.weightage)
            if new_total > 100:
                raise ValidationException(
                    f"Total category weightage would exceed 100% (would be: {new_total}%)"
                )

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(category, field, value)
        category.updated_by = updated_by

        await self.session.commit()
        await self.session.refresh(category)
        return category

    async def get_risk_category(self, id: UUID) -> RiskCategory:
        """Get risk category by ID."""
        category = await self.category_repo.get(id)
        if not category:
            raise NotFoundException("Risk category not found")
        return category

    async def get_risk_category_with_parameters(
        self, id: UUID
    ) -> RiskCategory:
        """Get risk category with its parameters."""
        category = await self.category_repo.get_with_parameters(id)
        if not category:
            raise NotFoundException("Risk category not found")
        return category

    async def get_all_risk_categories(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
        category_type: Optional[RiskCategoryType] = None,
    ) -> Tuple[List[RiskCategory], int]:
        """Get all risk categories."""
        return await self.category_repo.get_all_by_organization(
            organization_id=organization_id,
            skip=skip,
            limit=limit,
            include_inactive=include_inactive,
            category_type=category_type,
        )

    # =========================================================================
    # Risk Parameter Operations
    # =========================================================================

    async def create_risk_parameter(
        self, data: RiskParameterCreate, created_by: UUID
    ) -> RiskParameter:
        """Create a new risk parameter."""
        # Verify category exists
        category = await self.category_repo.get(data.risk_category_id)
        if not category:
            raise NotFoundException("Risk category not found")

        existing = await self.parameter_repo.get_by_code(data.code, data.risk_category_id)
        if existing:
            raise ConflictException(f"Parameter with code '{data.code}' already exists in this category")

        # Validate weightage
        current_total = await self.parameter_repo.get_total_weightage(data.risk_category_id)
        if current_total + float(data.weightage) > 100:
            raise ValidationException(
                f"Total parameter weightage would exceed 100% (current: {current_total}%)"
            )

        parameter = RiskParameter(
            **data.model_dump(),
            created_by=created_by,
        )
        self.session.add(parameter)
        await self.session.commit()
        await self.session.refresh(parameter)
        return parameter

    async def update_risk_parameter(
        self, id: UUID, data: RiskParameterUpdate, updated_by: UUID
    ) -> RiskParameter:
        """Update a risk parameter."""
        parameter = await self.parameter_repo.get(id)
        if not parameter:
            raise NotFoundException("Risk parameter not found")

        if data.weightage is not None:
            current_total = await self.parameter_repo.get_total_weightage(
                parameter.risk_category_id
            )
            new_total = current_total - float(parameter.weightage) + float(data.weightage)
            if new_total > 100:
                raise ValidationException(
                    f"Total parameter weightage would exceed 100% (would be: {new_total}%)"
                )

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(parameter, field, value)
        parameter.updated_by = updated_by

        await self.session.commit()
        await self.session.refresh(parameter)
        return parameter

    async def get_parameters_by_category(
        self, risk_category_id: UUID, include_inactive: bool = False
    ) -> List[RiskParameter]:
        """Get all parameters for a risk category."""
        return await self.parameter_repo.get_by_category(risk_category_id, include_inactive)

    # =========================================================================
    # Rating Matrix Operations
    # =========================================================================

    async def create_rating_matrix(
        self, data: RatingMatrixCreate, created_by: UUID
    ) -> RatingMatrix:
        """Create a new rating matrix entry."""
        # Check if grade already exists
        existing = await self.matrix_repo.get_by_grade(data.organization_id, data.grade)
        if existing:
            raise ConflictException(f"Rating matrix entry for grade '{data.grade.value}' already exists")

        matrix = RatingMatrix(
            **data.model_dump(),
            created_by=created_by,
        )
        self.session.add(matrix)
        await self.session.commit()
        await self.session.refresh(matrix)
        return matrix

    async def update_rating_matrix(
        self, id: UUID, data: RatingMatrixUpdate, updated_by: UUID
    ) -> RatingMatrix:
        """Update a rating matrix entry."""
        matrix = await self.matrix_repo.get(id)
        if not matrix:
            raise NotFoundException("Rating matrix entry not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(matrix, field, value)
        matrix.updated_by = updated_by

        await self.session.commit()
        await self.session.refresh(matrix)
        return matrix

    async def get_all_rating_matrix(
        self, organization_id: UUID, include_inactive: bool = False
    ) -> List[RatingMatrix]:
        """Get all rating matrix entries."""
        return await self.matrix_repo.get_all_by_organization(
            organization_id, include_inactive
        )

    async def get_grade_for_score(
        self, organization_id: UUID, score: float
    ) -> Optional[RatingGrade]:
        """Get rating grade for a given score."""
        return await self.matrix_repo.get_grade_for_score(organization_id, score)

    # =========================================================================
    # Entity Rating Operations
    # =========================================================================

    async def create_entity_rating(
        self, data: EntityRatingCreate, created_by: UUID
    ) -> EntityRating:
        """Create a new entity rating."""
        entity = await self.entity_repo.get(data.entity_id)
        if not entity:
            raise NotFoundException("Entity not found")

        # Generate reference number
        reference_number = await self.rating_repo.generate_reference_number(
            entity.organization_id
        )

        # Calculate total score from score details
        total_score = sum(
            float(detail.weighted_score) for detail in data.score_details
        )

        # Get proposed grade based on score
        proposed_grade = await self.matrix_repo.get_grade_for_score(
            entity.organization_id, total_score
        )

        rating = EntityRating(
            entity_id=data.entity_id,
            rating_reference_number=reference_number,
            rating_type=data.rating_type,
            rating_as_of_date=data.rating_as_of_date,
            financial_year=data.financial_year,
            total_score=Decimal(str(total_score)),
            proposed_grade=proposed_grade or data.proposed_grade,
            status=RatingStatus.DRAFT,
            initiated_by_id=created_by,
            analyst_remarks=data.analyst_remarks,
            created_by=created_by,
        )
        self.session.add(rating)
        await self.session.flush()

        # Create score details
        for detail_data in data.score_details:
            detail = RatingScoreDetail(
                entity_rating_id=rating.id,
                parameter_id=detail_data.parameter_id,
                raw_value=detail_data.raw_value,
                score=detail_data.score,
                weighted_score=detail_data.weighted_score,
                remarks=detail_data.remarks,
            )
            self.session.add(detail)

        await self.session.commit()
        await self.session.refresh(rating)
        return rating

    async def update_entity_rating(
        self, id: UUID, data: EntityRatingUpdate, updated_by: UUID
    ) -> EntityRating:
        """Update an entity rating."""
        rating = await self.rating_repo.get(id)
        if not rating:
            raise NotFoundException("Entity rating not found")

        if rating.status == RatingStatus.APPROVED:
            raise ValidationException("Cannot update an approved rating")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(rating, field, value)
        rating.updated_by = updated_by

        await self.session.commit()
        await self.session.refresh(rating)
        return rating

    async def submit_rating_for_approval(
        self, id: UUID, submitted_by: UUID
    ) -> EntityRating:
        """Submit rating for approval."""
        rating = await self.rating_repo.get(id)
        if not rating:
            raise NotFoundException("Entity rating not found")

        if rating.status != RatingStatus.DRAFT:
            raise ValidationException("Only draft ratings can be submitted")

        rating.status = RatingStatus.PENDING_APPROVAL
        rating.updated_by = submitted_by

        # Route through the workflow engine. Ratings don't carry an
        # amount; the delegation-band required level stays None and the
        # workflow uses a fixed rating-committee routing configured on
        # the workflow_code. See CLAUDE.md §8.4.
        from app.core.maker_checker import build_workflow_request

        self._pending_workflow_request = build_workflow_request(
            workflow_code="ENTITY_RATING_APPROVAL",
            entity_type="entity_rating",
            entity_id=rating.id,
            maker_user_id=submitted_by,
            organization_id=rating.organization_id,
        )

        await self.session.commit()
        await self.session.refresh(rating)
        return rating

    async def approve_rating(
        self,
        id: UUID,
        approved_by: UUID,
        approved_grade: Optional[RatingGrade] = None,
        override_reason: Optional[str] = None,
        remarks: Optional[str] = None,
        valid_from: Optional[date] = None,
        valid_till: Optional[date] = None,
    ) -> EntityRating:
        """Approve an entity rating."""
        rating = await self.rating_repo.get(id)
        if not rating:
            raise NotFoundException("Entity rating not found")

        if rating.status != RatingStatus.PENDING_APPROVAL:
            raise ValidationException("Rating is not pending approval")

        # Use override grade if provided, otherwise use proposed grade
        final_grade = approved_grade or rating.proposed_grade
        if approved_grade and approved_grade != rating.proposed_grade:
            if not override_reason:
                raise ValidationException("Override reason is required when changing the proposed grade")
            rating.grade_override_reason = override_reason

        rating.approved_grade = final_grade
        rating.status = RatingStatus.APPROVED
        rating.approved_by_id = approved_by
        rating.approved_at = datetime.utcnow()
        rating.approver_remarks = remarks
        rating.valid_from = valid_from or date.today()
        rating.valid_till = valid_till or date.today().replace(year=date.today().year + 1)
        rating.updated_by = approved_by

        # Update entity's internal rating
        entity = await self.entity_repo.get(rating.entity_id)
        if entity:
            entity.internal_rating = final_grade.value

        await self.session.commit()
        await self.session.refresh(rating)
        return rating

    async def reject_rating(
        self, id: UUID, rejected_by: UUID, remarks: str
    ) -> EntityRating:
        """Reject an entity rating."""
        rating = await self.rating_repo.get(id)
        if not rating:
            raise NotFoundException("Entity rating not found")

        if rating.status != RatingStatus.PENDING_APPROVAL:
            raise ValidationException("Rating is not pending approval")

        rating.status = RatingStatus.REJECTED
        rating.approver_remarks = remarks
        rating.updated_by = rejected_by

        await self.session.commit()
        await self.session.refresh(rating)
        return rating

    async def get_entity_rating(self, id: UUID) -> EntityRating:
        """Get entity rating by ID."""
        rating = await self.rating_repo.get(id)
        if not rating:
            raise NotFoundException("Entity rating not found")
        return rating

    async def get_entity_rating_with_details(
        self, id: UUID
    ) -> EntityRating:
        """Get entity rating with score details."""
        rating = await self.rating_repo.get_with_details(id)
        if not rating:
            raise NotFoundException("Entity rating not found")
        return rating

    async def get_entity_ratings(
        self, entity_id: UUID, include_inactive: bool = False
    ) -> List[EntityRating]:
        """Get all ratings for an entity."""
        return await self.rating_repo.get_by_entity(entity_id, include_inactive)

    async def get_current_rating(
        self, entity_id: UUID, as_of_date: Optional[date] = None
    ) -> Optional[EntityRating]:
        """Get current valid rating for an entity."""
        return await self.rating_repo.get_current_rating(entity_id, as_of_date)

    async def get_pending_approval_ratings(
        self, organization_id: UUID
    ) -> List[EntityRating]:
        """Get all ratings pending approval."""
        return await self.rating_repo.get_pending_approval(organization_id)
