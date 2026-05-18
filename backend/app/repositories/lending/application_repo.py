"""Loan Application repositories for the lending module."""

from datetime import date
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.lending.application import (
    ApplicationDocument,
    ApplicationFee,
    FinancialAnalysis,
    LoanApplication,
    ProjectMilestone,
    TechnicalAppraisal,
)
from app.models.lending.enums import (
    ApplicationStage,
    ApplicationStatus,
    MilestoneStatus,
)
from app.repositories.base import BaseRepository


class ApplicationDocumentRepository(BaseRepository[ApplicationDocument]):
    """Repository for ApplicationDocument operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(ApplicationDocument, session)

    async def get_by_application(
        self, application_id: UUID, include_inactive: bool = False
    ) -> list[ApplicationDocument]:
        """Get all documents for an application."""
        query = select(ApplicationDocument).where(
            ApplicationDocument.application_id == application_id
        )
        if not include_inactive:
            query = query.where(ApplicationDocument.is_active == True)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_verified_documents(self, application_id: UUID) -> list[ApplicationDocument]:
        """Get verified documents for an application."""
        query = select(ApplicationDocument).where(
            and_(
                ApplicationDocument.application_id == application_id,
                ApplicationDocument.is_verified == True,
                ApplicationDocument.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pending_verification(self, application_id: UUID) -> list[ApplicationDocument]:
        """Get documents pending verification."""
        query = select(ApplicationDocument).where(
            and_(
                ApplicationDocument.application_id == application_id,
                ApplicationDocument.is_verified == False,
                ApplicationDocument.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def check_all_mandatory_uploaded(
        self, application_id: UUID, mandatory_checklist_ids: list[UUID]
    ) -> bool:
        """Check if all mandatory documents are uploaded."""
        query = select(func.count(ApplicationDocument.id)).where(
            and_(
                ApplicationDocument.application_id == application_id,
                ApplicationDocument.checklist_id.in_(mandatory_checklist_ids),
                ApplicationDocument.is_active == True,
            )
        )
        result = await self.session.execute(query)
        uploaded_count = result.scalar() or 0
        return uploaded_count >= len(mandatory_checklist_ids)


class ApplicationFeeRepository(BaseRepository[ApplicationFee]):
    """Repository for ApplicationFee operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(ApplicationFee, session)

    async def get_by_application(
        self, application_id: UUID, include_inactive: bool = False
    ) -> list[ApplicationFee]:
        """Get all fees for an application."""
        query = select(ApplicationFee).where(ApplicationFee.application_id == application_id)
        if not include_inactive:
            query = query.where(ApplicationFee.is_active == True)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_collected_fees(self, application_id: UUID) -> list[ApplicationFee]:
        """Get collected fees for an application."""
        query = select(ApplicationFee).where(
            and_(
                ApplicationFee.application_id == application_id,
                ApplicationFee.is_collected == True,
                ApplicationFee.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pending_fees(self, application_id: UUID) -> list[ApplicationFee]:
        """Get pending fees for an application."""
        query = select(ApplicationFee).where(
            and_(
                ApplicationFee.application_id == application_id,
                ApplicationFee.status == "PENDING",
                ApplicationFee.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_total_fee_amount(self, application_id: UUID) -> float:
        """Get total fee amount for an application."""
        query = select(func.sum(ApplicationFee.total_amount)).where(
            and_(
                ApplicationFee.application_id == application_id,
                ApplicationFee.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return float(result.scalar() or 0)

    async def get_total_collected_amount(self, application_id: UUID) -> float:
        """Get total collected amount for an application."""
        query = select(func.sum(ApplicationFee.total_amount)).where(
            and_(
                ApplicationFee.application_id == application_id,
                ApplicationFee.status == "COLLECTED",
                ApplicationFee.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return float(result.scalar() or 0)


class TechnicalAppraisalRepository(BaseRepository[TechnicalAppraisal]):
    """Repository for TechnicalAppraisal operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(TechnicalAppraisal, session)

    async def get_by_application(
        self, application_id: UUID, include_inactive: bool = False
    ) -> list[TechnicalAppraisal]:
        """Get all technical appraisals for an application."""
        query = select(TechnicalAppraisal).where(
            TechnicalAppraisal.application_id == application_id
        )
        if not include_inactive:
            query = query.where(TechnicalAppraisal.is_active == True)
        query = query.order_by(TechnicalAppraisal.appraisal_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_latest(self, application_id: UUID) -> TechnicalAppraisal | None:
        """Get latest technical appraisal for an application."""
        query = (
            select(TechnicalAppraisal)
            .where(
                and_(
                    TechnicalAppraisal.application_id == application_id,
                    TechnicalAppraisal.is_active == True,
                )
            )
            .order_by(TechnicalAppraisal.appraisal_date.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class FinancialAnalysisRepository(BaseRepository[FinancialAnalysis]):
    """Repository for FinancialAnalysis operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(FinancialAnalysis, session)

    async def get_by_application(
        self, application_id: UUID, include_inactive: bool = False
    ) -> list[FinancialAnalysis]:
        """Get all financial analyses for an application."""
        query = select(FinancialAnalysis).where(FinancialAnalysis.application_id == application_id)
        if not include_inactive:
            query = query.where(FinancialAnalysis.is_active == True)
        query = query.order_by(FinancialAnalysis.analysis_date.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_latest(self, application_id: UUID) -> FinancialAnalysis | None:
        """Get latest financial analysis for an application."""
        query = (
            select(FinancialAnalysis)
            .where(
                and_(
                    FinancialAnalysis.application_id == application_id,
                    FinancialAnalysis.is_active == True,
                )
            )
            .order_by(FinancialAnalysis.analysis_date.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class ProjectMilestoneRepository(BaseRepository[ProjectMilestone]):
    """Repository for ProjectMilestone operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(ProjectMilestone, session)

    async def get_by_application(
        self, application_id: UUID, include_inactive: bool = False
    ) -> list[ProjectMilestone]:
        """Get all milestones for an application."""
        query = select(ProjectMilestone).where(ProjectMilestone.application_id == application_id)
        if not include_inactive:
            query = query.where(ProjectMilestone.is_active == True)
        query = query.order_by(ProjectMilestone.milestone_number)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_completed_milestones(self, application_id: UUID) -> list[ProjectMilestone]:
        """Get completed milestones for an application."""
        query = select(ProjectMilestone).where(
            and_(
                ProjectMilestone.application_id == application_id,
                ProjectMilestone.status == MilestoneStatus.COMPLETED,
                ProjectMilestone.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pending_milestones(self, application_id: UUID) -> list[ProjectMilestone]:
        """Get pending milestones for an application."""
        query = select(ProjectMilestone).where(
            and_(
                ProjectMilestone.application_id == application_id,
                ProjectMilestone.status.in_([MilestoneStatus.PENDING, MilestoneStatus.IN_PROGRESS]),
                ProjectMilestone.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_next_milestone(self, application_id: UUID) -> ProjectMilestone | None:
        """Get next pending milestone for an application."""
        query = (
            select(ProjectMilestone)
            .where(
                and_(
                    ProjectMilestone.application_id == application_id,
                    ProjectMilestone.status.in_(
                        [MilestoneStatus.PENDING, MilestoneStatus.IN_PROGRESS]
                    ),
                    ProjectMilestone.is_active == True,
                )
            )
            .order_by(ProjectMilestone.milestone_number)
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class LoanApplicationRepository(BaseRepository[LoanApplication]):
    """Repository for LoanApplication operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(LoanApplication, session)

    async def get_by_number(
        self, application_number: str, organization_id: UUID
    ) -> LoanApplication | None:
        """Get application by number."""
        query = select(LoanApplication).where(
            and_(
                LoanApplication.application_number == application_number,
                LoanApplication.organization_id == organization_id,
                LoanApplication.is_active == True,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_with_details(self, application_id: UUID) -> LoanApplication | None:
        """Get application with all related data."""
        query = (
            select(LoanApplication)
            .options(
                selectinload(LoanApplication.documents),
                selectinload(LoanApplication.fees),
                selectinload(LoanApplication.technical_appraisals),
                selectinload(LoanApplication.financial_analyses),
                selectinload(LoanApplication.milestones),
            )
            .where(
                and_(
                    LoanApplication.id == application_id,
                    LoanApplication.is_active == True,
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
        entity_id: UUID | None = None,
        product_id: UUID | None = None,
        stage: ApplicationStage | None = None,
        status: ApplicationStatus | None = None,
        relationship_manager_id: UUID | None = None,
        credit_officer_id: UUID | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> tuple[list[LoanApplication], int]:
        """Get all applications for an organization with filters."""
        base_query = select(LoanApplication).where(
            LoanApplication.organization_id == organization_id
        )

        if not include_inactive:
            base_query = base_query.where(LoanApplication.is_active == True)

        if search:
            search_term = f"%{search}%"
            base_query = base_query.where(
                or_(
                    LoanApplication.application_number.ilike(search_term),
                    LoanApplication.purpose.ilike(search_term),
                    LoanApplication.project_name.ilike(search_term),
                )
            )

        if entity_id:
            base_query = base_query.where(LoanApplication.entity_id == entity_id)

        if product_id:
            base_query = base_query.where(LoanApplication.product_id == product_id)

        if stage:
            base_query = base_query.where(LoanApplication.stage == stage)

        if status:
            base_query = base_query.where(LoanApplication.status == status)

        if relationship_manager_id:
            base_query = base_query.where(
                LoanApplication.relationship_manager_id == relationship_manager_id
            )

        if credit_officer_id:
            base_query = base_query.where(LoanApplication.credit_officer_id == credit_officer_id)

        if from_date:
            base_query = base_query.where(func.date(LoanApplication.created_at) >= from_date)

        if to_date:
            base_query = base_query.where(func.date(LoanApplication.created_at) <= to_date)

        # Count total
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.session.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated results — eager-load entity + product so the list
        # response can surface entity_name + product_name without N+1.
        query = (
            base_query.options(
                selectinload(LoanApplication.entity),
                selectinload(LoanApplication.product),
            )
            .order_by(LoanApplication.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_by_entity(
        self, entity_id: UUID, include_inactive: bool = False
    ) -> list[LoanApplication]:
        """Get all applications for an entity."""
        query = select(LoanApplication).where(LoanApplication.entity_id == entity_id)
        if not include_inactive:
            query = query.where(LoanApplication.is_active == True)
        query = query.order_by(LoanApplication.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pending_applications(self, organization_id: UUID) -> list[LoanApplication]:
        """Get applications pending action."""
        query = select(LoanApplication).where(
            and_(
                LoanApplication.organization_id == organization_id,
                LoanApplication.status.in_(
                    [
                        ApplicationStatus.SUBMITTED,
                        ApplicationStatus.UNDER_REVIEW,
                        ApplicationStatus.ADDITIONAL_INFO_REQUIRED,
                    ]
                ),
                LoanApplication.is_active == True,
            )
        )
        query = query.order_by(LoanApplication.created_at.asc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def generate_application_number(
        self,
        organization_id: UUID,
        product_code: str,
        branch_code: str = "HO",
    ) -> str:
        """Generate next application number."""
        year = date.today().year
        prefix = f"SMFC/{product_code}/{branch_code}/{year}"
        pattern = f"{prefix}/A%"

        query = select(func.max(LoanApplication.application_number)).where(
            and_(
                LoanApplication.organization_id == organization_id,
                LoanApplication.application_number.like(pattern),
            )
        )
        result = await self.session.execute(query)
        max_number = result.scalar()

        if max_number:
            try:
                num = int(max_number.split("/")[-1][1:]) + 1
            except ValueError:
                num = 1
        else:
            num = 1

        return f"{prefix}/A{num:05d}"

    async def get_stage_counts(self, organization_id: UUID) -> dict:
        """Get application counts by stage."""
        query = (
            select(
                LoanApplication.stage,
                func.count(LoanApplication.id).label("count"),
            )
            .where(
                and_(
                    LoanApplication.organization_id == organization_id,
                    LoanApplication.is_active == True,
                )
            )
            .group_by(LoanApplication.stage)
        )
        result = await self.session.execute(query)
        return {row.stage: row.count for row in result.all()}
