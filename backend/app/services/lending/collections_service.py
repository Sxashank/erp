"""Phase 3: NPA & Collections service for the lending module."""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.lending.collections_repo import (
    CollectionFollowUpRepository,
    DemandNoticeRepository,
    NPARecordRepository,
    PenalInterestRepository,
    PenalWaiverRepository,
    OTSProposalRepository,
    OTSPaymentScheduleRepository,
    LoanRestructureRepository,
    LegalCaseRepository,
    LegalHearingRepository,
    PropertyAuctionRepository,
    WriteOffRecordRepository,
)
from app.repositories.lending.loan_account_repo import LoanAccountRepository
from app.models.lending.collections import (
    CollectionFollowUp,
    DemandNotice,
    NPARecord,
    PenalInterest,
    PenalWaiver,
    OTSProposal,
    OTSPaymentSchedule,
    LoanRestructure,
    LegalCase,
    LegalHearing,
    PropertyAuction,
    WriteOffRecord,
)
from app.models.lending.enums import (
    AssetClassification,
    AuctionStatus,
    CollectionStage,
    FollowUpOutcome,
    FollowUpStatus,
    LegalCaseStatus,
    NPAStatus,
    OTSStatus,
    RestructureStatus,
    WriteOffStatus,
)
from app.schemas.lending.collections import (
    CollectionFollowUpCreate,
    CollectionFollowUpUpdate,
    CollectionFollowUpExecute,
    DemandNoticeCreate,
    DemandNoticeUpdate,
    NPARecordCreate,
    NPARecordUpdate,
    PenalInterestCreate,
    PenalWaiverCreate,
    PenalWaiverApprove,
    OTSProposalCreate,
    OTSProposalUpdate,
    OTSProposalApprove,
    OTSBorrowerAccept,
    OTSPaymentScheduleCreate,
    LoanRestructureCreate,
    LoanRestructureUpdate,
    LoanRestructureApprove,
    LoanRestructureImplement,
    LegalCaseCreate,
    LegalCaseUpdate,
    LegalHearingCreate,
    LegalHearingUpdate,
    PropertyAuctionCreate,
    PropertyAuctionUpdate,
    WriteOffCreate,
    WriteOffApprove,
    WriteOffEffect,
    NPASummary,
    CollectionActivitySummary,
    RecoverySummary,
)
from app.core.exceptions import BadRequestException, NotFoundException


class CollectionsService:
    """Service for NPA & Collections operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.follow_up_repo = CollectionFollowUpRepository(session)
        self.demand_notice_repo = DemandNoticeRepository(session)
        self.npa_record_repo = NPARecordRepository(session)
        self.penal_interest_repo = PenalInterestRepository(session)
        self.penal_waiver_repo = PenalWaiverRepository(session)
        self.ots_proposal_repo = OTSProposalRepository(session)
        self.ots_schedule_repo = OTSPaymentScheduleRepository(session)
        self.restructure_repo = LoanRestructureRepository(session)
        self.legal_case_repo = LegalCaseRepository(session)
        self.legal_hearing_repo = LegalHearingRepository(session)
        self.auction_repo = PropertyAuctionRepository(session)
        self.write_off_repo = WriteOffRecordRepository(session)
        self.loan_account_repo = LoanAccountRepository(session)

    # =========================================================================
    # Collection Follow-Up Operations
    # =========================================================================

    async def create_follow_up(
        self,
        data: CollectionFollowUpCreate,
        created_by: Optional[UUID] = None,
    ) -> CollectionFollowUp:
        """Create a collection follow-up."""
        follow_up = CollectionFollowUp(
            **data.model_dump(),
            status=FollowUpStatus.SCHEDULED,
            created_by=created_by,
        )
        return await self.follow_up_repo.create(follow_up)

    async def update_follow_up(
        self,
        follow_up_id: UUID,
        data: CollectionFollowUpUpdate,
        updated_by: Optional[UUID] = None,
    ) -> CollectionFollowUp:
        """Update a collection follow-up."""
        follow_up = await self.follow_up_repo.get(follow_up_id)
        if not follow_up:
            raise NotFoundException("Follow-up not found")

        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by"] = updated_by

        return await self.follow_up_repo.update(follow_up, update_data)

    async def execute_follow_up(
        self,
        follow_up_id: UUID,
        data: CollectionFollowUpExecute,
        updated_by: Optional[UUID] = None,
    ) -> CollectionFollowUp:
        """Record follow-up execution outcome."""
        follow_up = await self.follow_up_repo.get(follow_up_id)
        if not follow_up:
            raise NotFoundException("Follow-up not found")

        if follow_up.status != FollowUpStatus.SCHEDULED:
            raise BadRequestException("Follow-up is not in scheduled status")

        update_data = data.model_dump(exclude_unset=True)
        update_data["status"] = FollowUpStatus.COMPLETED
        update_data["executed_date"] = data.executed_date or datetime.now()
        update_data["updated_by"] = updated_by

        return await self.follow_up_repo.update(follow_up, update_data)

    async def get_scheduled_follow_ups(
        self,
        scheduled_date: date,
        assigned_to_id: Optional[UUID] = None,
    ) -> List[CollectionFollowUp]:
        """Get follow-ups scheduled for a date."""
        return await self.follow_up_repo.get_scheduled_for_date(
            scheduled_date, assigned_to_id
        )

    async def mark_ptp_broken(
        self,
        follow_up_id: UUID,
        updated_by: Optional[UUID] = None,
    ) -> CollectionFollowUp:
        """Mark a Promise to Pay as broken."""
        follow_up = await self.follow_up_repo.get(follow_up_id)
        if not follow_up:
            raise NotFoundException("Follow-up not found")

        if not follow_up.ptp_date:
            raise BadRequestException("No PTP date set on this follow-up")

        return await self.follow_up_repo.update(
            follow_up,
            {"ptp_broken": True, "updated_by": updated_by},
        )

    # =========================================================================
    # Demand Notice Operations
    # =========================================================================

    async def create_demand_notice(
        self,
        data: DemandNoticeCreate,
        created_by: Optional[UUID] = None,
    ) -> DemandNotice:
        """Create a demand notice."""
        notice_number = await self.demand_notice_repo.generate_notice_number()

        notice = DemandNotice(
            **data.model_dump(),
            notice_number=notice_number,
            created_by=created_by,
        )
        return await self.demand_notice_repo.create(notice)

    async def update_demand_notice(
        self,
        notice_id: UUID,
        data: DemandNoticeUpdate,
        updated_by: Optional[UUID] = None,
    ) -> DemandNotice:
        """Update a demand notice."""
        notice = await self.demand_notice_repo.get(notice_id)
        if not notice:
            raise NotFoundException("Demand notice not found")

        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by"] = updated_by

        return await self.demand_notice_repo.update(notice, update_data)

    async def get_demand_notices(
        self,
        loan_account_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[DemandNotice]:
        """Get demand notices for a loan account."""
        return await self.demand_notice_repo.get_by_loan_account(
            loan_account_id, skip, limit
        )

    # =========================================================================
    # NPA Record Operations
    # =========================================================================

    async def create_npa_record(
        self,
        data: NPARecordCreate,
        created_by: Optional[UUID] = None,
    ) -> NPARecord:
        """Create an NPA record."""
        existing = await self.npa_record_repo.get_by_loan_account(data.loan_account_id)
        if existing:
            raise BadRequestException("NPA record already exists for this loan account")

        npa_record = NPARecord(
            **data.model_dump(),
            created_by=created_by,
        )
        return await self.npa_record_repo.create(npa_record)

    async def update_npa_record(
        self,
        npa_record_id: UUID,
        data: NPARecordUpdate,
        updated_by: Optional[UUID] = None,
    ) -> NPARecord:
        """Update an NPA record."""
        npa_record = await self.npa_record_repo.get(npa_record_id)
        if not npa_record:
            raise NotFoundException("NPA record not found")

        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by"] = updated_by

        return await self.npa_record_repo.update(npa_record, update_data)

    async def get_npa_record(
        self,
        loan_account_id: UUID,
    ) -> Optional[NPARecord]:
        """Get NPA record for a loan account."""
        return await self.npa_record_repo.get_by_loan_account(loan_account_id)

    async def upgrade_npa(
        self,
        loan_account_id: UUID,
        upgrade_date: date,
        updated_by: Optional[UUID] = None,
    ) -> NPARecord:
        """Upgrade an NPA account back to standard."""
        npa_record = await self.npa_record_repo.get_by_loan_account(loan_account_id)
        if not npa_record:
            raise NotFoundException("NPA record not found")

        if npa_record.npa_status != NPAStatus.NPA:
            raise BadRequestException("Account is not in NPA status")

        update_data = {
            "npa_status": NPAStatus.UPGRADED,
            "upgrade_date": upgrade_date,
            "updated_by": updated_by,
        }

        return await self.npa_record_repo.update(npa_record, update_data)

    # =========================================================================
    # Penal Interest Operations
    # =========================================================================

    async def calculate_penal_interest(
        self,
        loan_account_id: UUID,
        period_start: date,
        period_end: date,
        created_by: Optional[UUID] = None,
    ) -> PenalInterest:
        """Calculate penal interest for a loan account."""
        loan_account = await self.loan_account_repo.get(loan_account_id)
        if not loan_account:
            raise NotFoundException("Loan account not found")

        overdue_principal = loan_account.principal_overdue
        overdue_interest = loan_account.interest_overdue
        overdue_total = overdue_principal + overdue_interest

        if overdue_total <= 0:
            raise BadRequestException("No overdue amount to calculate penal interest")

        penal_rate = loan_account.penal_interest_rate
        days_overdue = (period_end - period_start).days + 1

        # Calculate penal interest
        calculated_amount = (
            overdue_total * penal_rate / Decimal("100") * days_overdue / Decimal("365")
        )

        penal_data = PenalInterestCreate(
            loan_account_id=loan_account_id,
            period_start=period_start,
            period_end=period_end,
            overdue_principal=overdue_principal,
            overdue_interest=overdue_interest,
            overdue_total=overdue_total,
            penal_rate=penal_rate,
            days_overdue=days_overdue,
            calculated_amount=calculated_amount,
            applied_amount=calculated_amount,
        )

        penal_interest = PenalInterest(
            **penal_data.model_dump(),
            created_by=created_by,
        )
        return await self.penal_interest_repo.create(penal_interest)

    async def create_penal_waiver(
        self,
        data: PenalWaiverCreate,
        created_by: Optional[UUID] = None,
    ) -> PenalWaiver:
        """Create a penal waiver request."""
        waiver_reference = await self.penal_waiver_repo.generate_waiver_reference()

        balance_after_waiver = data.total_penal_accrued - data.waiver_amount

        waiver = PenalWaiver(
            **data.model_dump(),
            waiver_reference=waiver_reference,
            balance_after_waiver=balance_after_waiver,
            created_by=created_by,
        )
        return await self.penal_waiver_repo.create(waiver)

    async def approve_penal_waiver(
        self,
        waiver_id: UUID,
        data: PenalWaiverApprove,
        updated_by: Optional[UUID] = None,
    ) -> PenalWaiver:
        """Approve a penal waiver."""
        waiver = await self.penal_waiver_repo.get(waiver_id)
        if not waiver:
            raise NotFoundException("Penal waiver not found")

        if waiver.is_approved:
            raise BadRequestException("Waiver is already approved")

        update_data = data.model_dump()
        update_data["is_approved"] = True
        update_data["approval_date"] = date.today()
        update_data["updated_by"] = updated_by

        return await self.penal_waiver_repo.update(waiver, update_data)

    # =========================================================================
    # OTS Proposal Operations
    # =========================================================================

    async def create_ots_proposal(
        self,
        data: OTSProposalCreate,
        payment_schedule: Optional[List[OTSPaymentScheduleCreate]] = None,
        created_by: Optional[UUID] = None,
    ) -> OTSProposal:
        """Create an OTS proposal."""
        ots_reference = await self.ots_proposal_repo.generate_ots_reference()

        # Calculate haircut
        haircut_amount = data.total_outstanding - data.ots_amount
        haircut_percent = (haircut_amount / data.total_outstanding * 100) if data.total_outstanding > 0 else Decimal("0")

        proposal = OTSProposal(
            **data.model_dump(),
            ots_reference=ots_reference,
            haircut_amount=haircut_amount,
            haircut_percent=haircut_percent,
            balance_pending=data.ots_amount,
            status=OTSStatus.DRAFT,
            created_by=created_by,
        )
        proposal = await self.ots_proposal_repo.create(proposal)

        # Create payment schedule if provided
        if payment_schedule:
            for schedule_item in payment_schedule:
                schedule = OTSPaymentSchedule(
                    ots_proposal_id=proposal.id,
                    **schedule_item.model_dump(),
                    created_by=created_by,
                )
                await self.ots_schedule_repo.create(schedule)

        return proposal

    async def update_ots_proposal(
        self,
        proposal_id: UUID,
        data: OTSProposalUpdate,
        updated_by: Optional[UUID] = None,
    ) -> OTSProposal:
        """Update an OTS proposal."""
        proposal = await self.ots_proposal_repo.get(proposal_id)
        if not proposal:
            raise NotFoundException("OTS proposal not found")

        if proposal.status not in [OTSStatus.DRAFT, OTSStatus.PROPOSED, OTSStatus.NEGOTIATION]:
            raise BadRequestException("Cannot update proposal in current status")

        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by"] = updated_by

        return await self.ots_proposal_repo.update(proposal, update_data)

    async def approve_ots_proposal(
        self,
        proposal_id: UUID,
        data: OTSProposalApprove,
        updated_by: Optional[UUID] = None,
    ) -> OTSProposal:
        """Approve an OTS proposal."""
        proposal = await self.ots_proposal_repo.get(proposal_id)
        if not proposal:
            raise NotFoundException("OTS proposal not found")

        if proposal.status != OTSStatus.PENDING_APPROVAL:
            raise BadRequestException("Proposal is not pending approval")

        update_data = data.model_dump()
        update_data["status"] = OTSStatus.APPROVED
        update_data["approval_date"] = date.today()
        update_data["updated_by"] = updated_by

        return await self.ots_proposal_repo.update(proposal, update_data)

    async def accept_ots_by_borrower(
        self,
        proposal_id: UUID,
        data: OTSBorrowerAccept,
        updated_by: Optional[UUID] = None,
    ) -> OTSProposal:
        """Record borrower acceptance of OTS."""
        proposal = await self.ots_proposal_repo.get(proposal_id)
        if not proposal:
            raise NotFoundException("OTS proposal not found")

        if proposal.status != OTSStatus.APPROVED:
            raise BadRequestException("Proposal is not in approved status")

        update_data = data.model_dump()
        update_data["status"] = OTSStatus.ACCEPTED
        update_data["updated_by"] = updated_by

        return await self.ots_proposal_repo.update(proposal, update_data)

    async def record_ots_payment(
        self,
        proposal_id: UUID,
        amount: Decimal,
        payment_date: date,
        receipt_reference: str,
        updated_by: Optional[UUID] = None,
    ) -> OTSProposal:
        """Record payment against OTS proposal."""
        proposal = await self.ots_proposal_repo.get(proposal_id)
        if not proposal:
            raise NotFoundException("OTS proposal not found")

        if proposal.status not in [OTSStatus.ACCEPTED, OTSStatus.PAYMENT_PENDING, OTSStatus.PARTIALLY_PAID]:
            raise BadRequestException("Proposal is not in payment status")

        new_total_received = proposal.total_received + amount
        new_balance = proposal.ots_amount - new_total_received

        if new_balance <= 0:
            new_status = OTSStatus.COMPLETED
            completion_date = payment_date
        else:
            new_status = OTSStatus.PARTIALLY_PAID
            completion_date = None

        update_data = {
            "total_received": new_total_received,
            "balance_pending": max(new_balance, Decimal("0")),
            "status": new_status,
            "completion_date": completion_date,
            "updated_by": updated_by,
        }

        return await self.ots_proposal_repo.update(proposal, update_data)

    # =========================================================================
    # Loan Restructure Operations
    # =========================================================================

    async def create_restructure(
        self,
        data: LoanRestructureCreate,
        created_by: Optional[UUID] = None,
    ) -> LoanRestructure:
        """Create a loan restructure proposal."""
        restructure_reference = await self.restructure_repo.generate_restructure_reference()

        restructure = LoanRestructure(
            **data.model_dump(),
            restructure_reference=restructure_reference,
            status=RestructureStatus.DRAFT,
            created_by=created_by,
        )
        return await self.restructure_repo.create(restructure)

    async def update_restructure(
        self,
        restructure_id: UUID,
        data: LoanRestructureUpdate,
        updated_by: Optional[UUID] = None,
    ) -> LoanRestructure:
        """Update a restructure proposal."""
        restructure = await self.restructure_repo.get(restructure_id)
        if not restructure:
            raise NotFoundException("Restructure not found")

        if restructure.status not in [RestructureStatus.DRAFT, RestructureStatus.PROPOSED]:
            raise BadRequestException("Cannot update restructure in current status")

        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by"] = updated_by

        return await self.restructure_repo.update(restructure, update_data)

    async def approve_restructure(
        self,
        restructure_id: UUID,
        data: LoanRestructureApprove,
        updated_by: Optional[UUID] = None,
    ) -> LoanRestructure:
        """Approve a restructure."""
        restructure = await self.restructure_repo.get(restructure_id)
        if not restructure:
            raise NotFoundException("Restructure not found")

        if restructure.status != RestructureStatus.PENDING_APPROVAL:
            raise BadRequestException("Restructure is not pending approval")

        update_data = data.model_dump()
        update_data["status"] = RestructureStatus.APPROVED
        update_data["approval_date"] = date.today()
        update_data["updated_by"] = updated_by

        return await self.restructure_repo.update(restructure, update_data)

    async def implement_restructure(
        self,
        restructure_id: UUID,
        data: LoanRestructureImplement,
        updated_by: Optional[UUID] = None,
    ) -> LoanRestructure:
        """Implement an approved restructure."""
        restructure = await self.restructure_repo.get(restructure_id)
        if not restructure:
            raise NotFoundException("Restructure not found")

        if restructure.status != RestructureStatus.APPROVED:
            raise BadRequestException("Restructure is not approved")

        update_data = {
            "status": RestructureStatus.IMPLEMENTED,
            "implementation_date": data.implementation_date,
            "new_schedule_generated": data.generate_new_schedule,
            "updated_by": updated_by,
        }

        # Update loan account terms
        loan_account = await self.loan_account_repo.get(restructure.loan_account_id)
        if loan_account:
            loan_update = {
                "current_interest_rate": restructure.post_interest_rate,
                "tenure_months": restructure.post_tenure_months,
                "maturity_date": restructure.post_maturity_date,
                "current_emi_amount": restructure.post_emi_amount,
            }
            if restructure.moratorium_months > 0:
                loan_update["moratorium_months"] = restructure.moratorium_months
                loan_update["moratorium_end_date"] = restructure.moratorium_end_date

            await self.loan_account_repo.update(loan_account, loan_update)

        return await self.restructure_repo.update(restructure, update_data)

    # =========================================================================
    # Legal Case Operations
    # =========================================================================

    async def create_legal_case(
        self,
        data: LegalCaseCreate,
        created_by: Optional[UUID] = None,
    ) -> LegalCase:
        """Create a legal case."""
        case_reference = await self.legal_case_repo.generate_case_reference()

        legal_case = LegalCase(
            **data.model_dump(),
            case_reference=case_reference,
            status=LegalCaseStatus.DRAFT,
            created_by=created_by,
        )
        return await self.legal_case_repo.create(legal_case)

    async def update_legal_case(
        self,
        case_id: UUID,
        data: LegalCaseUpdate,
        updated_by: Optional[UUID] = None,
    ) -> LegalCase:
        """Update a legal case."""
        legal_case = await self.legal_case_repo.get(case_id)
        if not legal_case:
            raise NotFoundException("Legal case not found")

        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by"] = updated_by

        return await self.legal_case_repo.update(legal_case, update_data)

    async def create_hearing(
        self,
        data: LegalHearingCreate,
        created_by: Optional[UUID] = None,
    ) -> LegalHearing:
        """Create a hearing for a legal case."""
        hearing = LegalHearing(
            **data.model_dump(),
            created_by=created_by,
        )
        hearing = await self.legal_hearing_repo.create(hearing)

        # Update case with next hearing date
        if data.next_hearing_date:
            legal_case = await self.legal_case_repo.get(data.legal_case_id)
            if legal_case:
                await self.legal_case_repo.update(
                    legal_case,
                    {"next_hearing_date": data.next_hearing_date},
                )

        return hearing

    async def update_hearing(
        self,
        hearing_id: UUID,
        data: LegalHearingUpdate,
        updated_by: Optional[UUID] = None,
    ) -> LegalHearing:
        """Update a hearing."""
        hearing = await self.legal_hearing_repo.get(hearing_id)
        if not hearing:
            raise NotFoundException("Hearing not found")

        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by"] = updated_by

        hearing = await self.legal_hearing_repo.update(hearing, update_data)

        # Update case with next hearing date
        if data.next_hearing_date:
            legal_case = await self.legal_case_repo.get(hearing.legal_case_id)
            if legal_case:
                await self.legal_case_repo.update(
                    legal_case,
                    {"next_hearing_date": data.next_hearing_date},
                )

        return hearing

    async def get_upcoming_hearings(
        self,
        days: int = 7,
    ) -> List[LegalCase]:
        """Get cases with upcoming hearings."""
        return await self.legal_case_repo.get_upcoming_hearings(days)

    # =========================================================================
    # Property Auction Operations
    # =========================================================================

    async def create_auction(
        self,
        data: PropertyAuctionCreate,
        created_by: Optional[UUID] = None,
    ) -> PropertyAuction:
        """Create a property auction."""
        auction_reference = await self.auction_repo.generate_auction_reference()

        auction = PropertyAuction(
            **data.model_dump(),
            auction_reference=auction_reference,
            status=AuctionStatus.SCHEDULED,
            created_by=created_by,
        )
        return await self.auction_repo.create(auction)

    async def update_auction(
        self,
        auction_id: UUID,
        data: PropertyAuctionUpdate,
        updated_by: Optional[UUID] = None,
    ) -> PropertyAuction:
        """Update an auction."""
        auction = await self.auction_repo.get(auction_id)
        if not auction:
            raise NotFoundException("Auction not found")

        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by"] = updated_by

        return await self.auction_repo.update(auction, update_data)

    async def get_upcoming_auctions(
        self,
        days: int = 30,
    ) -> List[PropertyAuction]:
        """Get upcoming auctions."""
        return await self.auction_repo.get_upcoming_auctions(days)

    # =========================================================================
    # Write-Off Operations
    # =========================================================================

    async def create_write_off(
        self,
        data: WriteOffCreate,
        created_by: Optional[UUID] = None,
    ) -> WriteOffRecord:
        """Create a write-off proposal."""
        write_off_reference = await self.write_off_repo.generate_write_off_reference()

        write_off = WriteOffRecord(
            **data.model_dump(),
            write_off_reference=write_off_reference,
            status=WriteOffStatus.PROPOSED,
            created_by=created_by,
        )
        return await self.write_off_repo.create(write_off)

    async def approve_write_off(
        self,
        write_off_id: UUID,
        data: WriteOffApprove,
        updated_by: Optional[UUID] = None,
    ) -> WriteOffRecord:
        """Approve a write-off."""
        write_off = await self.write_off_repo.get(write_off_id)
        if not write_off:
            raise NotFoundException("Write-off not found")

        if write_off.status != WriteOffStatus.PENDING_APPROVAL:
            raise BadRequestException("Write-off is not pending approval")

        update_data = data.model_dump()
        update_data["status"] = WriteOffStatus.APPROVED
        update_data["approval_date"] = date.today()
        update_data["updated_by"] = updated_by

        return await self.write_off_repo.update(write_off, update_data)

    async def effect_write_off(
        self,
        write_off_id: UUID,
        data: WriteOffEffect,
        updated_by: Optional[UUID] = None,
    ) -> WriteOffRecord:
        """Effect an approved write-off."""
        write_off = await self.write_off_repo.get(write_off_id)
        if not write_off:
            raise NotFoundException("Write-off not found")

        if write_off.status != WriteOffStatus.APPROVED:
            raise BadRequestException("Write-off is not approved")

        update_data = {
            "status": WriteOffStatus.EFFECTED,
            "effective_date": data.effective_date,
            "updated_by": updated_by,
        }

        # Update loan account
        loan_account = await self.loan_account_repo.get(write_off.loan_account_id)
        if loan_account:
            loan_update = {
                "principal_written_off": loan_account.principal_written_off + write_off.principal_written_off,
                "interest_written_off": loan_account.interest_written_off + write_off.interest_written_off,
                "write_off_date": data.effective_date,
            }
            await self.loan_account_repo.update(loan_account, loan_update)

        return await self.write_off_repo.update(write_off, update_data)

    # =========================================================================
    # Summary & Dashboard Operations
    # =========================================================================

    async def get_npa_summary(self) -> NPASummary:
        """Get NPA portfolio summary."""
        npa_data = await self.npa_record_repo.get_npa_summary()

        summary = NPASummary()

        for classification, data in npa_data.items():
            count = data.get("count", 0)
            amount = data.get("amount", Decimal("0")) or Decimal("0")
            provision = data.get("provision", Decimal("0")) or Decimal("0")

            summary.total_npa_accounts += count
            summary.total_npa_amount += amount
            summary.total_provision_held += provision

            if classification == AssetClassification.SMA_0:
                summary.sma_0_count = count
                summary.sma_0_amount = amount
            elif classification == AssetClassification.SMA_1:
                summary.sma_1_count = count
                summary.sma_1_amount = amount
            elif classification == AssetClassification.SMA_2:
                summary.sma_2_count = count
                summary.sma_2_amount = amount
            elif classification == AssetClassification.SUBSTANDARD:
                summary.substandard_count = count
                summary.substandard_amount = amount
            elif classification == AssetClassification.DOUBTFUL_1:
                summary.doubtful_1_count = count
                summary.doubtful_1_amount = amount
            elif classification == AssetClassification.DOUBTFUL_2:
                summary.doubtful_2_count = count
                summary.doubtful_2_amount = amount
            elif classification == AssetClassification.DOUBTFUL_3:
                summary.doubtful_3_count = count
                summary.doubtful_3_amount = amount
            elif classification == AssetClassification.LOSS:
                summary.loss_count = count
                summary.loss_amount = amount

        if summary.total_npa_amount > 0:
            summary.provision_coverage_ratio = (
                summary.total_provision_held / summary.total_npa_amount * 100
            )

        return summary

    async def get_collection_summary(self) -> CollectionActivitySummary:
        """Get collection activity summary."""
        today = date.today()

        # Get pending follow-ups
        scheduled = await self.follow_up_repo.get_scheduled_for_date(today)

        summary = CollectionActivitySummary(
            pending_follow_ups=len(scheduled),
        )

        return summary

    async def get_recovery_summary(self) -> RecoverySummary:
        """Get recovery summary."""
        # Get OTS stats
        ots_approved = await self.ots_proposal_repo.get_by_status(OTSStatus.APPROVED)
        ots_completed = await self.ots_proposal_repo.get_by_status(OTSStatus.COMPLETED)

        # Get restructure stats
        restructures_approved = await self.restructure_repo.get_by_status(RestructureStatus.APPROVED)
        restructures_implemented = await self.restructure_repo.get_by_status(RestructureStatus.IMPLEMENTED)

        # Get legal case stats
        legal_pending = await self.legal_case_repo.get_by_status(LegalCaseStatus.PENDING)
        legal_decree = await self.legal_case_repo.get_by_status(LegalCaseStatus.DECREE_OBTAINED)

        # Get write-off stats
        write_off_data = await self.write_off_repo.get_total_written_off()

        # Calculate OTS settlement amount
        ots_settlement_amount = sum(
            p.ots_amount for p in ots_completed
        ) if ots_completed else Decimal("0")

        # Calculate legal recovery
        recovery_through_legal = sum(
            c.recovery_through_case for c in legal_decree
        ) if legal_decree else Decimal("0")

        return RecoverySummary(
            approved_ots=len(ots_approved),
            completed_ots=len(ots_completed),
            ots_settlement_amount=ots_settlement_amount,
            approved_restructures=len(restructures_approved),
            implemented_restructures=len(restructures_implemented),
            pending_cases=len(legal_pending),
            decree_obtained=len(legal_decree),
            recovery_through_legal=recovery_through_legal,
            total_written_off=write_off_data.get("total_written_off", Decimal("0")),
            recovery_from_written_off=write_off_data.get("recovery_after_write_off", Decimal("0")),
        )

    # =========================================================================
    # Batch Operations
    # =========================================================================

    async def identify_npa_accounts(
        self,
        as_of_date: date,
    ) -> List[Tuple[UUID, AssetClassification]]:
        """Identify accounts that should be classified as NPA based on DPD."""
        accounts = await self.loan_account_repo.get_accounts_for_npa_check()

        npa_accounts = []
        for account in accounts:
            dpd = account.days_past_due
            current_class = account.asset_classification

            # Determine new classification based on DPD
            if dpd >= 90 and current_class not in [
                AssetClassification.SUBSTANDARD,
                AssetClassification.DOUBTFUL_1,
                AssetClassification.DOUBTFUL_2,
                AssetClassification.DOUBTFUL_3,
                AssetClassification.LOSS,
            ]:
                npa_accounts.append((account.id, AssetClassification.SUBSTANDARD))

        return npa_accounts

    async def auto_create_follow_ups(
        self,
        as_of_date: date,
    ) -> List[CollectionFollowUp]:
        """Auto-create follow-ups for overdue accounts based on DPD."""
        # This would be called by a scheduled job
        created_follow_ups = []

        # Get accounts by DPD buckets and create appropriate follow-ups
        # Logic would vary based on organization's collection policy

        return created_follow_ups
