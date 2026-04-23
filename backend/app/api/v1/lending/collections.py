"""Phase 3: NPA & Collections API endpoints for the lending module."""

from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, RequirePermissions
from app.services.lending.collections_service import CollectionsService
from app.schemas.lending.collections import (
    # Follow-Up
    CollectionFollowUpCreate,
    CollectionFollowUpUpdate,
    CollectionFollowUpExecute,
    CollectionFollowUpResponse,
    # Demand Notice
    DemandNoticeCreate,
    DemandNoticeUpdate,
    DemandNoticeResponse,
    # NPA Record
    NPARecordCreate,
    NPARecordUpdate,
    NPARecordResponse,
    # Penal Interest
    PenalInterestCreate,
    PenalInterestResponse,
    # Penal Waiver
    PenalWaiverCreate,
    PenalWaiverApprove,
    PenalWaiverResponse,
    # OTS
    OTSProposalCreate,
    OTSProposalUpdate,
    OTSProposalApprove,
    OTSBorrowerAccept,
    OTSPaymentScheduleCreate,
    OTSProposalResponse,
    # Restructure
    LoanRestructureCreate,
    LoanRestructureUpdate,
    LoanRestructureApprove,
    LoanRestructureImplement,
    LoanRestructureResponse,
    # Legal Case
    LegalCaseCreate,
    LegalCaseUpdate,
    LegalCaseResponse,
    # Legal Hearing
    LegalHearingCreate,
    LegalHearingUpdate,
    LegalHearingResponse,
    # Auction
    PropertyAuctionCreate,
    PropertyAuctionUpdate,
    PropertyAuctionResponse,
    # Write-Off
    WriteOffCreate,
    WriteOffApprove,
    WriteOffEffect,
    WriteOffResponse,
    # Summary
    NPASummary,
    CollectionActivitySummary,
    RecoverySummary,
)
from app.models.lending.enums import (
    FollowUpStatus,
    NPAStatus,
    OTSStatus,
    RestructureStatus,
    LegalCaseStatus,
    AuctionStatus,
    WriteOffStatus,
)

router = APIRouter()


# =============================================================================
# Summary & Dashboard Endpoints
# =============================================================================

@router.get(
    "/summary/npa",
    response_model=NPASummary,
    dependencies=[Depends(RequirePermissions("collections:read"))],
)
async def get_npa_summary(
    db: AsyncSession = Depends(get_db),
):
    """Get NPA portfolio summary."""
    service = CollectionsService(db)
    return await service.get_npa_summary()


@router.get(
    "/summary/collection",
    response_model=CollectionActivitySummary,
    dependencies=[Depends(RequirePermissions("collections:read"))],
)
async def get_collection_summary(
    db: AsyncSession = Depends(get_db),
):
    """Get collection activity summary."""
    service = CollectionsService(db)
    return await service.get_collection_summary()


@router.get(
    "/summary/recovery",
    response_model=RecoverySummary,
    dependencies=[Depends(RequirePermissions("collections:read"))],
)
async def get_recovery_summary(
    db: AsyncSession = Depends(get_db),
):
    """Get recovery summary."""
    service = CollectionsService(db)
    return await service.get_recovery_summary()


# =============================================================================
# Collection Follow-Up Endpoints
# =============================================================================

@router.post(
    "/follow-ups",
    response_model=CollectionFollowUpResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermissions("collections:create"))],
)
async def create_follow_up(
    data: CollectionFollowUpCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a collection follow-up."""
    service = CollectionsService(db)
    follow_up = await service.create_follow_up(data, current_user.id)
    return CollectionFollowUpResponse.model_validate(follow_up)


@router.get(
    "/follow-ups/scheduled",
    response_model=List[CollectionFollowUpResponse],
    dependencies=[Depends(RequirePermissions("collections:read"))],
)
async def get_scheduled_follow_ups(
    scheduled_date: date = Query(...),
    assigned_to_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get follow-ups scheduled for a specific date."""
    service = CollectionsService(db)
    follow_ups = await service.get_scheduled_follow_ups(scheduled_date, assigned_to_id)
    return [CollectionFollowUpResponse.model_validate(f) for f in follow_ups]


@router.put(
    "/follow-ups/{follow_up_id}",
    response_model=CollectionFollowUpResponse,
    dependencies=[Depends(RequirePermissions("collections:update"))],
)
async def update_follow_up(
    follow_up_id: UUID,
    data: CollectionFollowUpUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a collection follow-up."""
    service = CollectionsService(db)
    follow_up = await service.update_follow_up(follow_up_id, data, current_user.id)
    return CollectionFollowUpResponse.model_validate(follow_up)


@router.post(
    "/follow-ups/{follow_up_id}/execute",
    response_model=CollectionFollowUpResponse,
    dependencies=[Depends(RequirePermissions("collections:update"))],
)
async def execute_follow_up(
    follow_up_id: UUID,
    data: CollectionFollowUpExecute,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Record follow-up execution outcome."""
    service = CollectionsService(db)
    follow_up = await service.execute_follow_up(follow_up_id, data, current_user.id)
    return CollectionFollowUpResponse.model_validate(follow_up)


@router.post(
    "/follow-ups/{follow_up_id}/mark-ptp-broken",
    response_model=CollectionFollowUpResponse,
    dependencies=[Depends(RequirePermissions("collections:update"))],
)
async def mark_ptp_broken(
    follow_up_id: UUID,
    db: AsyncSession = Depends(get_db),
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
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermissions("collections:create"))],
)
async def create_demand_notice(
    data: DemandNoticeCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a demand notice."""
    service = CollectionsService(db)
    notice = await service.create_demand_notice(data, current_user.id)
    return DemandNoticeResponse.model_validate(notice)


@router.get(
    "/loan-accounts/{loan_account_id}/demand-notices",
    response_model=List[DemandNoticeResponse],
    dependencies=[Depends(RequirePermissions("collections:read"))],
)
async def get_demand_notices(
    loan_account_id: UUID,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """Get demand notices for a loan account."""
    service = CollectionsService(db)
    notices = await service.get_demand_notices(loan_account_id, skip, limit)
    return [DemandNoticeResponse.model_validate(n) for n in notices]


@router.put(
    "/demand-notices/{notice_id}",
    response_model=DemandNoticeResponse,
    dependencies=[Depends(RequirePermissions("collections:update"))],
)
async def update_demand_notice(
    notice_id: UUID,
    data: DemandNoticeUpdate,
    db: AsyncSession = Depends(get_db),
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
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermissions("npa:create"))],
)
async def create_npa_record(
    data: NPARecordCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create an NPA record for a loan account."""
    service = CollectionsService(db)
    record = await service.create_npa_record(data, current_user.id)
    return NPARecordResponse.model_validate(record)


@router.get(
    "/loan-accounts/{loan_account_id}/npa-record",
    response_model=Optional[NPARecordResponse],
    dependencies=[Depends(RequirePermissions("npa:read"))],
)
async def get_npa_record(
    loan_account_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get NPA record for a loan account."""
    service = CollectionsService(db)
    record = await service.get_npa_record(loan_account_id)
    return NPARecordResponse.model_validate(record) if record else None


@router.put(
    "/npa-records/{npa_record_id}",
    response_model=NPARecordResponse,
    dependencies=[Depends(RequirePermissions("npa:update"))],
)
async def update_npa_record(
    npa_record_id: UUID,
    data: NPARecordUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update an NPA record."""
    service = CollectionsService(db)
    record = await service.update_npa_record(npa_record_id, data, current_user.id)
    return NPARecordResponse.model_validate(record)


@router.post(
    "/loan-accounts/{loan_account_id}/upgrade-npa",
    response_model=NPARecordResponse,
    dependencies=[Depends(RequirePermissions("npa:update"))],
)
async def upgrade_npa_account(
    loan_account_id: UUID,
    upgrade_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
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
    dependencies=[Depends(RequirePermissions("collections:create"))],
)
async def calculate_penal_interest(
    loan_account_id: UUID,
    period_start: date = Query(...),
    period_end: date = Query(...),
    db: AsyncSession = Depends(get_db),
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
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermissions("collections:create"))],
)
async def create_penal_waiver(
    data: PenalWaiverCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a penal waiver request."""
    service = CollectionsService(db)
    waiver = await service.create_penal_waiver(data, current_user.id)
    return PenalWaiverResponse.model_validate(waiver)


@router.post(
    "/penal-waivers/{waiver_id}/approve",
    response_model=PenalWaiverResponse,
    dependencies=[Depends(RequirePermissions("collections:approve"))],
)
async def approve_penal_waiver(
    waiver_id: UUID,
    data: PenalWaiverApprove,
    db: AsyncSession = Depends(get_db),
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
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermissions("ots:create"))],
)
async def create_ots_proposal(
    data: OTSProposalCreate,
    payment_schedule: Optional[List[OTSPaymentScheduleCreate]] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create an OTS proposal."""
    service = CollectionsService(db)
    proposal = await service.create_ots_proposal(data, payment_schedule, current_user.id)
    return OTSProposalResponse.model_validate(proposal)


@router.put(
    "/ots-proposals/{proposal_id}",
    response_model=OTSProposalResponse,
    dependencies=[Depends(RequirePermissions("ots:update"))],
)
async def update_ots_proposal(
    proposal_id: UUID,
    data: OTSProposalUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update an OTS proposal."""
    service = CollectionsService(db)
    proposal = await service.update_ots_proposal(proposal_id, data, current_user.id)
    return OTSProposalResponse.model_validate(proposal)


@router.post(
    "/ots-proposals/{proposal_id}/approve",
    response_model=OTSProposalResponse,
    dependencies=[Depends(RequirePermissions("ots:approve"))],
)
async def approve_ots_proposal(
    proposal_id: UUID,
    data: OTSProposalApprove,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Approve an OTS proposal."""
    service = CollectionsService(db)
    proposal = await service.approve_ots_proposal(proposal_id, data, current_user.id)
    return OTSProposalResponse.model_validate(proposal)


@router.post(
    "/ots-proposals/{proposal_id}/accept",
    response_model=OTSProposalResponse,
    dependencies=[Depends(RequirePermissions("ots:update"))],
)
async def accept_ots_by_borrower(
    proposal_id: UUID,
    data: OTSBorrowerAccept,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Record borrower acceptance of OTS."""
    service = CollectionsService(db)
    proposal = await service.accept_ots_by_borrower(proposal_id, data, current_user.id)
    return OTSProposalResponse.model_validate(proposal)


@router.post(
    "/ots-proposals/{proposal_id}/record-payment",
    response_model=OTSProposalResponse,
    dependencies=[Depends(RequirePermissions("ots:update"))],
)
async def record_ots_payment(
    proposal_id: UUID,
    amount: Decimal = Query(...),
    payment_date: date = Query(...),
    receipt_reference: str = Query(...),
    db: AsyncSession = Depends(get_db),
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
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermissions("restructure:create"))],
)
async def create_restructure(
    data: LoanRestructureCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a loan restructure proposal."""
    service = CollectionsService(db)
    restructure = await service.create_restructure(data, current_user.id)
    return LoanRestructureResponse.model_validate(restructure)


@router.put(
    "/restructures/{restructure_id}",
    response_model=LoanRestructureResponse,
    dependencies=[Depends(RequirePermissions("restructure:update"))],
)
async def update_restructure(
    restructure_id: UUID,
    data: LoanRestructureUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a restructure proposal."""
    service = CollectionsService(db)
    restructure = await service.update_restructure(restructure_id, data, current_user.id)
    return LoanRestructureResponse.model_validate(restructure)


@router.post(
    "/restructures/{restructure_id}/approve",
    response_model=LoanRestructureResponse,
    dependencies=[Depends(RequirePermissions("restructure:approve"))],
)
async def approve_restructure(
    restructure_id: UUID,
    data: LoanRestructureApprove,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Approve a restructure."""
    service = CollectionsService(db)
    restructure = await service.approve_restructure(restructure_id, data, current_user.id)
    return LoanRestructureResponse.model_validate(restructure)


@router.post(
    "/restructures/{restructure_id}/implement",
    response_model=LoanRestructureResponse,
    dependencies=[Depends(RequirePermissions("restructure:approve"))],
)
async def implement_restructure(
    restructure_id: UUID,
    data: LoanRestructureImplement,
    db: AsyncSession = Depends(get_db),
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
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermissions("legal:create"))],
)
async def create_legal_case(
    data: LegalCaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a legal case."""
    service = CollectionsService(db)
    case = await service.create_legal_case(data, current_user.id)
    return LegalCaseResponse.model_validate(case)


@router.put(
    "/legal-cases/{case_id}",
    response_model=LegalCaseResponse,
    dependencies=[Depends(RequirePermissions("legal:update"))],
)
async def update_legal_case(
    case_id: UUID,
    data: LegalCaseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a legal case."""
    service = CollectionsService(db)
    case = await service.update_legal_case(case_id, data, current_user.id)
    return LegalCaseResponse.model_validate(case)


@router.get(
    "/legal-cases/upcoming-hearings",
    response_model=List[LegalCaseResponse],
    dependencies=[Depends(RequirePermissions("legal:read"))],
)
async def get_upcoming_hearings(
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    """Get cases with upcoming hearings."""
    service = CollectionsService(db)
    cases = await service.get_upcoming_hearings(days)
    return [LegalCaseResponse.model_validate(c) for c in cases]


@router.post(
    "/legal-cases/{case_id}/hearings",
    response_model=LegalHearingResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermissions("legal:create"))],
)
async def create_hearing(
    case_id: UUID,
    data: LegalHearingCreate,
    db: AsyncSession = Depends(get_db),
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
    dependencies=[Depends(RequirePermissions("legal:update"))],
)
async def update_hearing(
    hearing_id: UUID,
    data: LegalHearingUpdate,
    db: AsyncSession = Depends(get_db),
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
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermissions("legal:create"))],
)
async def create_auction(
    data: PropertyAuctionCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a property auction."""
    service = CollectionsService(db)
    auction = await service.create_auction(data, current_user.id)
    return PropertyAuctionResponse.model_validate(auction)


@router.put(
    "/auctions/{auction_id}",
    response_model=PropertyAuctionResponse,
    dependencies=[Depends(RequirePermissions("legal:update"))],
)
async def update_auction(
    auction_id: UUID,
    data: PropertyAuctionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update an auction."""
    service = CollectionsService(db)
    auction = await service.update_auction(auction_id, data, current_user.id)
    return PropertyAuctionResponse.model_validate(auction)


@router.get(
    "/auctions/upcoming",
    response_model=List[PropertyAuctionResponse],
    dependencies=[Depends(RequirePermissions("legal:read"))],
)
async def get_upcoming_auctions(
    days: int = Query(30, ge=1, le=180),
    db: AsyncSession = Depends(get_db),
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
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermissions("writeoff:create"))],
)
async def create_write_off(
    data: WriteOffCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a write-off proposal."""
    service = CollectionsService(db)
    write_off = await service.create_write_off(data, current_user.id)
    return WriteOffResponse.model_validate(write_off)


@router.post(
    "/write-offs/{write_off_id}/approve",
    response_model=WriteOffResponse,
    dependencies=[Depends(RequirePermissions("writeoff:approve"))],
)
async def approve_write_off(
    write_off_id: UUID,
    data: WriteOffApprove,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Approve a write-off."""
    service = CollectionsService(db)
    write_off = await service.approve_write_off(write_off_id, data, current_user.id)
    return WriteOffResponse.model_validate(write_off)


@router.post(
    "/write-offs/{write_off_id}/effect",
    response_model=WriteOffResponse,
    dependencies=[Depends(RequirePermissions("writeoff:approve"))],
)
async def effect_write_off(
    write_off_id: UUID,
    data: WriteOffEffect,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Effect an approved write-off."""
    service = CollectionsService(db)
    write_off = await service.effect_write_off(write_off_id, data, current_user.id)
    return WriteOffResponse.model_validate(write_off)
