"""Loan Application service for the lending module."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
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
from app.repositories.lending.application_repo import (
    ApplicationDocumentRepository,
    ApplicationFeeRepository,
    FinancialAnalysisRepository,
    LoanApplicationRepository,
    ProjectMilestoneRepository,
    TechnicalAppraisalRepository,
)
from app.repositories.lending.entity_repo import EntityRepository
from app.repositories.lending.product_repo import LoanProductRepository
from app.schemas.lending.application import (
    ApplicationDocumentCreate,
    ApplicationFeeCreate,
    FinancialAnalysisCreate,
    FinancialAnalysisUpdate,
    LoanApplicationCreate,
    LoanApplicationUpdate,
    ProjectMilestoneCreate,
    ProjectMilestoneUpdate,
    TechnicalAppraisalCreate,
    TechnicalAppraisalUpdate,
)


class ApplicationService:
    """Service for Loan Application operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.app_repo = LoanApplicationRepository(session)
        self.doc_repo = ApplicationDocumentRepository(session)
        self.fee_repo = ApplicationFeeRepository(session)
        self.tech_appraisal_repo = TechnicalAppraisalRepository(session)
        self.fin_analysis_repo = FinancialAnalysisRepository(session)
        self.milestone_repo = ProjectMilestoneRepository(session)
        self.entity_repo = EntityRepository(session)
        self.product_repo = LoanProductRepository(session)

    # =========================================================================
    # Loan Application Operations
    # =========================================================================

    async def create_application(
        self, data: LoanApplicationCreate, created_by: UUID
    ) -> LoanApplication:
        """Create a new loan application."""
        # Verify entity exists
        entity = await self.entity_repo.get(data.entity_id)
        if not entity:
            raise NotFoundException("Entity not found")

        # Verify product exists
        product = await self.product_repo.get(data.product_id)
        if not product:
            raise NotFoundException("Product not found")

        # Validate amount against product limits
        if data.requested_amount < product.min_amount:
            raise ValidationException(f"Requested amount is below minimum ({product.min_amount})")
        if data.requested_amount > product.max_amount:
            raise ValidationException(f"Requested amount exceeds maximum ({product.max_amount})")

        # Validate tenure against product limits
        if data.requested_tenure_months < product.min_tenure_months:
            raise ValidationException(
                f"Requested tenure is below minimum ({product.min_tenure_months} months)"
            )
        if data.requested_tenure_months > product.max_tenure_months:
            raise ValidationException(
                f"Requested tenure exceeds maximum ({product.max_tenure_months} months)"
            )

        # Generate application number
        application_number = await self.app_repo.generate_application_number(
            data.organization_id, product.code
        )

        application = LoanApplication(
            **data.model_dump(),
            application_number=application_number,
            application_date=date.today(),
            stage=ApplicationStage.LEAD,
            status=ApplicationStatus.DRAFT,
            created_by=created_by,
        )
        self.session.add(application)
        await self.session.flush()
        await self.session.refresh(application)
        return application

    async def update_application(
        self, id: UUID, data: LoanApplicationUpdate, updated_by: UUID
    ) -> LoanApplication:
        """Update a loan application."""
        application = await self.app_repo.get(id)
        if not application:
            raise NotFoundException("Application not found")

        if application.status not in [
            ApplicationStatus.DRAFT,
            ApplicationStatus.ADDITIONAL_INFO_REQUIRED,
        ]:
            raise ValidationException("Application cannot be updated in current status")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(application, field, value)
        application.updated_by = updated_by

        await self.session.flush()
        await self.session.refresh(application)
        return application

    async def submit_application(self, id: UUID, submitted_by: UUID) -> LoanApplication:
        """Submit application for processing."""
        application = await self.app_repo.get(id)
        if not application:
            raise NotFoundException("Application not found")

        if application.status != ApplicationStatus.DRAFT:
            raise ValidationException("Only draft applications can be submitted")

        application.status = ApplicationStatus.SUBMITTED
        application.stage = ApplicationStage.APPLICATION
        application.submitted_at = datetime.utcnow()
        application.updated_by = submitted_by

        # Route through the workflow engine. The application's requested
        # amount drives the delegation-band required level. See CLAUDE.md §8.4.
        from app.core.maker_checker import build_workflow_request
        from app.models.workflow.enums import WorkflowEntityType
        from app.services.workflow.workflow_engine import WorkflowEngine

        self._pending_workflow_request = build_workflow_request(
            workflow_code="LOAN_APPLICATION_REVIEW",
            entity_type="loan_application",
            entity_id=application.id,
            maker_user_id=submitted_by,
            organization_id=application.organization_id,
            amount=getattr(application, "requested_amount", None),
        )

        # Dispatch. If no WorkflowDefinition is seeded yet, fall through to
        # "submitted, no workflow" — deployments without the seed still work.
        try:
            workflow_instance = await WorkflowEngine(self.session).start_workflow(
                entity_type=WorkflowEntityType.LOAN_APPLICATION,
                entity_id=application.id,
                entity_reference=application.application_number,
                organization_id=application.organization_id,
                context={
                    "amount": (
                        float(application.requested_amount)
                        if application.requested_amount is not None
                        else None
                    ),
                    "application_number": application.application_number,
                },
                started_by=submitted_by,
            )
            application.workflow_instance_id = workflow_instance.id
        except NotFoundException:
            pass  # No WorkflowDefinition seeded for LOAN_APPLICATION_REVIEW yet.

        await self.session.flush()
        await self.session.refresh(application)
        return application

    async def move_to_appraisal(self, id: UUID, updated_by: UUID) -> LoanApplication:
        """Move application to appraisal stage."""
        application = await self.app_repo.get(id)
        if not application:
            raise NotFoundException("Application not found")

        if application.stage != ApplicationStage.APPLICATION:
            raise ValidationException("Application must be in APPLICATION stage")

        application.stage = ApplicationStage.APPRAISAL
        application.status = ApplicationStatus.UNDER_REVIEW
        application.updated_by = updated_by

        await self.session.flush()
        await self.session.refresh(application)
        return application

    async def get_application(self, id: UUID) -> LoanApplication:
        """Get application by ID with entity + product eagerly loaded."""
        from sqlalchemy import select as _select
        from sqlalchemy.orm import selectinload

        result = await self.session.execute(
            _select(LoanApplication)
            .where(LoanApplication.id == id)
            .options(
                selectinload(LoanApplication.entity),
                selectinload(LoanApplication.product),
            )
        )
        application = result.scalar_one_or_none()
        if not application:
            raise NotFoundException("Application not found")
        return application

    async def get_application_with_details(self, id: UUID) -> LoanApplication:
        """Get application with all related data."""
        application = await self.app_repo.get_with_details(id)
        if not application:
            raise NotFoundException("Application not found")
        return application

    async def get_all_applications(
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
        """Get all applications with filters."""
        return await self.app_repo.get_all_by_organization(
            organization_id=organization_id,
            skip=skip,
            limit=limit,
            include_inactive=include_inactive,
            search=search,
            entity_id=entity_id,
            product_id=product_id,
            stage=stage,
            status=status,
            relationship_manager_id=relationship_manager_id,
            credit_officer_id=credit_officer_id,
            from_date=from_date,
            to_date=to_date,
        )

    async def get_entity_applications(
        self, entity_id: UUID, include_inactive: bool = False
    ) -> list[LoanApplication]:
        """Get all applications for an entity."""
        return await self.app_repo.get_by_entity(entity_id, include_inactive)

    async def get_stage_counts(self, organization_id: UUID) -> dict[str, int]:
        """Get application counts by stage."""
        return await self.app_repo.get_stage_counts(organization_id)

    async def delete_application(self, id: UUID, deleted_by: UUID) -> None:
        """Soft delete an application."""
        application = await self.app_repo.get(id)
        if not application:
            raise NotFoundException("Application not found")
        if application.status != ApplicationStatus.DRAFT:
            raise ValidationException("Only draft applications can be deleted")
        application.soft_delete(deleted_by)
        await self.session.flush()

    # =========================================================================
    # Application Document Operations
    # =========================================================================

    async def upload_document(
        self, data: ApplicationDocumentCreate, created_by: UUID
    ) -> ApplicationDocument:
        """Upload a document for an application."""
        application = await self.app_repo.get(data.application_id)
        if not application:
            raise NotFoundException("Application not found")

        document_data = data.model_dump()
        document_data["upload_date"] = document_data.get("upload_date") or datetime.utcnow()
        doc = ApplicationDocument(
            **document_data,
            created_by=created_by,
        )
        self.session.add(doc)
        await self.session.flush()
        await self.session.refresh(doc)
        return doc

    async def verify_document(
        self,
        id: UUID,
        verified_by: UUID,
        remarks: str | None = None,
    ) -> ApplicationDocument:
        """Verify an application document."""
        doc = await self.doc_repo.get(id)
        if not doc:
            raise NotFoundException("Document not found")

        doc.status = "VERIFIED"
        doc.verified_by_id = verified_by
        doc.verified_at = datetime.utcnow()
        doc.verification_remarks = remarks
        doc.updated_by = verified_by

        await self.session.flush()
        await self.session.refresh(doc)
        return doc

    async def delete_document(self, id: UUID, deleted_by: UUID) -> None:
        """Soft delete an application document."""
        doc = await self.doc_repo.get(id)
        if not doc:
            raise NotFoundException("Document not found")
        doc.soft_delete(deleted_by)
        await self.session.flush()

    async def get_application_documents(
        self, application_id: UUID, include_inactive: bool = False
    ) -> list[ApplicationDocument]:
        """Get all documents for an application."""
        return await self.doc_repo.get_by_application(application_id, include_inactive)

    # =========================================================================
    # Application Fee Operations
    # =========================================================================

    async def add_application_fee(
        self, data: ApplicationFeeCreate, created_by: UUID
    ) -> ApplicationFee:
        """Add a fee to an application."""
        application = await self.app_repo.get(data.application_id)
        if not application:
            raise NotFoundException("Application not found")

        fee = ApplicationFee(
            **data.model_dump(),
            created_by=created_by,
        )
        self.session.add(fee)
        await self.session.flush()
        await self.session.refresh(fee)
        return fee

    async def collect_fee(
        self,
        id: UUID,
        collected_amount: Decimal,
        collected_date: date,
        collected_by: UUID,
    ) -> ApplicationFee:
        """Record fee collection."""
        fee = await self.fee_repo.get(id)
        if not fee:
            raise NotFoundException("Application fee not found")

        fee.status = "COLLECTED"
        fee.collection_date = collected_date
        fee.collection_reference = f"MANUAL-{collected_by}-{collected_date.isoformat()}"
        fee.updated_by = collected_by

        await self.session.flush()
        await self.session.refresh(fee)
        return fee

    async def get_application_fees(
        self, application_id: UUID, include_inactive: bool = False
    ) -> list[ApplicationFee]:
        """Get all fees for an application."""
        return await self.fee_repo.get_by_application(application_id, include_inactive)

    async def get_fee_summary(self, application_id: UUID) -> dict[str, Any]:
        """Get fee summary for an application."""
        total = await self.fee_repo.get_total_fee_amount(application_id)
        collected = await self.fee_repo.get_total_collected_amount(application_id)
        pending_fees = await self.fee_repo.get_pending_fees(application_id)

        return {
            "total_amount": total,
            "collected_amount": collected,
            "pending_amount": total - collected,
            "pending_fees": pending_fees,
        }

    # =========================================================================
    # Technical Appraisal Operations
    # =========================================================================

    async def create_technical_appraisal(
        self, data: TechnicalAppraisalCreate, created_by: UUID
    ) -> TechnicalAppraisal:
        """Create a technical appraisal."""
        application = await self.app_repo.get(data.application_id)
        if not application:
            raise NotFoundException("Application not found")

        appraisal_data = data.model_dump()
        appraisal_data["appraisal_reference"] = (
            appraisal_data.get("appraisal_reference")
            or f"TA-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"
        )
        appraisal_data["appraiser_id"] = appraisal_data.get("appraiser_id") or created_by
        appraisal = TechnicalAppraisal(
            **appraisal_data,
            created_by=created_by,
        )
        self.session.add(appraisal)
        await self.session.flush()
        await self.session.refresh(appraisal)
        return appraisal

    async def update_technical_appraisal(
        self, id: UUID, data: TechnicalAppraisalUpdate, updated_by: UUID
    ) -> TechnicalAppraisal:
        """Update a technical appraisal."""
        appraisal = await self.tech_appraisal_repo.get(id)
        if not appraisal:
            raise NotFoundException("Technical appraisal not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(appraisal, field, value)
        appraisal.updated_by = updated_by

        await self.session.flush()
        await self.session.refresh(appraisal)
        return appraisal

    async def get_technical_appraisals(
        self, application_id: UUID, include_inactive: bool = False
    ) -> list[TechnicalAppraisal]:
        """Get all technical appraisals for an application."""
        return await self.tech_appraisal_repo.get_by_application(application_id, include_inactive)

    # =========================================================================
    # Financial Analysis Operations
    # =========================================================================

    async def create_financial_analysis(
        self, data: FinancialAnalysisCreate, created_by: UUID
    ) -> FinancialAnalysis:
        """Create a financial analysis."""
        application = await self.app_repo.get(data.application_id)
        if not application:
            raise NotFoundException("Application not found")

        analysis_data = data.model_dump()
        analysis_data["analysis_reference"] = (
            analysis_data.get("analysis_reference")
            or f"FA-{datetime.utcnow().strftime('%Y%m%d')}-{uuid4().hex[:8].upper()}"
        )
        analysis_data["analyst_id"] = analysis_data.get("analyst_id") or created_by
        analysis = FinancialAnalysis(
            **analysis_data,
            created_by=created_by,
        )
        self.session.add(analysis)
        await self.session.flush()
        await self.session.refresh(analysis)
        return analysis

    async def update_financial_analysis(
        self, id: UUID, data: FinancialAnalysisUpdate, updated_by: UUID
    ) -> FinancialAnalysis:
        """Update a financial analysis."""
        analysis = await self.fin_analysis_repo.get(id)
        if not analysis:
            raise NotFoundException("Financial analysis not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(analysis, field, value)
        analysis.updated_by = updated_by

        await self.session.flush()
        await self.session.refresh(analysis)
        return analysis

    async def get_financial_analyses(
        self, application_id: UUID, include_inactive: bool = False
    ) -> list[FinancialAnalysis]:
        """Get all financial analyses for an application."""
        return await self.fin_analysis_repo.get_by_application(application_id, include_inactive)

    # =========================================================================
    # Project Milestone Operations
    # =========================================================================

    async def add_milestone(
        self, data: ProjectMilestoneCreate, created_by: UUID
    ) -> ProjectMilestone:
        """Add a project milestone."""
        application = await self.app_repo.get(data.application_id)
        if not application:
            raise NotFoundException("Application not found")

        milestone = ProjectMilestone(
            **data.model_dump(),
            created_by=created_by,
        )
        self.session.add(milestone)
        await self.session.flush()
        await self.session.refresh(milestone)
        return milestone

    async def update_milestone(
        self, id: UUID, data: ProjectMilestoneUpdate, updated_by: UUID
    ) -> ProjectMilestone:
        """Update a project milestone."""
        milestone = await self.milestone_repo.get(id)
        if not milestone:
            raise NotFoundException("Milestone not found")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(milestone, field, value)
        milestone.updated_by = updated_by

        await self.session.flush()
        await self.session.refresh(milestone)
        return milestone

    async def complete_milestone(
        self,
        id: UUID,
        completion_date: date,
        verified_by: UUID,
        remarks: str | None = None,
    ) -> ProjectMilestone:
        """Mark a milestone as completed."""
        milestone = await self.milestone_repo.get(id)
        if not milestone:
            raise NotFoundException("Milestone not found")

        milestone.status = MilestoneStatus.COMPLETED
        milestone.actual_date = completion_date
        milestone.verified_by_id = verified_by
        milestone.verified_at = datetime.utcnow()
        milestone.verification_remarks = remarks
        milestone.updated_by = verified_by

        await self.session.flush()
        await self.session.refresh(milestone)
        return milestone

    async def get_application_milestones(
        self, application_id: UUID, include_inactive: bool = False
    ) -> list[ProjectMilestone]:
        """Get all milestones for an application."""
        return await self.milestone_repo.get_by_application(application_id, include_inactive)

    async def get_next_milestone(self, application_id: UUID) -> ProjectMilestone | None:
        """Get next pending milestone for an application."""
        return await self.milestone_repo.get_next_milestone(application_id)
