"""Phase 3: NPA & Collections API endpoints for the lending module."""

from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Body, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_current_user, get_db_with_tenant
from app.models.lending.enums import (
    AssetClassification,
    FollowUpStatus,
    LegalCaseStatus,
    OTSStatus,
    RestructureStatus,
)
from app.schemas.base import PaginatedResponse as PaginatedResponseBase
from app.schemas.lending.collections import (
    CollectionActivitySummary,
    # Follow-Up
    CollectionFollowUpCreate,
    CollectionFollowUpExecute,
    CollectionFollowUpResponse,
    CollectionFollowUpUpdate,
    # Demand Notice
    DemandNoticeCreate,
    DemandNoticeResponse,
    DemandNoticeUpdate,
    FollowUpListResponse,
    # Legal Case
    LegalCaseCreate,
    LegalCaseListResponse,
    LegalCaseResponse,
    LegalCaseUpdate,
    # Legal Hearing
    LegalHearingCreate,
    LegalHearingResponse,
    LegalHearingUpdate,
    LoanRestructureApprove,
    # Restructure
    LoanRestructureCreate,
    LoanRestructureImplement,
    LoanRestructureReject,
    LoanRestructureResponse,
    LoanRestructureUpdate,
    NPAAccountListResponse,
    # NPA Record
    NPARecordCreate,
    NPARecordResponse,
    NPARecordUpdate,
    # Summary
    NPASummary,
    OTSBorrowerAccept,
    OTSPaymentScheduleCreate,
    OTSProposalApprove,
    # OTS
    OTSProposalCreate,
    # Slim list responses (camelCase)
    OTSProposalListResponse,
    OTSProposalResponse,
    OTSProposalUpdate,
    # Penal Interest
    PenalInterestResponse,
    PenalWaiverApprove,
    # Penal Waiver
    PenalWaiverCreate,
    PenalWaiverResponse,
    # Auction
    PropertyAuctionCreate,
    PropertyAuctionResponse,
    PropertyAuctionUpdate,
    RecoverySummary,
    RestructureListResponse,
    WriteOffApprove,
    # Write-Off
    WriteOffCreate,
    WriteOffEffect,
    WriteOffResponse,
)
from app.services.lending.collections_service import CollectionsService
from app.core.exceptions import NotFoundException

router = APIRouter()


# =============================================================================
# Summary & Dashboard Endpoints
# =============================================================================

# =============================================================================
# Paginated list endpoints (camelCase wire format via CamelSchema)
# =============================================================================


@router.get(
    "/legal-cases",
    response_model=PaginatedResponseBase[LegalCaseListResponse],
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("COLLECTIONS_READ"))],
)
async def list_legal_cases(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200, alias="pageSize"),
    status: LegalCaseStatus | None = Query(None),
    case_type: str | None = Query(None, alias="caseType"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Paginated list of legal cases scoped to caller's org."""
    service = CollectionsService(db)
    skip = (page - 1) * page_size
    items, total = await service.list_legal_cases_for_org(
        organization_id=current_user.organization_id,
        skip=skip,
        limit=page_size,
        status=status,
        case_type=case_type,
    )
    list_items = [LegalCaseListResponse.model_validate(i) for i in items]
    return PaginatedResponseBase.create(list_items, total, page, page_size)


@router.get(
    "/npa-accounts",
    response_model=PaginatedResponseBase[NPAAccountListResponse],
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("COLLECTIONS_READ"))],
)
async def list_npa_accounts(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200, alias="pageSize"),
    classification: AssetClassification | None = Query(None),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Paginated list of NPA-classified loan accounts scoped to caller's org."""
    service = CollectionsService(db)
    skip = (page - 1) * page_size
    rows, total = await service.list_npa_accounts_for_org(
        organization_id=current_user.organization_id,
        skip=skip,
        limit=page_size,
        classification=classification,
    )
    list_items = [NPAAccountListResponse.model_validate(row) for row in rows]
    return PaginatedResponseBase.create(list_items, total, page, page_size)


@router.get(
    "/follow-ups",
    response_model=PaginatedResponseBase[FollowUpListResponse],
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("COLLECTIONS_READ"))],
)
async def list_follow_ups(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200, alias="pageSize"),
    status: FollowUpStatus | None = Query(None),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Paginated list of collection follow-ups scoped to caller's org."""
    service = CollectionsService(db)
    skip = (page - 1) * page_size
    items, total = await service.list_follow_ups_for_org(
        organization_id=current_user.organization_id,
        skip=skip,
        limit=page_size,
        status=status,
    )
    list_items = [FollowUpListResponse.model_validate(i) for i in items]
    return PaginatedResponseBase.create(list_items, total, page, page_size)


@router.get(
    "/ots-proposals",
    response_model=PaginatedResponseBase[OTSProposalListResponse],
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("COLLECTIONS_READ"))],
)
async def list_ots_proposals(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200, alias="pageSize"),
    status: OTSStatus | None = Query(None),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Paginated list of OTS proposals scoped to caller's org."""
    service = CollectionsService(db)
    skip = (page - 1) * page_size
    items, total = await service.list_ots_proposals_for_org(
        organization_id=current_user.organization_id,
        skip=skip,
        limit=page_size,
        status=status,
    )
    list_items = [OTSProposalListResponse.model_validate(i) for i in items]
    return PaginatedResponseBase.create(list_items, total, page, page_size)


@router.get(
    "/restructures",
    response_model=PaginatedResponseBase[RestructureListResponse],
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("COLLECTIONS_READ"))],
)
async def list_restructures(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200, alias="pageSize"),
    status: RestructureStatus | None = Query(None),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Paginated list of loan restructures scoped to caller's org."""
    service = CollectionsService(db)
    skip = (page - 1) * page_size
    items, total = await service.list_restructures_for_org(
        organization_id=current_user.organization_id,
        skip=skip,
        limit=page_size,
        status=status,
    )
    list_items = [RestructureListResponse.model_validate(i) for i in items]
    return PaginatedResponseBase.create(list_items, total, page, page_size)


@router.get(
    "/summary/npa",
    response_model=NPASummary,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("COLLECTIONS_READ"))],
)
async def get_npa_summary(
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Get NPA portfolio summary (camelCase, scoped to caller's org)."""
    service = CollectionsService(db)
    return await service.get_npa_summary(current_user.organization_id)


@router.get(
    "/summary/collection",
    response_model=CollectionActivitySummary,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("COLLECTIONS_READ"))],
)
async def get_collection_summary(
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Get collection activity summary (camelCase, scoped to caller's org)."""
    service = CollectionsService(db)
    return await service.get_collection_summary(current_user.organization_id)


@router.get(
    "/summary/recovery",
    response_model=RecoverySummary,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("COLLECTIONS_READ"))],
)
async def get_recovery_summary(
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Get recovery summary (camelCase, scoped to caller's org)."""
    service = CollectionsService(db)
    return await service.get_recovery_summary(current_user.organization_id)


# =============================================================================
# Collection Follow-Up Endpoints
# =============================================================================


@router.post(
    "/follow-ups",
    response_model=CollectionFollowUpResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermissions("COLLECTIONS_CREATE"))],
)
async def create_follow_up(
    data: CollectionFollowUpCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Create a collection follow-up."""
    service = CollectionsService(db)
    follow_up = await service.create_follow_up(data, current_user.id)
    return CollectionFollowUpResponse.model_validate(follow_up)


@router.get(
    "/follow-ups/scheduled",
    response_model=list[CollectionFollowUpResponse],
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("COLLECTIONS_READ"))],
)
async def get_scheduled_follow_ups(
    scheduled_date: date = Query(...),
    assigned_to_id: UUID | None = None,
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get follow-ups scheduled for a specific date."""
    service = CollectionsService(db)
    follow_ups = await service.get_scheduled_follow_ups(scheduled_date, assigned_to_id)
    return [CollectionFollowUpResponse.model_validate(f) for f in follow_ups]


@router.put(
    "/follow-ups/{follow_up_id}",
    response_model=CollectionFollowUpResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("COLLECTIONS_UPDATE"))],
)
async def update_follow_up(
    follow_up_id: UUID,
    data: CollectionFollowUpUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Update a collection follow-up."""
    service = CollectionsService(db)
    follow_up = await service.update_follow_up(follow_up_id, data, current_user.id)
    return CollectionFollowUpResponse.model_validate(follow_up)


@router.post(
    "/follow-ups/{follow_up_id}/execute",
    response_model=CollectionFollowUpResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("COLLECTIONS_UPDATE"))],
)
async def execute_follow_up(
    follow_up_id: UUID,
    data: CollectionFollowUpExecute,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Record follow-up execution outcome."""
    service = CollectionsService(db)
    follow_up = await service.execute_follow_up(follow_up_id, data, current_user.id)
    return CollectionFollowUpResponse.model_validate(follow_up)


@router.post(
    "/follow-ups/{follow_up_id}/mark-ptp-broken",
    response_model=CollectionFollowUpResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("COLLECTIONS_UPDATE"))],
)
async def mark_ptp_broken(
    follow_up_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Mark a Promise to Pay as broken."""
    service = CollectionsService(db)
    follow_up = await service.mark_ptp_broken(follow_up_id, current_user.id)
    return CollectionFollowUpResponse.model_validate(follow_up)


# =============================================================================
# Demand Notice Endpoints
# =============================================================================


@router.post(
    "/demand-notices",
    response_model=DemandNoticeResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermissions("COLLECTIONS_CREATE"))],
)
async def create_demand_notice(
    data: DemandNoticeCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Create a demand notice."""
    service = CollectionsService(db)
    notice = await service.create_demand_notice(data, current_user.id)
    return DemandNoticeResponse.model_validate(notice)


@router.get(
    "/loan-accounts/{loan_account_id}/demand-notices",
    response_model=list[DemandNoticeResponse],
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("COLLECTIONS_READ"))],
)
async def get_demand_notices(
    loan_account_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get demand notices for a loan account."""
    service = CollectionsService(db)
    notices = await service.get_demand_notices(loan_account_id, skip, limit)
    return [DemandNoticeResponse.model_validate(n) for n in notices]


@router.put(
    "/demand-notices/{notice_id}",
    response_model=DemandNoticeResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("COLLECTIONS_UPDATE"))],
)
async def update_demand_notice(
    notice_id: UUID,
    data: DemandNoticeUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Update a demand notice."""
    service = CollectionsService(db)
    notice = await service.update_demand_notice(notice_id, data, current_user.id)
    return DemandNoticeResponse.model_validate(notice)


# =============================================================================
# NPA Record Endpoints
# =============================================================================


@router.post(
    "/npa-records",
    response_model=NPARecordResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermissions("NPA_CREATE"))],
)
async def create_npa_record(
    data: NPARecordCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Create an NPA record for a loan account."""
    service = CollectionsService(db)
    record = await service.create_npa_record(data, current_user.id)
    return NPARecordResponse.model_validate(record)


@router.get(
    "/loan-accounts/{loan_account_id}/npa-record",
    response_model=Optional[NPARecordResponse],
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("NPA_READ"))],
)
async def get_npa_record(
    loan_account_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get NPA record for a loan account."""
    service = CollectionsService(db)
    record = await service.get_npa_record(loan_account_id)
    return NPARecordResponse.model_validate(record) if record else None


@router.put(
    "/npa-records/{npa_record_id}",
    response_model=NPARecordResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("NPA_UPDATE"))],
)
async def update_npa_record(
    npa_record_id: UUID,
    data: NPARecordUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Update an NPA record."""
    service = CollectionsService(db)
    record = await service.update_npa_record(npa_record_id, data, current_user.id)
    return NPARecordResponse.model_validate(record)


@router.post(
    "/loan-accounts/{loan_account_id}/upgrade-npa",
    response_model=NPARecordResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("NPA_UPDATE"))],
)
async def upgrade_npa_account(
    loan_account_id: UUID,
    upgrade_date: date = Query(...),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Upgrade an NPA account back to standard."""
    service = CollectionsService(db)
    record = await service.upgrade_npa(loan_account_id, upgrade_date, current_user.id)
    return NPARecordResponse.model_validate(record)


# =============================================================================
# Penal Interest & Waiver Endpoints
# =============================================================================


@router.post(
    "/loan-accounts/{loan_account_id}/calculate-penal",
    response_model=PenalInterestResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("COLLECTIONS_CREATE"))],
)
async def calculate_penal_interest(
    loan_account_id: UUID,
    period_start: date = Query(...),
    period_end: date = Query(...),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Calculate penal interest for a loan account."""
    service = CollectionsService(db)
    penal = await service.calculate_penal_interest(
        loan_account_id, period_start, period_end, current_user.id
    )
    return PenalInterestResponse.model_validate(penal)


@router.post(
    "/penal-waivers",
    response_model=PenalWaiverResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermissions("COLLECTIONS_CREATE"))],
)
async def create_penal_waiver(
    data: PenalWaiverCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Create a penal waiver request."""
    service = CollectionsService(db)
    waiver = await service.create_penal_waiver(data, current_user.id)
    return PenalWaiverResponse.model_validate(waiver)


@router.post(
    "/penal-waivers/{waiver_id}/approve",
    response_model=PenalWaiverResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("COLLECTIONS_APPROVE"))],
)
async def approve_penal_waiver(
    waiver_id: UUID,
    data: PenalWaiverApprove,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Approve a penal waiver."""
    service = CollectionsService(db)
    waiver = await service.approve_penal_waiver(waiver_id, data, current_user.id)
    return PenalWaiverResponse.model_validate(waiver)


# =============================================================================
# OTS Proposal Endpoints
# =============================================================================


@router.post(
    "/ots-proposals",
    response_model=OTSProposalResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermissions("OTS_CREATE"))],
)
async def create_ots_proposal(
    data: OTSProposalCreate = Body(...),
    payment_schedule: list[OTSPaymentScheduleCreate] | None = Body(
        default=None, alias="paymentSchedule"
    ),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Create an OTS proposal."""
    service = CollectionsService(db)
    proposal = await service.create_ots_proposal(
        current_user.organization_id, data, payment_schedule, current_user.id
    )
    return OTSProposalResponse.model_validate(proposal)


@router.put(
    "/ots-proposals/{proposal_id}",
    response_model=OTSProposalResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("OTS_UPDATE"))],
)
async def update_ots_proposal(
    proposal_id: UUID,
    data: OTSProposalUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Update an OTS proposal."""
    service = CollectionsService(db)
    proposal = await service.update_ots_proposal(proposal_id, data, current_user.id)
    return OTSProposalResponse.model_validate(proposal)


@router.post(
    "/ots-proposals/{proposal_id}/approve",
    response_model=OTSProposalResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("OTS_APPROVE"))],
)
async def approve_ots_proposal(
    proposal_id: UUID,
    data: OTSProposalApprove,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Approve an OTS proposal."""
    service = CollectionsService(db)
    proposal = await service.approve_ots_proposal(proposal_id, data, current_user.id)
    return OTSProposalResponse.model_validate(proposal)


@router.post(
    "/ots-proposals/{proposal_id}/accept",
    response_model=OTSProposalResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("OTS_UPDATE"))],
)
async def accept_ots_by_borrower(
    proposal_id: UUID,
    data: OTSBorrowerAccept,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Record borrower acceptance of OTS."""
    service = CollectionsService(db)
    proposal = await service.accept_ots_by_borrower(proposal_id, data, current_user.id)
    return OTSProposalResponse.model_validate(proposal)


@router.post(
    "/ots-proposals/{proposal_id}/record-payment",
    response_model=OTSProposalResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("OTS_UPDATE"))],
)
async def record_ots_payment(
    proposal_id: UUID,
    amount: Decimal = Query(...),
    payment_date: date = Query(...),
    receipt_reference: str = Query(...),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Record payment against OTS proposal."""
    service = CollectionsService(db)
    proposal = await service.record_ots_payment(
        proposal_id, amount, payment_date, receipt_reference, current_user.id
    )
    return OTSProposalResponse.model_validate(proposal)


# =============================================================================
# Loan Restructure Endpoints
# =============================================================================


@router.post(
    "/restructures",
    response_model=LoanRestructureResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermissions("RESTRUCTURE_CREATE"))],
)
async def create_restructure(
    data: LoanRestructureCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Create a loan restructure proposal."""
    service = CollectionsService(db)
    restructure = await service.create_restructure(
        current_user.organization_id, data, current_user.id
    )
    return LoanRestructureResponse.model_validate(restructure)


@router.get(
    "/restructures/{restructure_id}",
    response_model=LoanRestructureResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("COLLECTIONS_READ"))],
)
async def get_restructure(
    restructure_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Fetch a single restructure proposal by ID."""
    service = CollectionsService(db)
    restructure = await service.restructure_repo.get(restructure_id)
    if not restructure:
        raise NotFoundException(detail="Restructure not found", error_code="RESTRUCTURE_NOT_FOUND")
    loan = await service.loan_account_repo.get(restructure.loan_account_id)
    if loan is None or loan.organization_id != current_user.organization_id:
        raise NotFoundException(detail="Restructure not found", error_code="RESTRUCTURE_NOT_FOUND")
    return LoanRestructureResponse.model_validate(restructure)


@router.put(
    "/restructures/{restructure_id}",
    response_model=LoanRestructureResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("RESTRUCTURE_UPDATE"))],
)
async def update_restructure(
    restructure_id: UUID,
    data: LoanRestructureUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Update a restructure proposal."""
    service = CollectionsService(db)
    restructure = await service.update_restructure(restructure_id, data, current_user.id)
    return LoanRestructureResponse.model_validate(restructure)


@router.post(
    "/restructures/{restructure_id}/approve",
    response_model=LoanRestructureResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("RESTRUCTURE_APPROVE"))],
)
async def approve_restructure(
    restructure_id: UUID,
    data: LoanRestructureApprove,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Approve a restructure."""
    service = CollectionsService(db)
    restructure = await service.approve_restructure(
        current_user.organization_id, restructure_id, data, current_user.id
    )
    return LoanRestructureResponse.model_validate(restructure)


@router.post(
    "/restructures/{restructure_id}/reject",
    response_model=LoanRestructureResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("RESTRUCTURE_APPROVE"))],
)
async def reject_restructure(
    restructure_id: UUID,
    data: LoanRestructureReject,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Reject a restructure."""
    service = CollectionsService(db)
    restructure = await service.reject_restructure(
        current_user.organization_id, restructure_id, data, current_user.id
    )
    return LoanRestructureResponse.model_validate(restructure)


@router.post(
    "/restructures/{restructure_id}/implement",
    response_model=LoanRestructureResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("RESTRUCTURE_APPROVE"))],
)
async def implement_restructure(
    restructure_id: UUID,
    data: LoanRestructureImplement,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Implement an approved restructure."""
    service = CollectionsService(db)
    restructure = await service.implement_restructure(restructure_id, data, current_user.id)
    return LoanRestructureResponse.model_validate(restructure)


# =============================================================================
# Legal Case Endpoints
# =============================================================================


@router.post(
    "/legal-cases",
    response_model=LegalCaseResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermissions("LEGAL_CREATE"))],
)
async def create_legal_case(
    data: LegalCaseCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Create a legal case."""
    service = CollectionsService(db)
    case = await service.create_legal_case(data, current_user.id)
    return LegalCaseResponse.model_validate(case)


@router.put(
    "/legal-cases/{case_id}",
    response_model=LegalCaseResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("LEGAL_UPDATE"))],
)
async def update_legal_case(
    case_id: UUID,
    data: LegalCaseUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Update a legal case."""
    service = CollectionsService(db)
    case = await service.update_legal_case(case_id, data, current_user.id)
    return LegalCaseResponse.model_validate(case)


@router.get(
    "/legal-cases/upcoming-hearings",
    response_model=list[LegalCaseResponse],
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("LEGAL_READ"))],
)
async def get_upcoming_hearings(
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get cases with upcoming hearings."""
    service = CollectionsService(db)
    cases = await service.get_upcoming_hearings(days)
    return [LegalCaseResponse.model_validate(c) for c in cases]


@router.post(
    "/legal-cases/{case_id}/hearings",
    response_model=LegalHearingResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermissions("LEGAL_CREATE"))],
)
async def create_hearing(
    case_id: UUID,
    data: LegalHearingCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Create a hearing for a legal case."""
    data.legal_case_id = case_id
    service = CollectionsService(db)
    hearing = await service.create_hearing(data, current_user.id)
    return LegalHearingResponse.model_validate(hearing)


@router.put(
    "/hearings/{hearing_id}",
    response_model=LegalHearingResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("LEGAL_UPDATE"))],
)
async def update_hearing(
    hearing_id: UUID,
    data: LegalHearingUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Update a hearing."""
    service = CollectionsService(db)
    hearing = await service.update_hearing(hearing_id, data, current_user.id)
    return LegalHearingResponse.model_validate(hearing)


# =============================================================================
# Property Auction Endpoints
# =============================================================================


@router.post(
    "/auctions",
    response_model=PropertyAuctionResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermissions("LEGAL_CREATE"))],
)
async def create_auction(
    data: PropertyAuctionCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Create a property auction."""
    service = CollectionsService(db)
    auction = await service.create_auction(data, current_user.id)
    return PropertyAuctionResponse.model_validate(auction)


@router.put(
    "/auctions/{auction_id}",
    response_model=PropertyAuctionResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("LEGAL_UPDATE"))],
)
async def update_auction(
    auction_id: UUID,
    data: PropertyAuctionUpdate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Update an auction."""
    service = CollectionsService(db)
    auction = await service.update_auction(auction_id, data, current_user.id)
    return PropertyAuctionResponse.model_validate(auction)


@router.get(
    "/auctions/upcoming",
    response_model=list[PropertyAuctionResponse],
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("LEGAL_READ"))],
)
async def get_upcoming_auctions(
    days: int = Query(30, ge=1, le=180),
    db: AsyncSession = Depends(get_db_with_tenant),
):
    """Get upcoming auctions."""
    service = CollectionsService(db)
    auctions = await service.get_upcoming_auctions(days)
    return [PropertyAuctionResponse.model_validate(a) for a in auctions]


# =============================================================================
# Write-Off Endpoints
# =============================================================================


@router.post(
    "/write-offs",
    response_model=WriteOffResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermissions("WRITEOFF_CREATE"))],
)
async def create_write_off(
    data: WriteOffCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Create a write-off proposal."""
    service = CollectionsService(db)
    write_off = await service.create_write_off(data, current_user.id)
    return WriteOffResponse.model_validate(write_off)


@router.post(
    "/write-offs/{write_off_id}/approve",
    response_model=WriteOffResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("WRITEOFF_APPROVE"))],
)
async def approve_write_off(
    write_off_id: UUID,
    data: WriteOffApprove,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Approve a write-off."""
    service = CollectionsService(db)
    write_off = await service.approve_write_off(write_off_id, data, current_user.id)
    return WriteOffResponse.model_validate(write_off)


@router.post(
    "/write-offs/{write_off_id}/effect",
    response_model=WriteOffResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("WRITEOFF_APPROVE"))],
)
async def effect_write_off(
    write_off_id: UUID,
    data: WriteOffEffect,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
):
    """Effect an approved write-off."""
    service = CollectionsService(db)
    write_off = await service.effect_write_off(write_off_id, data, current_user.id)
    return WriteOffResponse.model_validate(write_off)
