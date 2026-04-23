"""Phase 3: NPA & Collections repositories for the lending module."""

from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.repositories.base import BaseRepository
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
    CollectionStage,
    FollowUpStatus,
    NPAStatus,
    OTSStatus,
    RestructureStatus,
    LegalCaseStatus,
    AuctionStatus,
    WriteOffStatus,
)


class CollectionFollowUpRepository(BaseRepository[CollectionFollowUp]):
    """Repository for collection follow-up operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(CollectionFollowUp, session)

    async def get_by_loan_account(
        self,
        loan_account_id: UUID,
        status: Optional[FollowUpStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[CollectionFollowUp]:
        """Get follow-ups for a loan account."""
        query = select(CollectionFollowUp).where(
            CollectionFollowUp.loan_account_id == loan_account_id,
            CollectionFollowUp.is_deleted == False,
        )
        if status:
            query = query.where(CollectionFollowUp.status == status)
        query = query.order_by(CollectionFollowUp.scheduled_date.desc()).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_scheduled_for_date(
        self,
        scheduled_date: date,
        assigned_to_id: Optional[UUID] = None,
    ) -> List[CollectionFollowUp]:
        """Get follow-ups scheduled for a specific date."""
        query = select(CollectionFollowUp).where(
            CollectionFollowUp.scheduled_date == scheduled_date,
            CollectionFollowUp.status == FollowUpStatus.SCHEDULED,
            CollectionFollowUp.is_deleted == False,
        )
        if assigned_to_id:
            query = query.where(CollectionFollowUp.assigned_to_id == assigned_to_id)
        query = query.order_by(CollectionFollowUp.scheduled_time)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_pending_ptp(
        self,
        as_of_date: date,
    ) -> List[CollectionFollowUp]:
        """Get follow-ups with PTP date passed and not fulfilled."""
        query = select(CollectionFollowUp).where(
            CollectionFollowUp.ptp_date <= as_of_date,
            CollectionFollowUp.ptp_broken == False,
            CollectionFollowUp.is_deleted == False,
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_by_status(
        self,
        loan_account_id: UUID,
    ) -> dict:
        """Count follow-ups by status for a loan account."""
        query = (
            select(CollectionFollowUp.status, func.count(CollectionFollowUp.id))
            .where(
                CollectionFollowUp.loan_account_id == loan_account_id,
                CollectionFollowUp.is_deleted == False,
            )
            .group_by(CollectionFollowUp.status)
        )
        result = await self.session.execute(query)
        return dict(result.all())


class DemandNoticeRepository(BaseRepository[DemandNotice]):
    """Repository for demand notice operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(DemandNotice, session)

    async def get_by_loan_account(
        self,
        loan_account_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[DemandNotice]:
        """Get demand notices for a loan account."""
        query = (
            select(DemandNotice)
            .where(
                DemandNotice.loan_account_id == loan_account_id,
                DemandNotice.is_deleted == False,
            )
            .order_by(DemandNotice.notice_date.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_notice_number(
        self,
        notice_number: str,
    ) -> Optional[DemandNotice]:
        """Get demand notice by notice number."""
        query = select(DemandNotice).where(
            DemandNotice.notice_number == notice_number,
            DemandNotice.is_deleted == False,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def generate_notice_number(
        self,
        prefix: str = "DN",
    ) -> str:
        """Generate unique notice number."""
        year = date.today().year
        query = select(func.count(DemandNotice.id)).where(
            DemandNotice.notice_number.like(f"{prefix}/{year}/%"),
        )
        result = await self.session.execute(query)
        count = result.scalar() or 0
        return f"{prefix}/{year}/{count + 1:05d}"


class NPARecordRepository(BaseRepository[NPARecord]):
    """Repository for NPA record operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(NPARecord, session)

    async def get_by_loan_account(
        self,
        loan_account_id: UUID,
    ) -> Optional[NPARecord]:
        """Get NPA record for a loan account."""
        query = select(NPARecord).where(
            NPARecord.loan_account_id == loan_account_id,
            NPARecord.is_deleted == False,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_npa_accounts(
        self,
        npa_status: Optional[NPAStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[NPARecord]:
        """Get all NPA records."""
        query = select(NPARecord).where(NPARecord.is_deleted == False)
        if npa_status:
            query = query.where(NPARecord.npa_status == npa_status)
        query = query.order_by(NPARecord.npa_date.desc()).offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_npa_summary(self) -> dict:
        """Get NPA summary statistics."""
        query = (
            select(
                NPARecord.current_classification,
                func.count(NPARecord.id),
                func.sum(NPARecord.current_total),
                func.sum(NPARecord.provision_amount),
            )
            .where(
                NPARecord.npa_status == NPAStatus.NPA,
                NPARecord.is_deleted == False,
            )
            .group_by(NPARecord.current_classification)
        )
        result = await self.session.execute(query)
        return {
            row[0]: {"count": row[1], "amount": row[2], "provision": row[3]}
            for row in result.all()
        }


class PenalInterestRepository(BaseRepository[PenalInterest]):
    """Repository for penal interest operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(PenalInterest, session)

    async def get_by_loan_account(
        self,
        loan_account_id: UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[PenalInterest]:
        """Get penal interest records for a loan account."""
        query = (
            select(PenalInterest)
            .where(
                PenalInterest.loan_account_id == loan_account_id,
                PenalInterest.is_deleted == False,
            )
            .order_by(PenalInterest.period_end.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_total_outstanding(
        self,
        loan_account_id: UUID,
    ) -> Decimal:
        """Get total outstanding penal interest for a loan account."""
        query = (
            select(func.sum(PenalInterest.applied_amount - PenalInterest.waived_amount))
            .where(
                PenalInterest.loan_account_id == loan_account_id,
                PenalInterest.is_accrued == True,
                PenalInterest.is_deleted == False,
            )
        )
        result = await self.session.execute(query)
        return result.scalar() or Decimal("0")


class PenalWaiverRepository(BaseRepository[PenalWaiver]):
    """Repository for penal waiver operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(PenalWaiver, session)

    async def get_by_loan_account(
        self,
        loan_account_id: UUID,
    ) -> List[PenalWaiver]:
        """Get penal waivers for a loan account."""
        query = (
            select(PenalWaiver)
            .where(
                PenalWaiver.loan_account_id == loan_account_id,
                PenalWaiver.is_deleted == False,
            )
            .order_by(PenalWaiver.waiver_date.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_reference(
        self,
        waiver_reference: str,
    ) -> Optional[PenalWaiver]:
        """Get penal waiver by reference."""
        query = select(PenalWaiver).where(
            PenalWaiver.waiver_reference == waiver_reference,
            PenalWaiver.is_deleted == False,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def generate_waiver_reference(
        self,
        prefix: str = "PWV",
    ) -> str:
        """Generate unique waiver reference."""
        year = date.today().year
        query = select(func.count(PenalWaiver.id)).where(
            PenalWaiver.waiver_reference.like(f"{prefix}/{year}/%"),
        )
        result = await self.session.execute(query)
        count = result.scalar() or 0
        return f"{prefix}/{year}/{count + 1:05d}"


class OTSProposalRepository(BaseRepository[OTSProposal]):
    """Repository for OTS proposal operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(OTSProposal, session)

    async def get_by_loan_account(
        self,
        loan_account_id: UUID,
    ) -> List[OTSProposal]:
        """Get OTS proposals for a loan account."""
        query = (
            select(OTSProposal)
            .options(selectinload(OTSProposal.payment_schedule))
            .where(
                OTSProposal.loan_account_id == loan_account_id,
                OTSProposal.is_deleted == False,
            )
            .order_by(OTSProposal.proposal_date.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_reference(
        self,
        ots_reference: str,
    ) -> Optional[OTSProposal]:
        """Get OTS proposal by reference."""
        query = (
            select(OTSProposal)
            .options(selectinload(OTSProposal.payment_schedule))
            .where(
                OTSProposal.ots_reference == ots_reference,
                OTSProposal.is_deleted == False,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_status(
        self,
        status: OTSStatus,
        skip: int = 0,
        limit: int = 100,
    ) -> List[OTSProposal]:
        """Get OTS proposals by status."""
        query = (
            select(OTSProposal)
            .where(
                OTSProposal.status == status,
                OTSProposal.is_deleted == False,
            )
            .order_by(OTSProposal.valid_till)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_expiring_soon(
        self,
        days: int = 7,
    ) -> List[OTSProposal]:
        """Get OTS proposals expiring soon."""
        target_date = date.today()
        from datetime import timedelta
        end_date = target_date + timedelta(days=days)
        query = (
            select(OTSProposal)
            .where(
                OTSProposal.status.in_([OTSStatus.APPROVED, OTSStatus.ACCEPTED]),
                OTSProposal.valid_till.between(target_date, end_date),
                OTSProposal.is_deleted == False,
            )
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def generate_ots_reference(
        self,
        prefix: str = "OTS",
    ) -> str:
        """Generate unique OTS reference."""
        year = date.today().year
        query = select(func.count(OTSProposal.id)).where(
            OTSProposal.ots_reference.like(f"{prefix}/{year}/%"),
        )
        result = await self.session.execute(query)
        count = result.scalar() or 0
        return f"{prefix}/{year}/{count + 1:05d}"


class OTSPaymentScheduleRepository(BaseRepository[OTSPaymentSchedule]):
    """Repository for OTS payment schedule operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(OTSPaymentSchedule, session)

    async def get_by_ots_proposal(
        self,
        ots_proposal_id: UUID,
    ) -> List[OTSPaymentSchedule]:
        """Get payment schedule for OTS proposal."""
        query = (
            select(OTSPaymentSchedule)
            .where(
                OTSPaymentSchedule.ots_proposal_id == ots_proposal_id,
                OTSPaymentSchedule.is_deleted == False,
            )
            .order_by(OTSPaymentSchedule.installment_number)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_overdue_installments(
        self,
        as_of_date: date,
    ) -> List[OTSPaymentSchedule]:
        """Get overdue OTS installments."""
        query = (
            select(OTSPaymentSchedule)
            .where(
                OTSPaymentSchedule.due_date < as_of_date,
                OTSPaymentSchedule.is_paid == False,
                OTSPaymentSchedule.is_deleted == False,
            )
            .order_by(OTSPaymentSchedule.due_date)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())


class LoanRestructureRepository(BaseRepository[LoanRestructure]):
    """Repository for loan restructure operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(LoanRestructure, session)

    async def get_by_loan_account(
        self,
        loan_account_id: UUID,
    ) -> List[LoanRestructure]:
        """Get restructures for a loan account."""
        query = (
            select(LoanRestructure)
            .where(
                LoanRestructure.loan_account_id == loan_account_id,
                LoanRestructure.is_deleted == False,
            )
            .order_by(LoanRestructure.proposal_date.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_reference(
        self,
        restructure_reference: str,
    ) -> Optional[LoanRestructure]:
        """Get restructure by reference."""
        query = select(LoanRestructure).where(
            LoanRestructure.restructure_reference == restructure_reference,
            LoanRestructure.is_deleted == False,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_status(
        self,
        status: RestructureStatus,
        skip: int = 0,
        limit: int = 100,
    ) -> List[LoanRestructure]:
        """Get restructures by status."""
        query = (
            select(LoanRestructure)
            .where(
                LoanRestructure.status == status,
                LoanRestructure.is_deleted == False,
            )
            .order_by(LoanRestructure.proposal_date.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def generate_restructure_reference(
        self,
        prefix: str = "RST",
    ) -> str:
        """Generate unique restructure reference."""
        year = date.today().year
        query = select(func.count(LoanRestructure.id)).where(
            LoanRestructure.restructure_reference.like(f"{prefix}/{year}/%"),
        )
        result = await self.session.execute(query)
        count = result.scalar() or 0
        return f"{prefix}/{year}/{count + 1:05d}"


class LegalCaseRepository(BaseRepository[LegalCase]):
    """Repository for legal case operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(LegalCase, session)

    async def get_by_loan_account(
        self,
        loan_account_id: UUID,
    ) -> List[LegalCase]:
        """Get legal cases for a loan account."""
        query = (
            select(LegalCase)
            .options(
                selectinload(LegalCase.hearings),
                selectinload(LegalCase.auctions),
            )
            .where(
                LegalCase.loan_account_id == loan_account_id,
                LegalCase.is_deleted == False,
            )
            .order_by(LegalCase.created_at.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_reference(
        self,
        case_reference: str,
    ) -> Optional[LegalCase]:
        """Get legal case by reference."""
        query = (
            select(LegalCase)
            .options(
                selectinload(LegalCase.hearings),
                selectinload(LegalCase.auctions),
            )
            .where(
                LegalCase.case_reference == case_reference,
                LegalCase.is_deleted == False,
            )
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_status(
        self,
        status: LegalCaseStatus,
        skip: int = 0,
        limit: int = 100,
    ) -> List[LegalCase]:
        """Get legal cases by status."""
        query = (
            select(LegalCase)
            .where(
                LegalCase.status == status,
                LegalCase.is_deleted == False,
            )
            .order_by(LegalCase.next_hearing_date)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_upcoming_hearings(
        self,
        days: int = 7,
    ) -> List[LegalCase]:
        """Get cases with upcoming hearings."""
        target_date = date.today()
        from datetime import timedelta
        end_date = target_date + timedelta(days=days)
        query = (
            select(LegalCase)
            .where(
                LegalCase.next_hearing_date.between(target_date, end_date),
                LegalCase.is_deleted == False,
            )
            .order_by(LegalCase.next_hearing_date)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def generate_case_reference(
        self,
        prefix: str = "LC",
    ) -> str:
        """Generate unique case reference."""
        year = date.today().year
        query = select(func.count(LegalCase.id)).where(
            LegalCase.case_reference.like(f"{prefix}/{year}/%"),
        )
        result = await self.session.execute(query)
        count = result.scalar() or 0
        return f"{prefix}/{year}/{count + 1:05d}"


class LegalHearingRepository(BaseRepository[LegalHearing]):
    """Repository for legal hearing operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(LegalHearing, session)

    async def get_by_legal_case(
        self,
        legal_case_id: UUID,
    ) -> List[LegalHearing]:
        """Get hearings for a legal case."""
        query = (
            select(LegalHearing)
            .where(
                LegalHearing.legal_case_id == legal_case_id,
                LegalHearing.is_deleted == False,
            )
            .order_by(LegalHearing.hearing_date.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_latest_hearing(
        self,
        legal_case_id: UUID,
    ) -> Optional[LegalHearing]:
        """Get the latest hearing for a legal case."""
        query = (
            select(LegalHearing)
            .where(
                LegalHearing.legal_case_id == legal_case_id,
                LegalHearing.is_deleted == False,
            )
            .order_by(LegalHearing.hearing_date.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_next_hearing_number(
        self,
        legal_case_id: UUID,
    ) -> int:
        """Get next hearing number for a case."""
        query = (
            select(func.max(LegalHearing.hearing_number))
            .where(
                LegalHearing.legal_case_id == legal_case_id,
                LegalHearing.is_deleted == False,
            )
        )
        result = await self.session.execute(query)
        max_num = result.scalar() or 0
        return max_num + 1


class PropertyAuctionRepository(BaseRepository[PropertyAuction]):
    """Repository for property auction operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(PropertyAuction, session)

    async def get_by_legal_case(
        self,
        legal_case_id: UUID,
    ) -> List[PropertyAuction]:
        """Get auctions for a legal case."""
        query = (
            select(PropertyAuction)
            .where(
                PropertyAuction.legal_case_id == legal_case_id,
                PropertyAuction.is_deleted == False,
            )
            .order_by(PropertyAuction.auction_date.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_reference(
        self,
        auction_reference: str,
    ) -> Optional[PropertyAuction]:
        """Get auction by reference."""
        query = select(PropertyAuction).where(
            PropertyAuction.auction_reference == auction_reference,
            PropertyAuction.is_deleted == False,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_status(
        self,
        status: AuctionStatus,
        skip: int = 0,
        limit: int = 100,
    ) -> List[PropertyAuction]:
        """Get auctions by status."""
        query = (
            select(PropertyAuction)
            .where(
                PropertyAuction.status == status,
                PropertyAuction.is_deleted == False,
            )
            .order_by(PropertyAuction.auction_date)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_upcoming_auctions(
        self,
        days: int = 30,
    ) -> List[PropertyAuction]:
        """Get upcoming auctions."""
        target_date = date.today()
        from datetime import timedelta
        end_date = target_date + timedelta(days=days)
        query = (
            select(PropertyAuction)
            .where(
                PropertyAuction.auction_date.between(target_date, end_date),
                PropertyAuction.status.in_([AuctionStatus.SCHEDULED, AuctionStatus.PUBLISHED]),
                PropertyAuction.is_deleted == False,
            )
            .order_by(PropertyAuction.auction_date)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def generate_auction_reference(
        self,
        prefix: str = "AUC",
    ) -> str:
        """Generate unique auction reference."""
        year = date.today().year
        query = select(func.count(PropertyAuction.id)).where(
            PropertyAuction.auction_reference.like(f"{prefix}/{year}/%"),
        )
        result = await self.session.execute(query)
        count = result.scalar() or 0
        return f"{prefix}/{year}/{count + 1:05d}"


class WriteOffRecordRepository(BaseRepository[WriteOffRecord]):
    """Repository for write-off record operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(WriteOffRecord, session)

    async def get_by_loan_account(
        self,
        loan_account_id: UUID,
    ) -> List[WriteOffRecord]:
        """Get write-offs for a loan account."""
        query = (
            select(WriteOffRecord)
            .where(
                WriteOffRecord.loan_account_id == loan_account_id,
                WriteOffRecord.is_deleted == False,
            )
            .order_by(WriteOffRecord.proposal_date.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_by_reference(
        self,
        write_off_reference: str,
    ) -> Optional[WriteOffRecord]:
        """Get write-off by reference."""
        query = select(WriteOffRecord).where(
            WriteOffRecord.write_off_reference == write_off_reference,
            WriteOffRecord.is_deleted == False,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_by_status(
        self,
        status: WriteOffStatus,
        skip: int = 0,
        limit: int = 100,
    ) -> List[WriteOffRecord]:
        """Get write-offs by status."""
        query = (
            select(WriteOffRecord)
            .where(
                WriteOffRecord.status == status,
                WriteOffRecord.is_deleted == False,
            )
            .order_by(WriteOffRecord.proposal_date.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_total_written_off(self) -> dict:
        """Get total written off amounts."""
        query = (
            select(
                func.count(WriteOffRecord.id),
                func.sum(WriteOffRecord.total_written_off),
                func.sum(WriteOffRecord.recovery_after_write_off),
            )
            .where(
                WriteOffRecord.status == WriteOffStatus.EFFECTED,
                WriteOffRecord.is_deleted == False,
            )
        )
        result = await self.session.execute(query)
        row = result.one()
        return {
            "count": row[0] or 0,
            "total_written_off": row[1] or Decimal("0"),
            "recovery_after_write_off": row[2] or Decimal("0"),
        }

    async def generate_write_off_reference(
        self,
        prefix: str = "WO",
    ) -> str:
        """Generate unique write-off reference."""
        year = date.today().year
        query = select(func.count(WriteOffRecord.id)).where(
            WriteOffRecord.write_off_reference.like(f"{prefix}/{year}/%"),
        )
        result = await self.session.execute(query)
        count = result.scalar() or 0
        return f"{prefix}/{year}/{count + 1:05d}"
