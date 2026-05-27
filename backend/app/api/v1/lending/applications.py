"""Loan Application API endpoints."""

from datetime import date
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_db_with_tenant
from app.models.auth.user import User
from app.models.lending.enums import (
    ApplicationStage,
    ApplicationStatus,
)
from app.schemas.base import PaginatedResponse
from app.schemas.lending.application import (
    ApplicationDocumentCreate,
    ApplicationDocumentResponse,
    ApplicationFeeCreate,
    ApplicationFeeResponse,
    FinancialAnalysisCreate,
    FinancialAnalysisResponse,
    FinancialAnalysisUpdate,
    LoanApplicationCreate,
    LoanApplicationDetailResponse,
    LoanApplicationListResponse,
    LoanApplicationResponse,
    LoanApplicationUpdate,
    LoanApplicationViewResponse,
    ProjectMilestoneCreate,
    ProjectMilestoneResponse,
    ProjectMilestoneUpdate,
    TechnicalAppraisalCreate,
    TechnicalAppraisalResponse,
    TechnicalAppraisalUpdate,
)
from app.services.lending.application_service import ApplicationService

router = APIRouter()


# =============================================================================
# Loan Application CRUD Endpoints
# =============================================================================


@router.get(
    "",
    response_model=PaginatedResponse[LoanApplicationListResponse],
    response_model_by_alias=True,
)
async def list_applications(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100, alias="pageSize"),
    include_inactive: bool = Query(False, alias="includeInactive"),
    search: str | None = Query(None, description="Search in application number, entity name"),
    entity_id: UUID | None = Query(None, alias="entityId"),
    product_id: UUID | None = Query(None, alias="productId"),
    stage: ApplicationStage | None = Query(None),
    status: ApplicationStatus | None = Query(None),
    relationship_manager_id: UUID | None = Query(None, alias="relationshipManagerId"),
    credit_officer_id: UUID | None = Query(None, alias="creditOfficerId"),
    from_date: date | None = Query(None, alias="fromDate"),
    to_date: date | None = Query(None, alias="toDate"),
    current_user: User = Depends(RequirePermissions("LOS_APPLICATION_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get paginated list of loan applications."""
    service = ApplicationService(db)
    skip = (page - 1) * page_size
    applications, total = await service.get_all_applications(
        organization_id=current_user.organization_id,
        skip=skip,
        limit=page_size,
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
    items = [LoanApplicationListResponse.model_validate(a) for a in applications]
    return PaginatedResponse.create(items, total, page, page_size)


@router.get("/stage-counts")
async def get_stage_counts(
    current_user: User = Depends(RequirePermissions("LOS_APPLICATION_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get application counts by stage for pipeline view."""
    service = ApplicationService(db)
    counts = await service.get_stage_counts(current_user.organization_id)
    return counts


@router.get(
    "/entity/{entity_id}",
    response_model=list[LoanApplicationListResponse],
    response_model_by_alias=True,
)
async def get_entity_applications(
    entity_id: UUID,
    include_inactive: bool = Query(False, alias="includeInactive"),
    current_user: User = Depends(RequirePermissions("LOS_APPLICATION_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get all applications for an entity."""
    service = ApplicationService(db)
    applications = await service.get_entity_applications(entity_id, include_inactive)
    return [LoanApplicationListResponse.model_validate(a) for a in applications]


@router.post(
    "",
    response_model=LoanApplicationResponse,
    response_model_by_alias=True,
)
async def create_application(
    data: LoanApplicationCreate,
    current_user: User = Depends(RequirePermissions("LOS_APPLICATION_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Create a new loan application."""
    data.organization_id = current_user.organization_id
    service = ApplicationService(db)
    application = await service.create_application(data, current_user.id)
    return LoanApplicationResponse.model_validate(application)


@router.get(
    "/{application_id}",
    response_model=LoanApplicationViewResponse,
    response_model_by_alias=True,
)
async def get_application(
    application_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_APPLICATION_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get loan application by ID (camelCase view shape with joined entity/product)."""
    service = ApplicationService(db)
    application = await service.get_application(application_id)
    return LoanApplicationViewResponse.model_validate(application)


@router.get(
    "/{application_id}/details",
    response_model=LoanApplicationDetailResponse,
    response_model_by_alias=True,
)
async def get_application_details(
    application_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_APPLICATION_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get loan application with all related data."""
    service = ApplicationService(db)
    application = await service.get_application_with_details(application_id)
    return LoanApplicationDetailResponse.model_validate(application)


@router.put(
    "/{application_id}",
    response_model=LoanApplicationResponse,
    response_model_by_alias=True,
)
async def update_application(
    application_id: UUID,
    data: LoanApplicationUpdate,
    current_user: User = Depends(RequirePermissions("LOS_APPLICATION_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Update a loan application."""
    service = ApplicationService(db)
    application = await service.update_application(application_id, data, current_user.id)
    return LoanApplicationResponse.model_validate(application)


@router.post(
    "/{application_id}/submit",
    response_model=LoanApplicationResponse,
    response_model_by_alias=True,
)
async def submit_application(
    application_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_APPLICATION_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Submit application for processing."""
    service = ApplicationService(db)
    application = await service.submit_application(application_id, current_user.id)
    return LoanApplicationResponse.model_validate(application)


@router.post(
    "/{application_id}/move-to-appraisal",
    response_model=LoanApplicationResponse,
    response_model_by_alias=True,
)
async def move_to_appraisal(
    application_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_APPLICATION_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Move application to appraisal stage."""
    service = ApplicationService(db)
    application = await service.move_to_appraisal(application_id, current_user.id)
    return LoanApplicationResponse.model_validate(application)


@router.delete("/{application_id}")
async def delete_application(
    application_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_APPLICATION_DELETE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Soft delete a loan application (draft only)."""
    service = ApplicationService(db)
    await service.delete_application(application_id, current_user.id)
    return {"message": "Application deleted successfully"}


# =============================================================================
# Application Document Endpoints
# =============================================================================


@router.get(
    "/{application_id}/documents",
    response_model=list[ApplicationDocumentResponse],
    response_model_by_alias=True,
)
async def list_application_documents(
    application_id: UUID,
    include_inactive: bool = Query(False),
    current_user: User = Depends(RequirePermissions("LOS_APPLICATION_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get all documents for an application."""
    service = ApplicationService(db)
    documents = await service.get_application_documents(application_id, include_inactive)
    return [ApplicationDocumentResponse.model_validate(d) for d in documents]


@router.post(
    "/{application_id}/documents",
    response_model=ApplicationDocumentResponse,
    response_model_by_alias=True,
)
async def upload_document(
    application_id: UUID,
    data: ApplicationDocumentCreate,
    current_user: User = Depends(RequirePermissions("LOS_APPLICATION_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Upload a document for an application."""
    data.application_id = application_id
    service = ApplicationService(db)
    document = await service.upload_document(data, current_user.id)
    return ApplicationDocumentResponse.model_validate(document)


@router.post(
    "/{application_id}/documents/{document_id}/verify",
    response_model=ApplicationDocumentResponse,
    response_model_by_alias=True,
)
async def verify_document(
    application_id: UUID,
    document_id: UUID,
    remarks: str | None = Query(None),
    current_user: User = Depends(RequirePermissions("LOS_APPLICATION_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Verify an application document."""
    service = ApplicationService(db)
    document = await service.verify_document(document_id, current_user.id, remarks)
    return ApplicationDocumentResponse.model_validate(document)


@router.delete("/{application_id}/documents/{document_id}")
async def delete_document(
    application_id: UUID,
    document_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_APPLICATION_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Soft delete an application document."""
    service = ApplicationService(db)
    await service.delete_document(document_id, current_user.id)
    return {"message": "Document deleted successfully"}


@router.post(
    "/{application_id}/documents/{document_id}/replace",
    response_model=ApplicationDocumentResponse,
    response_model_by_alias=True,
)
async def replace_document(
    application_id: UUID,
    document_id: UUID,
    payload: dict[str, Any],
    current_user: User = Depends(RequirePermissions("LOS_APPLICATION_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Re-upload a document — supersedes the prior version (Phase C.3).

    Expected payload keys: ``new_file_path``, ``new_file_name``,
    ``new_file_size_bytes``, ``new_file_mime_type``, optional
    ``new_dms_document_id``.
    """
    service = ApplicationService(db)
    document = await service.replace_document(
        document_id=document_id,
        new_file_path=payload["new_file_path"],
        new_file_name=payload["new_file_name"],
        new_file_size_bytes=int(payload["new_file_size_bytes"]),
        new_file_mime_type=payload["new_file_mime_type"],
        new_dms_document_id=payload.get("new_dms_document_id"),
        replaced_by=current_user.id,
        replaced_by_kind=payload.get("replaced_by_kind", "LENDER"),
    )
    await db.commit()
    return ApplicationDocumentResponse.model_validate(document)


@router.get("/{application_id}/documents/{document_id}/versions")
async def list_document_versions(
    application_id: UUID,
    document_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_APPLICATION_READ")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Return the version chain (oldest → newest) for an application document."""
    service = ApplicationService(db)
    versions = await service.get_document_versions(document_id)
    return {
        "documentId": str(document_id),
        "versions": [
            {
                "id": str(v.id),
                "version": v.version,
                "isActive": v.is_active,
                "fileName": v.file_name,
                "uploadedAt": v.created_at.isoformat() if v.created_at else None,
                "previousVersionId": str(v.previous_version_id) if v.previous_version_id else None,
            }
            for v in versions
        ],
    }


# =============================================================================
# Application Fee Endpoints
# =============================================================================


@router.get(
    "/{application_id}/fees",
    response_model=list[ApplicationFeeResponse],
    response_model_by_alias=True,
)
async def list_application_fees(
    application_id: UUID,
    include_inactive: bool = Query(False),
    current_user: User = Depends(RequirePermissions("LOS_APPLICATION_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get all fees for an application."""
    service = ApplicationService(db)
    fees = await service.get_application_fees(application_id, include_inactive)
    return [ApplicationFeeResponse.model_validate(f) for f in fees]


@router.get("/{application_id}/fees/summary")
async def get_fee_summary(
    application_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_APPLICATION_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get fee summary for an application."""
    service = ApplicationService(db)
    summary = await service.get_fee_summary(application_id)
    return summary


@router.post(
    "/{application_id}/fees",
    response_model=ApplicationFeeResponse,
    response_model_by_alias=True,
)
async def add_application_fee(
    application_id: UUID,
    data: ApplicationFeeCreate,
    current_user: User = Depends(RequirePermissions("LOS_APPLICATION_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Add a fee to an application."""
    data.application_id = application_id
    service = ApplicationService(db)
    fee = await service.add_application_fee(data, current_user.id)
    return ApplicationFeeResponse.model_validate(fee)


@router.post(
    "/fees/{fee_id}/collect",
    response_model=ApplicationFeeResponse,
    response_model_by_alias=True,
)
async def collect_fee(
    fee_id: UUID,
    collected_amount: Decimal = Query(...),
    collected_date: date = Query(...),
    current_user: User = Depends(RequirePermissions("LOS_APPLICATION_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Record fee collection."""
    service = ApplicationService(db)
    fee = await service.collect_fee(fee_id, collected_amount, collected_date, current_user.id)
    return ApplicationFeeResponse.model_validate(fee)


# =============================================================================
# Technical Appraisal Endpoints
# =============================================================================


@router.get(
    "/{application_id}/appraisals/technical",
    response_model=list[TechnicalAppraisalResponse],
    response_model_by_alias=True,
)
async def list_technical_appraisals(
    application_id: UUID,
    include_inactive: bool = Query(False),
    current_user: User = Depends(RequirePermissions("LOS_APPLICATION_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get all technical appraisals for an application."""
    service = ApplicationService(db)
    appraisals = await service.get_technical_appraisals(application_id, include_inactive)
    return [TechnicalAppraisalResponse.model_validate(a) for a in appraisals]


@router.post(
    "/{application_id}/appraisals/technical",
    response_model=TechnicalAppraisalResponse,
    response_model_by_alias=True,
)
async def create_technical_appraisal(
    application_id: UUID,
    data: TechnicalAppraisalCreate,
    current_user: User = Depends(RequirePermissions("LOS_APPRAISAL_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Create a technical appraisal."""
    data.application_id = application_id
    service = ApplicationService(db)
    appraisal = await service.create_technical_appraisal(data, current_user.id)
    return TechnicalAppraisalResponse.model_validate(appraisal)


@router.put(
    "/appraisals/technical/{appraisal_id}",
    response_model=TechnicalAppraisalResponse,
    response_model_by_alias=True,
)
async def update_technical_appraisal(
    appraisal_id: UUID,
    data: TechnicalAppraisalUpdate,
    current_user: User = Depends(RequirePermissions("LOS_APPRAISAL_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Update a technical appraisal."""
    service = ApplicationService(db)
    appraisal = await service.update_technical_appraisal(appraisal_id, data, current_user.id)
    return TechnicalAppraisalResponse.model_validate(appraisal)


# =============================================================================
# Financial Analysis Endpoints
# =============================================================================


@router.get(
    "/{application_id}/appraisals/financial",
    response_model=list[FinancialAnalysisResponse],
    response_model_by_alias=True,
)
async def list_financial_analyses(
    application_id: UUID,
    include_inactive: bool = Query(False),
    current_user: User = Depends(RequirePermissions("LOS_APPLICATION_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get all financial analyses for an application."""
    service = ApplicationService(db)
    analyses = await service.get_financial_analyses(application_id, include_inactive)
    return [FinancialAnalysisResponse.model_validate(a) for a in analyses]


@router.post(
    "/{application_id}/appraisals/financial",
    response_model=FinancialAnalysisResponse,
    response_model_by_alias=True,
)
async def create_financial_analysis(
    application_id: UUID,
    data: FinancialAnalysisCreate,
    current_user: User = Depends(RequirePermissions("LOS_APPRAISAL_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Create a financial analysis."""
    data.application_id = application_id
    service = ApplicationService(db)
    analysis = await service.create_financial_analysis(data, current_user.id)
    return FinancialAnalysisResponse.model_validate(analysis)


@router.put(
    "/appraisals/financial/{analysis_id}",
    response_model=FinancialAnalysisResponse,
    response_model_by_alias=True,
)
async def update_financial_analysis(
    analysis_id: UUID,
    data: FinancialAnalysisUpdate,
    current_user: User = Depends(RequirePermissions("LOS_APPRAISAL_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Update a financial analysis."""
    service = ApplicationService(db)
    analysis = await service.update_financial_analysis(analysis_id, data, current_user.id)
    return FinancialAnalysisResponse.model_validate(analysis)


# =============================================================================
# Project Milestone Endpoints
# =============================================================================


@router.get(
    "/{application_id}/milestones",
    response_model=list[ProjectMilestoneResponse],
    response_model_by_alias=True,
)
async def list_milestones(
    application_id: UUID,
    include_inactive: bool = Query(False),
    current_user: User = Depends(RequirePermissions("LOS_APPLICATION_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get all milestones for an application."""
    service = ApplicationService(db)
    milestones = await service.get_application_milestones(application_id, include_inactive)
    return [ProjectMilestoneResponse.model_validate(m) for m in milestones]


@router.get(
    "/{application_id}/milestones/next",
    response_model=ProjectMilestoneResponse,
    response_model_by_alias=True,
)
async def get_next_milestone(
    application_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_APPLICATION_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get the next pending milestone for an application."""
    service = ApplicationService(db)
    milestone = await service.get_next_milestone(application_id)
    if milestone:
        return ProjectMilestoneResponse.model_validate(milestone)
    return None


@router.post(
    "/{application_id}/milestones",
    response_model=ProjectMilestoneResponse,
    response_model_by_alias=True,
)
async def add_milestone(
    application_id: UUID,
    data: ProjectMilestoneCreate,
    current_user: User = Depends(RequirePermissions("LOS_APPLICATION_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Add a milestone to an application."""
    data.application_id = application_id
    service = ApplicationService(db)
    milestone = await service.add_milestone(data, current_user.id)
    return ProjectMilestoneResponse.model_validate(milestone)


@router.put(
    "/milestones/{milestone_id}",
    response_model=ProjectMilestoneResponse,
    response_model_by_alias=True,
)
async def update_milestone(
    milestone_id: UUID,
    data: ProjectMilestoneUpdate,
    current_user: User = Depends(RequirePermissions("LOS_APPLICATION_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Update a milestone."""
    service = ApplicationService(db)
    milestone = await service.update_milestone(milestone_id, data, current_user.id)
    return ProjectMilestoneResponse.model_validate(milestone)


@router.post(
    "/milestones/{milestone_id}/complete",
    response_model=ProjectMilestoneResponse,
    response_model_by_alias=True,
)
async def complete_milestone(
    milestone_id: UUID,
    completion_date: date = Query(...),
    remarks: str | None = Query(None),
    current_user: User = Depends(RequirePermissions("LOS_APPLICATION_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Mark a milestone as completed."""
    service = ApplicationService(db)
    milestone = await service.complete_milestone(
        milestone_id, completion_date, current_user.id, remarks
    )
    return ProjectMilestoneResponse.model_validate(milestone)
