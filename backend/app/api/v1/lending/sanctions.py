"""Loan Sanction API endpoints."""

from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_db_with_tenant
from app.models.auth.user import User
from app.models.lending.enums import (
    ConditionType,
    SanctionStatus,
)
from app.schemas.base import PaginatedResponse
from app.schemas.lending.sanction import (
    LoanSanctionCreate,
    LoanSanctionDetailResponse,
    LoanSanctionListResponse,
    LoanSanctionResponse,
    LoanSanctionUpdate,
    LoanSecurityCreate,
    LoanSecurityResponse,
    LoanSecurityUpdate,
    SanctionConditionCreate,
    SanctionConditionResponse,
    SanctionConditionUpdate,
)
from app.services.lending.sanction_service import SanctionService

router = APIRouter()


# =============================================================================
# Loan Sanction CRUD Endpoints
# =============================================================================


@router.get(
    "",
    response_model=PaginatedResponse[LoanSanctionListResponse],
    response_model_by_alias=True,
)
async def list_sanctions(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100, alias="pageSize"),
    include_inactive: bool = Query(False, alias="includeInactive"),
    search: str | None = Query(None, description="Search in sanction number"),
    entity_id: UUID | None = Query(None, alias="entityId"),
    status: SanctionStatus | None = Query(None),
    from_date: date | None = Query(None, alias="fromDate"),
    to_date: date | None = Query(None, alias="toDate"),
    current_user: User = Depends(RequirePermissions("LOS_SANCTION_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get paginated list of loan sanctions."""
    service = SanctionService(db)
    skip = (page - 1) * page_size
    sanctions, total = await service.get_all_sanctions(
        organization_id=current_user.organization_id,
        skip=skip,
        limit=page_size,
        include_inactive=include_inactive,
        search=search,
        entity_id=entity_id,
        status=status,
        from_date=from_date,
        to_date=to_date,
    )
    items = [LoanSanctionListResponse.model_validate(s) for s in sanctions]
    return PaginatedResponse.create(items, total, page, page_size)


@router.get(
    "/entity/{entity_id}",
    response_model=list[LoanSanctionListResponse],
    response_model_by_alias=True,
)
async def get_entity_sanctions(
    entity_id: UUID,
    include_inactive: bool = Query(False),
    current_user: User = Depends(RequirePermissions("LOS_SANCTION_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get all sanctions for an entity."""
    service = SanctionService(db)
    sanctions = await service.get_entity_sanctions(entity_id, include_inactive)
    return [LoanSanctionListResponse.model_validate(s) for s in sanctions]


@router.get(
    "/application/{application_id}",
    response_model=Optional[LoanSanctionResponse],
    response_model_by_alias=True,
)
async def get_sanction_by_application(
    application_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_SANCTION_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get sanction for an application."""
    service = SanctionService(db)
    sanction = await service.get_sanction_by_application(application_id)
    if sanction:
        return LoanSanctionResponse.model_validate(sanction)
    return None


@router.get("/total-sanctioned")
async def get_total_sanctioned_amount(
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    current_user: User = Depends(RequirePermissions("LOS_SANCTION_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get total sanctioned amount for an organization."""
    service = SanctionService(db)
    total = await service.get_total_sanctioned_amount(
        current_user.organization_id, from_date, to_date
    )
    return {"totalSanctionedAmount": total}


@router.post(
    "",
    response_model=LoanSanctionResponse,
    response_model_by_alias=True,
)
async def create_sanction(
    data: LoanSanctionCreate,
    current_user: User = Depends(RequirePermissions("LOS_SANCTION_CREATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Create a new loan sanction."""
    data.organization_id = current_user.organization_id
    service = SanctionService(db)
    sanction = await service.create_sanction(data, current_user.id)
    return LoanSanctionResponse.model_validate(sanction)


@router.get(
    "/{sanction_id}",
    response_model=LoanSanctionResponse,
    response_model_by_alias=True,
)
async def get_sanction(
    sanction_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_SANCTION_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get loan sanction by ID."""
    service = SanctionService(db)
    sanction = await service.get_sanction(sanction_id)
    return LoanSanctionResponse.model_validate(sanction)


@router.get(
    "/{sanction_id}/details",
    response_model=LoanSanctionDetailResponse,
    response_model_by_alias=True,
)
async def get_sanction_details(
    sanction_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_SANCTION_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get loan sanction with conditions and securities."""
    service = SanctionService(db)
    sanction = await service.get_sanction_with_details(sanction_id)
    return LoanSanctionDetailResponse.model_validate(sanction)


@router.put(
    "/{sanction_id}",
    response_model=LoanSanctionResponse,
    response_model_by_alias=True,
)
async def update_sanction(
    sanction_id: UUID,
    data: LoanSanctionUpdate,
    current_user: User = Depends(RequirePermissions("LOS_SANCTION_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Update a loan sanction."""
    service = SanctionService(db)
    sanction = await service.update_sanction(sanction_id, data, current_user.id)
    return LoanSanctionResponse.model_validate(sanction)


@router.post(
    "/{sanction_id}/submit",
    response_model=LoanSanctionResponse,
    response_model_by_alias=True,
)
async def submit_for_approval(
    sanction_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_SANCTION_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Submit sanction for approval."""
    service = SanctionService(db)
    sanction = await service.submit_for_approval(sanction_id, current_user.id)
    return LoanSanctionResponse.model_validate(sanction)


@router.post(
    "/{sanction_id}/approve",
    response_model=LoanSanctionResponse,
    response_model_by_alias=True,
)
async def approve_sanction(
    sanction_id: UUID,
    remarks: str | None = Query(None),
    current_user: User = Depends(RequirePermissions("LOS_SANCTION_APPROVE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Approve a sanction."""
    service = SanctionService(db)
    sanction = await service.approve_sanction(sanction_id, current_user.id, remarks)
    return LoanSanctionResponse.model_validate(sanction)


@router.post(
    "/{sanction_id}/accept",
    response_model=LoanSanctionResponse,
    response_model_by_alias=True,
)
async def record_borrower_acceptance(
    sanction_id: UUID,
    acceptance_date: date = Query(...),
    document_path: str | None = Query(None),
    current_user: User = Depends(RequirePermissions("LOS_SANCTION_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Record borrower acceptance of sanction."""
    service = SanctionService(db)
    sanction = await service.record_borrower_acceptance(
        sanction_id, acceptance_date, document_path, current_user.id
    )
    return LoanSanctionResponse.model_validate(sanction)


@router.get("/{sanction_id}/disbursement-eligibility")
async def check_disbursement_eligibility(
    sanction_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_SANCTION_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Check if sanction is eligible for disbursement."""
    service = SanctionService(db)
    eligibility = await service.check_disbursement_eligible(sanction_id)
    return eligibility


# =============================================================================
# Sanction Condition Endpoints
# =============================================================================


@router.get(
    "/{sanction_id}/conditions",
    response_model=list[SanctionConditionResponse],
    response_model_by_alias=True,
)
async def list_conditions(
    sanction_id: UUID,
    include_inactive: bool = Query(False),
    current_user: User = Depends(RequirePermissions("LOS_SANCTION_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get all conditions for a sanction."""
    service = SanctionService(db)
    conditions = await service.get_sanction_conditions(sanction_id, include_inactive)
    return [SanctionConditionResponse.model_validate(c) for c in conditions]


@router.get(
    "/{sanction_id}/conditions/pending",
    response_model=list[SanctionConditionResponse],
    response_model_by_alias=True,
)
async def get_pending_conditions(
    sanction_id: UUID,
    condition_type: ConditionType | None = Query(None),
    current_user: User = Depends(RequirePermissions("LOS_SANCTION_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get pending conditions for a sanction."""
    service = SanctionService(db)
    conditions = await service.get_pending_conditions(sanction_id, condition_type)
    return [SanctionConditionResponse.model_validate(c) for c in conditions]


@router.post(
    "/{sanction_id}/conditions",
    response_model=SanctionConditionResponse,
    response_model_by_alias=True,
)
async def add_condition(
    sanction_id: UUID,
    data: SanctionConditionCreate,
    current_user: User = Depends(RequirePermissions("LOS_SANCTION_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Add a condition to a sanction."""
    data.sanction_id = sanction_id
    service = SanctionService(db)
    condition = await service.add_condition(data, current_user.id)
    return SanctionConditionResponse.model_validate(condition)


@router.put(
    "/conditions/{condition_id}",
    response_model=SanctionConditionResponse,
    response_model_by_alias=True,
)
async def update_condition(
    condition_id: UUID,
    data: SanctionConditionUpdate,
    current_user: User = Depends(RequirePermissions("LOS_SANCTION_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Update a sanction condition."""
    service = SanctionService(db)
    condition = await service.update_condition(condition_id, data, current_user.id)
    return SanctionConditionResponse.model_validate(condition)


@router.post(
    "/conditions/{condition_id}/comply",
    response_model=SanctionConditionResponse,
    response_model_by_alias=True,
)
async def comply_condition(
    condition_id: UUID,
    complied_on: date = Query(...),
    remarks: str | None = Query(None),
    document_path: str | None = Query(None),
    current_user: User = Depends(RequirePermissions("LOS_SANCTION_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Mark a condition as complied."""
    service = SanctionService(db)
    condition = await service.comply_condition(
        condition_id, complied_on, current_user.id, remarks, document_path
    )
    return SanctionConditionResponse.model_validate(condition)


@router.post(
    "/conditions/{condition_id}/waive",
    response_model=SanctionConditionResponse,
    response_model_by_alias=True,
)
async def waive_condition(
    condition_id: UUID,
    waiver_remarks: str = Query(...),
    current_user: User = Depends(RequirePermissions("LOS_SANCTION_APPROVE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Waive a condition."""
    service = SanctionService(db)
    condition = await service.waive_condition(condition_id, current_user.id, waiver_remarks)
    return SanctionConditionResponse.model_validate(condition)


# =============================================================================
# Loan Security Endpoints
# =============================================================================


@router.get(
    "/{sanction_id}/securities",
    response_model=list[LoanSecurityResponse],
    response_model_by_alias=True,
)
async def list_securities(
    sanction_id: UUID,
    include_inactive: bool = Query(False),
    current_user: User = Depends(RequirePermissions("LOS_SANCTION_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get all securities for a sanction."""
    service = SanctionService(db)
    securities = await service.get_sanction_securities(sanction_id, include_inactive)
    return [LoanSecurityResponse.model_validate(s) for s in securities]


@router.get("/{sanction_id}/securities/summary")
async def get_security_summary(
    sanction_id: UUID,
    current_user: User = Depends(RequirePermissions("LOS_SANCTION_VIEW")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get security summary for a sanction."""
    service = SanctionService(db)
    summary = await service.get_security_summary(sanction_id)
    return summary


@router.post(
    "/{sanction_id}/securities",
    response_model=LoanSecurityResponse,
    response_model_by_alias=True,
)
async def add_security(
    sanction_id: UUID,
    data: LoanSecurityCreate,
    current_user: User = Depends(RequirePermissions("LOS_SANCTION_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Add a security to a sanction."""
    data.sanction_id = sanction_id
    service = SanctionService(db)
    security = await service.add_security(data, current_user.id)
    return LoanSecurityResponse.model_validate(security)


@router.put(
    "/securities/{security_id}",
    response_model=LoanSecurityResponse,
    response_model_by_alias=True,
)
async def update_security(
    security_id: UUID,
    data: LoanSecurityUpdate,
    current_user: User = Depends(RequirePermissions("LOS_SANCTION_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Update a loan security."""
    service = SanctionService(db)
    security = await service.update_security(security_id, data, current_user.id)
    return LoanSecurityResponse.model_validate(security)


@router.post(
    "/securities/{security_id}/register",
    response_model=LoanSecurityResponse,
    response_model_by_alias=True,
)
async def register_security(
    security_id: UUID,
    cersai_registration_id: str = Query(...),
    registration_date: date = Query(...),
    current_user: User = Depends(RequirePermissions("LOS_SANCTION_UPDATE")),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Register security with CERSAI."""
    service = SanctionService(db)
    security = await service.register_security(
        security_id, cersai_registration_id, registration_date, current_user.id
    )
    return LoanSecurityResponse.model_validate(security)
