"""Phase 3: NPA & Collections service for the lending module."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.lending.collections import (
    CollectionFollowUp,
    DemandNotice,
    LegalCase,
    LegalHearing,
    LoanRestructure,
    NPARecord,
    OTSPaymentSchedule,
    OTSProposal,
    PenalInterest,
    PenalWaiver,
    PropertyAuction,
    WriteOffRecord,
)
from app.models.lending.enums import (
    AssetClassification,
    AuctionStatus,
    FollowUpStatus,
    LegalCaseStatus,
    NPAStatus,
    OTSStatus,
    RestructureStatus,
    WriteOffStatus,
)
from app.models.lending.loan_account import LoanAccount
from app.models.lending.masters import LendingOption
from app.repositories.lending.collections_repo import (
    CollectionFollowUpRepository,
    DemandNoticeRepository,
    LegalCaseRepository,
    LegalHearingRepository,
    LoanRestructureRepository,
    NPARecordRepository,
    OTSPaymentScheduleRepository,
    OTSProposalRepository,
    PenalInterestRepository,
    PenalWaiverRepository,
    PropertyAuctionRepository,
    WriteOffRecordRepository,
)
from app.repositories.lending.loan_account_repo import LoanAccountRepository
from app.schemas.lending.collections import (
    CollectionActivitySummary,
    CollectionFollowUpCreate,
    CollectionFollowUpExecute,
    CollectionFollowUpUpdate,
    DemandNoticeCreate,
    DemandNoticeUpdate,
    LegalCaseCreate,
    LegalCaseUpdate,
    LegalHearingCreate,
    LegalHearingUpdate,
    LoanRestructureApprove,
    LoanRestructureCreate,
    LoanRestructureImplement,
    LoanRestructureReject,
    LoanRestructureUpdate,
    NPARecordCreate,
    NPARecordUpdate,
    NPASummary,
    OTSBorrowerAccept,
    OTSPaymentScheduleCreate,
    OTSProposalApprove,
    OTSProposalCreate,
    OTSProposalUpdate,
    PenalInterestCreate,
    PenalWaiverApprove,
    PenalWaiverCreate,
    PropertyAuctionCreate,
    PropertyAuctionUpdate,
    RecoverySummary,
    WriteOffApprove,
    WriteOffCreate,
    WriteOffEffect,
)
from app.services.audit import record_financial_action


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

    async def _validate_lending_option(
        self, organization_id: UUID, option_group: str, code: str | None
    ) -> str | None:
        if code is None:
            return None
        normalized = code.strip().upper()
        result = await self.session.execute(
            select(LendingOption).where(
                LendingOption.organization_id == organization_id,
                LendingOption.option_group == option_group,
                LendingOption.code == normalized,
                LendingOption.is_active,
            )
        )
        if result.scalar_one_or_none() is None:
            raise BadRequestException(
                f"{code} is not configured for {option_group}",
                error_code="INVALID_LENDING_OPTION",
            )
        return normalized

    # =========================================================================
    # Paginated org-scoped list queries (for list pages)
    # =========================================================================

    async def list_legal_cases_for_org(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 50,
        status: LegalCaseStatus | None = None,
        case_type: str | None = None,
    ) -> tuple[list[LegalCase], int]:
        """Paginated list of legal cases scoped to caller's org."""
        join_filters = [LoanAccount.organization_id == organization_id]
        if status is not None:
            join_filters.append(LegalCase.status == status)
        if case_type is not None:
            join_filters.append(LegalCase.case_type == case_type)
        count_q = (
            select(func.count(LegalCase.id))
            .select_from(LegalCase)
            .join(LoanAccount, LegalCase.loan_account_id == LoanAccount.id)
            .where(*join_filters)
        )
        total = (await self.session.execute(count_q)).scalar() or 0
        result = await self.session.execute(
            select(LegalCase)
            .join(LoanAccount, LegalCase.loan_account_id == LoanAccount.id)
            .where(*join_filters)
            .options(
                selectinload(LegalCase.loan_account).selectinload(LoanAccount.entity),
            )
            .order_by(LegalCase.filing_date.desc().nullslast())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def list_npa_accounts_for_org(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 50,
        classification: AssetClassification | None = None,
    ) -> tuple[list[tuple[LoanAccount, "NPARecord | None"]], int]:
        """Paginated list of NPA accounts scoped to caller's org.

        Returns ``[(LoanAccount, NPARecord|None), ...]`` tuples — the
        list response schema flattens both into a single row.
        """

        npa_classifications = [
            AssetClassification.SUBSTANDARD,
            AssetClassification.DOUBTFUL_1,
            AssetClassification.DOUBTFUL_2,
            AssetClassification.DOUBTFUL_3,
            AssetClassification.LOSS,
        ]
        filters = [
            LoanAccount.organization_id == organization_id,
            LoanAccount.asset_classification.in_(npa_classifications),
        ]
        if classification is not None:
            filters.append(LoanAccount.asset_classification == classification)

        count_q = select(func.count(LoanAccount.id)).select_from(LoanAccount).where(*filters)
        total = (await self.session.execute(count_q)).scalar() or 0

        result = await self.session.execute(
            select(LoanAccount, NPARecord)
            .outerjoin(NPARecord, NPARecord.loan_account_id == LoanAccount.id)
            .where(*filters)
            .options(
                selectinload(LoanAccount.entity),
                selectinload(LoanAccount.product),
            )
            .order_by(LoanAccount.days_past_due.desc())
            .offset(skip)
            .limit(limit)
        )
        return [(row[0], row[1]) for row in result.all()], total

    async def list_follow_ups_for_org(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 50,
        status: FollowUpStatus | None = None,
    ) -> tuple[list[CollectionFollowUp], int]:
        """Paginated list of follow-ups scoped to caller's org."""
        join_filters = [LoanAccount.organization_id == organization_id]
        if status is not None:
            join_filters.append(CollectionFollowUp.status == status)
        count_q = (
            select(func.count(CollectionFollowUp.id))
            .select_from(CollectionFollowUp)
            .join(LoanAccount, CollectionFollowUp.loan_account_id == LoanAccount.id)
            .where(*join_filters)
        )
        total = (await self.session.execute(count_q)).scalar() or 0
        result = await self.session.execute(
            select(CollectionFollowUp)
            .join(LoanAccount, CollectionFollowUp.loan_account_id == LoanAccount.id)
            .where(*join_filters)
            .options(
                selectinload(CollectionFollowUp.loan_account).selectinload(LoanAccount.entity),
            )
            .order_by(CollectionFollowUp.scheduled_date.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def list_ots_proposals_for_org(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 50,
        status: OTSStatus | None = None,
    ) -> tuple[list[OTSProposal], int]:
        """Paginated list of OTS proposals scoped to caller's org."""
        join_filters = [LoanAccount.organization_id == organization_id]
        if status is not None:
            join_filters.append(OTSProposal.status == status)
        count_q = (
            select(func.count(OTSProposal.id))
            .select_from(OTSProposal)
            .join(LoanAccount, OTSProposal.loan_account_id == LoanAccount.id)
            .where(*join_filters)
        )
        total = (await self.session.execute(count_q)).scalar() or 0
        result = await self.session.execute(
            select(OTSProposal)
            .join(LoanAccount, OTSProposal.loan_account_id == LoanAccount.id)
            .where(*join_filters)
            .options(
                selectinload(OTSProposal.loan_account).selectinload(LoanAccount.entity),
            )
            .order_by(OTSProposal.proposal_date.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def list_restructures_for_org(
        self,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 50,
        status: RestructureStatus | None = None,
    ) -> tuple[list[LoanRestructure], int]:
        """Paginated list of restructures scoped to caller's org."""
        join_filters = [LoanAccount.organization_id == organization_id]
        if status is not None:
            join_filters.append(LoanRestructure.status == status)
        count_q = (
            select(func.count(LoanRestructure.id))
            .select_from(LoanRestructure)
            .join(LoanAccount, LoanRestructure.loan_account_id == LoanAccount.id)
            .where(*join_filters)
        )
        total = (await self.session.execute(count_q)).scalar() or 0
        result = await self.session.execute(
            select(LoanRestructure)
            .join(LoanAccount, LoanRestructure.loan_account_id == LoanAccount.id)
            .where(*join_filters)
            .options(
                selectinload(LoanRestructure.loan_account).selectinload(LoanAccount.entity),
            )
            .order_by(LoanRestructure.proposal_date.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    # =========================================================================
    # Collection Follow-Up Operations
    # =========================================================================

    async def create_follow_up(
        self,
        data: CollectionFollowUpCreate,
        created_by: UUID | None = None,
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
        updated_by: UUID | None = None,
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
        updated_by: UUID | None = None,
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
        assigned_to_id: UUID | None = None,
    ) -> list[CollectionFollowUp]:
        """Get follow-ups scheduled for a date."""
        return await self.follow_up_repo.get_scheduled_for_date(scheduled_date, assigned_to_id)

    async def mark_ptp_broken(
        self,
        follow_up_id: UUID,
        updated_by: UUID | None = None,
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
        created_by: UUID | None = None,
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
        updated_by: UUID | None = None,
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
    ) -> list[DemandNotice]:
        """Get demand notices for a loan account."""
        return await self.demand_notice_repo.get_by_loan_account(loan_account_id, skip, limit)

    # =========================================================================
    # NPA Record Operations
    # =========================================================================

    async def create_npa_record(
        self,
        data: NPARecordCreate,
        created_by: UUID | None = None,
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
        updated_by: UUID | None = None,
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
    ) -> NPARecord | None:
        """Get NPA record for a loan account."""
        return await self.npa_record_repo.get_by_loan_account(loan_account_id)

    async def upgrade_npa(
        self,
        loan_account_id: UUID,
        upgrade_date: date,
        updated_by: UUID | None = None,
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
        created_by: UUID | None = None,
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
        created_by: UUID | None = None,
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
        updated_by: UUID | None = None,
    ) -> PenalWaiver:
        """Approve a penal waiver.

        §8.4 maker-checker: the collector who proposed the waiver cannot
        also approve it. Waiving penal charges is a concession that reduces
        recoverable income — it needs two-person sign-off.
        """
        from app.core.maker_checker import ensure_maker_is_not_checker

        waiver = await self.penal_waiver_repo.get(waiver_id)
        if not waiver:
            raise NotFoundException("Penal waiver not found")

        if waiver.is_approved:
            raise BadRequestException("Waiver is already approved")

        ensure_maker_is_not_checker(
            maker_user_id=waiver.created_by,
            checker_user_id=updated_by,
        )

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
        organization_id: UUID,
        data: OTSProposalCreate,
        payment_schedule: list[OTSPaymentScheduleCreate] | None = None,
        created_by: UUID | None = None,
    ) -> OTSProposal:
        """Create an OTS proposal."""
        loan = await self.loan_account_repo.get(data.loan_account_id)
        if loan is None or loan.organization_id != organization_id:
            raise NotFoundException("Loan account not found")
        data.payment_mode = await self._validate_lending_option(
            organization_id, "OTS_PAYMENT_MODE", data.payment_mode
        )

        ots_reference = await self.ots_proposal_repo.generate_ots_reference()

        # Calculate haircut
        haircut_amount = data.total_outstanding - data.ots_amount
        haircut_percent = (
            (haircut_amount / data.total_outstanding * 100)
            if data.total_outstanding > 0
            else Decimal("0")
        )

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
        updated_by: UUID | None = None,
    ) -> OTSProposal:
        """Update an OTS proposal."""
        proposal = await self.ots_proposal_repo.get(proposal_id)
        if not proposal:
            raise NotFoundException("OTS proposal not found")

        if proposal.status not in [OTSStatus.DRAFT, OTSStatus.PROPOSED, OTSStatus.NEGOTIATION]:
            raise BadRequestException("Cannot update proposal in current status")

        update_data = data.model_dump(exclude_unset=True)
        if "payment_mode" in update_data:
            loan = await self.loan_account_repo.get(proposal.loan_account_id)
            if loan is None:
                raise NotFoundException("Loan account not found")
            update_data["payment_mode"] = await self._validate_lending_option(
                loan.organization_id, "OTS_PAYMENT_MODE", update_data["payment_mode"]
            )
        update_data["updated_by"] = updated_by

        return await self.ots_proposal_repo.update(proposal, update_data)

    async def approve_ots_proposal(
        self,
        proposal_id: UUID,
        data: OTSProposalApprove,
        updated_by: UUID | None = None,
    ) -> OTSProposal:
        """Approve an OTS proposal.

        §8.4 maker-checker: the user who prepared the OTS proposal cannot
        also approve it. OTS typically involves a haircut on recoverable
        principal + interest — two-person sign-off is mandatory.
        """
        from app.core.maker_checker import ensure_maker_is_not_checker

        proposal = await self.ots_proposal_repo.get(proposal_id)
        if not proposal:
            raise NotFoundException("OTS proposal not found")

        if proposal.status != OTSStatus.PENDING_APPROVAL:
            raise BadRequestException("Proposal is not pending approval")

        ensure_maker_is_not_checker(
            maker_user_id=proposal.created_by,
            checker_user_id=updated_by,
        )

        before_status = (
            proposal.status.value if hasattr(proposal.status, "value") else str(proposal.status)
        )

        update_data = data.model_dump()
        update_data["status"] = OTSStatus.APPROVED
        update_data["approval_date"] = date.today()
        update_data["updated_by"] = updated_by

        updated = await self.ots_proposal_repo.update(proposal, update_data)

        # Domain audit: OTS approval — §8.5 / §4.8. The haircut split (waiver
        # by component) is captured in metadata so reviewers can reconstruct
        # exactly what concession was granted.
        if updated_by is not None:
            loan = await self.loan_account_repo.get(updated.loan_account_id)
            await record_financial_action(
                self.session,
                organization_id=loan.organization_id,
                entity_type="OTS_PROPOSAL",
                entity_id=updated.id,
                entity_reference=updated.ots_reference,
                action="OTS_APPROVE",
                user_id=updated_by,
                before={
                    "status": before_status,
                    "total_outstanding": proposal.total_outstanding,
                    "ots_amount": proposal.ots_amount,
                    "haircut_amount": proposal.haircut_amount,
                    "haircut_percent": proposal.haircut_percent,
                },
                after={
                    "status": "APPROVED",
                    "approval_date": updated.approval_date,
                    "approval_authority": updated.approval_authority,
                    "ots_amount": updated.ots_amount,
                    "haircut_amount": updated.haircut_amount,
                    "haircut_percent": updated.haircut_percent,
                },
                metadata={
                    "transaction_type": "OTS_APPROVE",
                    "loan_account_id": str(updated.loan_account_id),
                    "loan_account_number": loan.loan_account_number if loan else None,
                    "principal_outstanding": str(updated.principal_outstanding),
                    "interest_outstanding": str(updated.interest_outstanding),
                    "penal_outstanding": str(updated.penal_outstanding),
                    "other_charges": str(updated.other_charges),
                    "principal_waiver": str(updated.principal_waiver),
                    "interest_waiver": str(updated.interest_waiver),
                    "penal_waiver": str(updated.penal_waiver),
                    "charges_waiver": str(updated.charges_waiver),
                    "haircut_amount": str(updated.haircut_amount),
                    "haircut_percent": str(updated.haircut_percent),
                },
                change_reason="OTS proposal approved (maker-checker complete)",
            )

        # Lifecycle event — OTS_APPROVED.
        from app.models.lending.lifecycle_event import (
            LifecycleActorKind,
            LifecycleSubjectType,
        )
        from app.services.lending.lifecycle_service import LifecycleService

        await LifecycleService(self.session).record_event(
            organization_id=loan.organization_id,
            subject_type=LifecycleSubjectType.LOAN_ACCOUNT,
            subject_id=updated.loan_account_id,
            event_type="OTS_APPROVED",
            actor_kind=LifecycleActorKind.LENDER,
            actor_user_id=updated_by,
            business_number=updated.ots_reference,
            state_from=before_status,
            state_to="APPROVED",
            payload={
                "ots_id": str(updated.id),
                "ots_amount": float(updated.ots_amount),
                "haircut_amount": float(updated.haircut_amount),
                "haircut_percent": float(updated.haircut_percent or 0),
            },
            regulatory_tags=["OTS_APPROVED"],
        )

        return updated

    async def accept_ots_by_borrower(
        self,
        proposal_id: UUID,
        data: OTSBorrowerAccept,
        updated_by: UUID | None = None,
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
        updated_by: UUID | None = None,
    ) -> OTSProposal:
        """Record payment against OTS proposal."""
        proposal = await self.ots_proposal_repo.get(proposal_id)
        if not proposal:
            raise NotFoundException("OTS proposal not found")

        if proposal.status not in [
            OTSStatus.ACCEPTED,
            OTSStatus.PAYMENT_PENDING,
            OTSStatus.PARTIALLY_PAID,
        ]:
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
        organization_id: UUID,
        data: LoanRestructureCreate,
        created_by: UUID | None = None,
    ) -> LoanRestructure:
        """Create a loan restructure proposal."""
        loan = await self.loan_account_repo.get(data.loan_account_id)
        if loan is None or loan.organization_id != organization_id:
            raise NotFoundException("Loan account not found")
        data.restructure_type = await self._validate_lending_option(
            organization_id, "RESTRUCTURE_TYPE", data.restructure_type
        )
        data.moratorium_interest_treatment = await self._validate_lending_option(
            organization_id,
            "MORATORIUM_INTEREST_TREATMENT",
            data.moratorium_interest_treatment,
        )

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
        updated_by: UUID | None = None,
    ) -> LoanRestructure:
        """Update a restructure proposal."""
        restructure = await self.restructure_repo.get(restructure_id)
        if not restructure:
            raise NotFoundException("Restructure not found")

        if restructure.status not in [RestructureStatus.DRAFT, RestructureStatus.PROPOSED]:
            raise BadRequestException("Cannot update restructure in current status")

        update_data = data.model_dump(exclude_unset=True)
        loan = await self.loan_account_repo.get(restructure.loan_account_id)
        if loan is None:
            raise NotFoundException("Loan account not found")
        if "moratorium_interest_treatment" in update_data:
            update_data["moratorium_interest_treatment"] = await self._validate_lending_option(
                loan.organization_id,
                "MORATORIUM_INTEREST_TREATMENT",
                update_data["moratorium_interest_treatment"],
            )
        update_data["updated_by"] = updated_by

        return await self.restructure_repo.update(restructure, update_data)

    async def approve_restructure(
        self,
        organization_id: UUID,
        restructure_id: UUID,
        data: LoanRestructureApprove,
        updated_by: UUID | None = None,
    ) -> LoanRestructure:
        """Approve a restructure.

        §8.4 maker-checker: the user who prepared the restructure proposal
        cannot also approve it. Restructuring changes the economics of a
        live loan — two-person sign-off is mandatory.
        """
        from app.core.maker_checker import ensure_maker_is_not_checker

        restructure = await self.restructure_repo.get(restructure_id)
        if not restructure:
            raise NotFoundException("Restructure not found")
        loan = await self.loan_account_repo.get(restructure.loan_account_id)
        if loan is None or loan.organization_id != organization_id:
            raise NotFoundException("Restructure not found")

        if restructure.status != RestructureStatus.PENDING_APPROVAL:
            raise BadRequestException("Restructure is not pending approval")

        ensure_maker_is_not_checker(
            maker_user_id=restructure.created_by,
            checker_user_id=updated_by,
        )

        before_status = (
            restructure.status.value
            if hasattr(restructure.status, "value")
            else str(restructure.status)
        )

        update_data = data.model_dump()
        update_data["status"] = RestructureStatus.APPROVED
        update_data["approval_date"] = date.today()
        update_data["updated_by"] = updated_by

        updated = await self.restructure_repo.update(restructure, update_data)

        # Domain audit: restructure approved — §8.5 / §4.8.
        if updated_by is not None:
            await record_financial_action(
                self.session,
                organization_id=loan.organization_id if loan else updated.organization_id,  # type: ignore[attr-defined]
                entity_type="LOAN_RESTRUCTURE",
                entity_id=updated.id,
                entity_reference=updated.restructure_reference,
                action="RESTRUCTURE_APPROVE",
                user_id=updated_by,
                before={
                    "status": before_status,
                    "pre_interest_rate": restructure.pre_interest_rate,
                    "pre_tenure_months": restructure.pre_tenure_months,
                    "pre_emi_amount": restructure.pre_emi_amount,
                    "pre_maturity_date": restructure.pre_maturity_date,
                },
                after={
                    "status": "APPROVED",
                    "approval_date": updated.approval_date,
                    "post_interest_rate": updated.post_interest_rate,
                    "post_tenure_months": updated.post_tenure_months,
                    "post_emi_amount": updated.post_emi_amount,
                    "post_maturity_date": updated.post_maturity_date,
                },
                metadata={
                    "transaction_type": "RESTRUCTURE_APPROVE",
                    "loan_account_id": str(updated.loan_account_id),
                    "loan_account_number": loan.loan_account_number if loan else None,
                    "restructure_type": (
                        updated.restructure_type.value
                        if hasattr(updated.restructure_type, "value")
                        else str(updated.restructure_type)
                    ),
                    "interest_waived": str(updated.interest_waived),
                    "penal_waived": str(updated.penal_waived),
                    "principal_converted_to_fitl": str(updated.principal_converted_to_fitl),
                    "moratorium_months": updated.moratorium_months,
                    "downgrade_required": updated.downgrade_required,
                },
                change_reason="Restructure approved (maker-checker complete)",
            )

        # Lifecycle event — RESTRUCTURE_APPROVED.
        from app.models.lending.lifecycle_event import (
            LifecycleActorKind,
            LifecycleSubjectType,
        )
        from app.services.lending.lifecycle_service import LifecycleService

        await LifecycleService(self.session).record_event(
            organization_id=updated.organization_id,
            subject_type=LifecycleSubjectType.LOAN_ACCOUNT,
            subject_id=updated.loan_account_id,
            event_type="RESTRUCTURE_APPROVED",
            actor_kind=LifecycleActorKind.LENDER,
            actor_user_id=updated_by,
            business_number=updated.restructure_reference,
            state_from=before_status,
            state_to="APPROVED",
            payload={
                "restructure_id": str(updated.id),
                "post_interest_rate": float(updated.post_interest_rate or 0),
                "post_tenure_months": updated.post_tenure_months,
                "moratorium_months": updated.moratorium_months,
            },
            regulatory_tags=["RESTRUCTURE_APPROVED"],
        )

        return updated

    async def reject_restructure(
        self,
        organization_id: UUID,
        restructure_id: UUID,
        data: LoanRestructureReject,
        updated_by: UUID | None = None,
    ) -> LoanRestructure:
        """Reject a restructure proposal through maker-checker review."""
        from app.core.maker_checker import ensure_maker_is_not_checker

        restructure = await self.restructure_repo.get(restructure_id)
        if not restructure:
            raise NotFoundException("Restructure not found")
        loan = await self.loan_account_repo.get(restructure.loan_account_id)
        if loan is None or loan.organization_id != organization_id:
            raise NotFoundException("Restructure not found")

        if restructure.status != RestructureStatus.PENDING_APPROVAL:
            raise BadRequestException("Restructure is not pending approval")

        ensure_maker_is_not_checker(
            maker_user_id=restructure.created_by,
            checker_user_id=updated_by,
        )

        return await self.restructure_repo.update(
            restructure,
            {
                "status": RestructureStatus.REJECTED,
                "approval_authority": data.approval_authority,
                "remarks": data.rejection_reason,
                "updated_by": updated_by,
            },
        )

    async def implement_restructure(
        self,
        restructure_id: UUID,
        data: LoanRestructureImplement,
        updated_by: UUID | None = None,
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
        created_by: UUID | None = None,
    ) -> LegalCase:
        """Create a legal case."""
        case_reference = await self.legal_case_repo.generate_case_reference()
        loan_account = await self.loan_account_repo.get(data.loan_account_id)
        if not loan_account:
            raise ValueError("Loan account not found")

        legal_case = LegalCase(
            **data.model_dump(),
            organization_id=loan_account.organization_id,
            case_reference=case_reference,
            status=LegalCaseStatus.DRAFT,
            created_by=created_by,
        )
        return await self.legal_case_repo.create(legal_case)

    async def update_legal_case(
        self,
        case_id: UUID,
        data: LegalCaseUpdate,
        updated_by: UUID | None = None,
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
        created_by: UUID | None = None,
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
        updated_by: UUID | None = None,
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
    ) -> list[LegalCase]:
        """Get cases with upcoming hearings."""
        return await self.legal_case_repo.get_upcoming_hearings(days)

    # =========================================================================
    # Property Auction Operations
    # =========================================================================

    async def create_auction(
        self,
        data: PropertyAuctionCreate,
        created_by: UUID | None = None,
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
        updated_by: UUID | None = None,
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
    ) -> list[PropertyAuction]:
        """Get upcoming auctions."""
        return await self.auction_repo.get_upcoming_auctions(days)

    # =========================================================================
    # Write-Off Operations
    # =========================================================================

    async def create_write_off(
        self,
        data: WriteOffCreate,
        created_by: UUID | None = None,
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
        updated_by: UUID | None = None,
    ) -> WriteOffRecord:
        """Approve a write-off.

        §8.4 maker-checker: the user who prepared the write-off recommendation
        cannot also approve it. Writing off a loan removes it from the balance
        sheet — this is the highest-severity concession and demands two-person
        sign-off.
        """
        from app.core.maker_checker import ensure_maker_is_not_checker

        write_off = await self.write_off_repo.get(write_off_id)
        if not write_off:
            raise NotFoundException("Write-off not found")

        if write_off.status != WriteOffStatus.PENDING_APPROVAL:
            raise BadRequestException("Write-off is not pending approval")

        ensure_maker_is_not_checker(
            maker_user_id=write_off.created_by,
            checker_user_id=updated_by,
        )

        before_status = (
            write_off.status.value if hasattr(write_off.status, "value") else str(write_off.status)
        )

        update_data = data.model_dump()
        update_data["status"] = WriteOffStatus.APPROVED
        update_data["approval_date"] = date.today()
        update_data["updated_by"] = updated_by

        updated = await self.write_off_repo.update(write_off, update_data)

        # Domain audit: write-off approval — §8.5 / §4.8.
        # Captures the principal/interest/penal split being written off.
        if updated_by is not None:
            loan = await self.loan_account_repo.get(updated.loan_account_id)
            await record_financial_action(
                self.session,
                organization_id=loan.organization_id if loan else updated.organization_id,  # type: ignore[attr-defined]
                entity_type="WRITE_OFF",
                entity_id=updated.id,
                entity_reference=updated.write_off_reference,
                action="WRITE_OFF",
                user_id=updated_by,
                before={
                    "status": before_status,
                    "principal_outstanding": write_off.principal_outstanding,
                    "interest_outstanding": write_off.interest_outstanding,
                    "penal_outstanding": write_off.penal_outstanding,
                    "total_outstanding": write_off.total_outstanding,
                },
                after={
                    "status": "APPROVED",
                    "approval_date": updated.approval_date,
                    "approval_authority": updated.approval_authority,
                    "principal_written_off": updated.principal_written_off,
                    "interest_written_off": updated.interest_written_off,
                    "penal_written_off": updated.penal_written_off,
                    "total_written_off": updated.total_written_off,
                },
                metadata={
                    "transaction_type": "WRITE_OFF",
                    "loan_account_id": str(updated.loan_account_id),
                    "loan_account_number": loan.loan_account_number if loan else None,
                    "write_off_type": (
                        updated.write_off_type.value
                        if hasattr(updated.write_off_type, "value")
                        else str(updated.write_off_type)
                    ),
                    "principal_written_off": str(updated.principal_written_off),
                    "interest_written_off": str(updated.interest_written_off),
                    "penal_written_off": str(updated.penal_written_off),
                    "total_written_off": str(updated.total_written_off),
                    "provision_utilized": str(updated.provision_utilized),
                    "provision_available": str(updated.provision_available),
                    "board_resolution_number": updated.board_resolution_number,
                    "board_resolution_date": (
                        updated.board_resolution_date.isoformat()
                        if updated.board_resolution_date
                        else None
                    ),
                },
                change_reason="Write-off approved (maker-checker complete)",
            )

        # Lifecycle event — WRITE_OFF_TECHNICAL or WRITE_OFF_FINAL.
        from app.models.lending.lifecycle_event import (
            LifecycleActorKind,
            LifecycleSubjectType,
        )
        from app.services.lending.lifecycle_service import LifecycleService

        wo_type_value = (
            updated.write_off_type.value
            if hasattr(updated.write_off_type, "value")
            else str(updated.write_off_type)
        )
        event_type = (
            "WRITE_OFF_TECHNICAL" if wo_type_value.upper().startswith("TECH") else "WRITE_OFF_FINAL"
        )
        await LifecycleService(self.session).record_event(
            organization_id=updated.organization_id,
            subject_type=LifecycleSubjectType.LOAN_ACCOUNT,
            subject_id=updated.loan_account_id,
            event_type=event_type,
            actor_kind=LifecycleActorKind.LENDER,
            actor_user_id=updated_by,
            business_number=updated.write_off_reference,
            state_from=before_status,
            state_to="APPROVED",
            payload={
                "write_off_id": str(updated.id),
                "write_off_type": wo_type_value,
                "total_written_off": float(updated.total_written_off or 0),
                "principal_written_off": float(updated.principal_written_off or 0),
                "interest_written_off": float(updated.interest_written_off or 0),
            },
            regulatory_tags=[event_type],
        )

        return updated

    async def effect_write_off(
        self,
        write_off_id: UUID,
        data: WriteOffEffect,
        updated_by: UUID | None = None,
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
                "principal_written_off": loan_account.principal_written_off
                + write_off.principal_written_off,
                "interest_written_off": loan_account.interest_written_off
                + write_off.interest_written_off,
                "write_off_date": data.effective_date,
            }
            await self.loan_account_repo.update(loan_account, loan_update)

        return await self.write_off_repo.update(write_off, update_data)

    # =========================================================================
    # Summary & Dashboard Operations
    # =========================================================================

    async def get_npa_summary(self, organization_id: UUID | None = None) -> NPASummary:
        """Get NPA portfolio summary.

        The ``organization_id`` argument is accepted for symmetry with the
        other summary methods; current repo-level filter already runs
        under the request's org-scoped session (RLS via get_db_with_tenant).
        """
        _ = organization_id  # currently unused at this layer
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

    async def get_collection_summary(
        self, organization_id: UUID | None = None
    ) -> CollectionActivitySummary:
        """Get collection activity summary."""
        _ = organization_id
        today = date.today()

        # Get pending follow-ups
        scheduled = await self.follow_up_repo.get_scheduled_for_date(today)

        summary = CollectionActivitySummary(
            pending_follow_ups=len(scheduled),
        )

        return summary

    async def get_recovery_summary(self, organization_id: UUID | None = None) -> RecoverySummary:
        """Get recovery summary."""
        _ = organization_id
        # Get OTS stats
        ots_approved = await self.ots_proposal_repo.get_by_status(OTSStatus.APPROVED)
        ots_completed = await self.ots_proposal_repo.get_by_status(OTSStatus.COMPLETED)

        # Get restructure stats
        restructures_approved = await self.restructure_repo.get_by_status(
            RestructureStatus.APPROVED
        )
        restructures_implemented = await self.restructure_repo.get_by_status(
            RestructureStatus.IMPLEMENTED
        )

        # Get legal case stats
        legal_pending = await self.legal_case_repo.get_by_status(LegalCaseStatus.PENDING)
        legal_decree = await self.legal_case_repo.get_by_status(LegalCaseStatus.DECREE_OBTAINED)

        # Get write-off stats
        write_off_data = await self.write_off_repo.get_total_written_off()

        # Calculate OTS settlement amount
        ots_settlement_amount = (
            sum(p.ots_amount for p in ots_completed) if ots_completed else Decimal("0")
        )

        # Calculate legal recovery
        recovery_through_legal = (
            sum(c.recovery_through_case for c in legal_decree) if legal_decree else Decimal("0")
        )

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
    ) -> list[tuple[UUID, AssetClassification]]:
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
    ) -> list[CollectionFollowUp]:
        """Auto-create follow-ups for overdue accounts based on DPD."""
        # This would be called by a scheduled job
        created_follow_ups = []

        # Get accounts by DPD buckets and create appropriate follow-ups
        # Logic would vary based on organization's collection policy

        return created_follow_ups
