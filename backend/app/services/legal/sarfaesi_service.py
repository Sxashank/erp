"""SARFAESI Workflow Service.

Provides business logic for managing SARFAESI Act proceedings
including demand notices, possession, and auction.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.lending.collections import LegalCase, PropertyAuction, LegalHearing
from app.models.lending.enums import (
    LegalCaseType,
    LegalForumType,
    LegalCaseStatus,
    SARFAESIStage,
    AuctionStatus,
)
from app.models.legal.notice import LegalNotice
from app.models.legal.enums import NoticeType, NoticeStatus
from app.services.legal.notice_service import NoticeService
from app.services.legal.statutory_service import StatutoryService


class SARFAESIService:
    """Service for managing SARFAESI proceedings."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.notice_service = NoticeService(db)
        self.statutory_service = StatutoryService(db)

    # =========================================================================
    # SARFAESI Initiation
    # =========================================================================

    async def initiate_sarfaesi(
        self,
        organization_id: UUID,
        loan_account_id: UUID,
        claim_principal: Decimal,
        claim_interest: Decimal,
        borrower_name: str,
        borrower_address: str,
        loan_account_number: str,
        court_name: str = "Authorized Officer",
        court_location: str = "Head Office",
        claim_costs: Decimal = Decimal("0"),
        interest_rate_claimed: Optional[Decimal] = None,
        security_description: Optional[str] = None,
        security_address: Optional[str] = None,
        security_value: Optional[Decimal] = None,
        created_by: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """Initiate SARFAESI proceedings with Section 13(2) notice.

        This creates:
        1. A legal case of type SARFAESI
        2. A Section 13(2) demand notice

        Returns dict with legal_case and notice objects.
        """
        # Generate case reference
        case_reference = await self._generate_case_reference(organization_id)
        total_claim = claim_principal + claim_interest + claim_costs

        # Create Legal Case
        legal_case = LegalCase(
            organization_id=organization_id,
            loan_account_id=loan_account_id,
            case_reference=case_reference,
            case_type=LegalCaseType.SARFAESI,
            forum_type=LegalForumType.SARFAESI,
            status=LegalCaseStatus.NOTICE_ISSUED,
            court_name=court_name,
            court_location=court_location,
            claim_principal=claim_principal,
            claim_interest=claim_interest,
            claim_costs=claim_costs,
            total_claim=total_claim,
            interest_rate_claimed=interest_rate_claimed,
            sarfaesi_stage=SARFAESIStage.DEMAND_13_2,
            demand_notice_date=date.today(),
            created_by=created_by,
        )
        self.db.add(legal_case)
        await self.db.flush()

        # Generate Section 13(2) Notice
        notice = await self.notice_service.generate_notice(
            organization_id=organization_id,
            loan_account_id=loan_account_id,
            notice_type=NoticeType.SARFAESI_13_2,
            borrower_name=borrower_name,
            borrower_address=borrower_address,
            loan_account_number=loan_account_number,
            principal_outstanding=claim_principal,
            interest_outstanding=claim_interest,
            legal_case_id=legal_case.id,
            security_description=security_description,
            security_address=security_address,
            security_value=security_value,
            future_interest_rate=interest_rate_claimed,
            created_by=created_by,
        )

        # Start statutory period tracking
        period = await self.statutory_service.get_period_by_code(
            organization_id, "SARFAESI_13_2"
        )
        if period:
            await self.statutory_service.start_period_tracking(
                organization_id=organization_id,
                legal_case_id=legal_case.id,
                statutory_period_id=period.id,
                trigger_event="Section 13(2) notice issued",
                trigger_date=date.today(),
                action_required="Wait for 60 days response period or process objections",
                loan_account_id=loan_account_id,
                created_by=created_by,
            )

        return {
            "legal_case": legal_case,
            "notice": notice,
            "timeline": self.statutory_service.calculate_sarfaesi_timeline(date.today()),
        }

    # =========================================================================
    # Objection Handling
    # =========================================================================

    async def record_objection(
        self,
        legal_case_id: UUID,
        objection_date: date,
        objection_summary: str,
        objection_grounds: str,
        respondent_name: str,
        respondent_type: str = "BORROWER",
        document_path: Optional[str] = None,
        updated_by: Optional[UUID] = None,
    ) -> LegalCase:
        """Record objection received under Section 13(3A).

        Borrower has right to make representation/objection
        which must be disposed within 15 days (Section 13(3A)).
        """
        result = await self.db.execute(
            select(LegalCase).where(LegalCase.id == legal_case_id)
        )
        legal_case = result.scalar_one_or_none()
        if not legal_case:
            raise ValueError(f"Legal case {legal_case_id} not found")

        if legal_case.case_type != LegalCaseType.SARFAESI:
            raise ValueError("This method is only for SARFAESI cases")

        legal_case.sarfaesi_stage = SARFAESIStage.OBJECTION_PERIOD
        legal_case.remarks = f"Objection received on {objection_date}: {objection_summary}"
        legal_case.updated_by = updated_by

        # Create notice response record
        from app.models.legal.notice import NoticeResponse

        # Get the 13(2) notice
        notice_result = await self.db.execute(
            select(LegalNotice).where(
                and_(
                    LegalNotice.legal_case_id == legal_case_id,
                    LegalNotice.notice_type == NoticeType.SARFAESI_13_2,
                )
            )
        )
        notice = notice_result.scalar_one_or_none()

        if notice:
            response = NoticeResponse(
                legal_notice_id=notice.id,
                response_date=objection_date,
                response_type="OBJECTION",
                respondent_name=respondent_name,
                respondent_type=respondent_type,
                received_mode="POST",
                received_date=objection_date,
                response_summary=objection_summary,
                is_valid_objection=True,
                objection_grounds=objection_grounds,
                document_path=document_path,
                created_by=updated_by,
            )
            self.db.add(response)

        await self.db.flush()
        return legal_case

    async def dispose_objection(
        self,
        legal_case_id: UUID,
        disposal_date: date,
        is_objection_accepted: bool,
        disposal_remarks: str,
        updated_by: Optional[UUID] = None,
    ) -> LegalCase:
        """Dispose objection under Section 13(3A).

        Must be done within 15 days of receipt of objection.
        If rejected, possession can proceed.
        """
        result = await self.db.execute(
            select(LegalCase).where(LegalCase.id == legal_case_id)
        )
        legal_case = result.scalar_one_or_none()
        if not legal_case:
            raise ValueError(f"Legal case {legal_case_id} not found")

        if is_objection_accepted:
            # Objection accepted - case may be closed or modified
            legal_case.status = LegalCaseStatus.SETTLED
            legal_case.closure_date = disposal_date
            legal_case.closure_reason = f"Objection accepted: {disposal_remarks}"
        else:
            # Objection rejected - can proceed to possession
            legal_case.sarfaesi_stage = SARFAESIStage.POSSESSION_13_4

        legal_case.remarks = f"Objection disposed on {disposal_date}: {disposal_remarks}"
        legal_case.updated_by = updated_by

        await self.db.flush()
        return legal_case

    # =========================================================================
    # Possession
    # =========================================================================

    async def take_possession(
        self,
        legal_case_id: UUID,
        possession_date: date,
        possession_type: str,  # SYMBOLIC or PHYSICAL
        security_description: str,
        security_address: str,
        authorized_officer: str,
        witnesses: Optional[List[str]] = None,
        panchnama_document_path: Optional[str] = None,
        updated_by: Optional[UUID] = None,
    ) -> LegalCase:
        """Record possession taken under Section 13(4).

        Possession can be taken after 60 days of 13(2) notice
        if no valid objection or after objection disposal.
        """
        result = await self.db.execute(
            select(LegalCase).where(LegalCase.id == legal_case_id)
        )
        legal_case = result.scalar_one_or_none()
        if not legal_case:
            raise ValueError(f"Legal case {legal_case_id} not found")

        # Verify 60 days have passed since demand notice
        if legal_case.demand_notice_date:
            days_since_notice = (possession_date - legal_case.demand_notice_date).days
            if days_since_notice < 60:
                raise ValueError(
                    f"Cannot take possession before 60 days. "
                    f"Only {days_since_notice} days have passed."
                )

        legal_case.sarfaesi_stage = SARFAESIStage.POSSESSION_13_4
        legal_case.possession_date = possession_date
        legal_case.possession_type = possession_type
        legal_case.remarks = (
            f"{possession_type} possession taken on {possession_date} "
            f"by {authorized_officer}"
        )
        legal_case.updated_by = updated_by

        # Generate possession notice
        notice = await self.notice_service.generate_notice(
            organization_id=legal_case.organization_id,
            loan_account_id=legal_case.loan_account_id,
            notice_type=NoticeType.SARFAESI_13_4_POSSESSION
            if possession_type == "SYMBOLIC"
            else NoticeType.PHYSICAL_POSSESSION,
            borrower_name="",  # Will be filled from loan account
            borrower_address=security_address,
            loan_account_number="",  # Will be filled from loan account
            principal_outstanding=legal_case.claim_principal,
            interest_outstanding=legal_case.claim_interest,
            legal_case_id=legal_case.id,
            security_description=security_description,
            security_address=security_address,
            created_by=updated_by,
        )

        # Start appeal period tracking (45 days from possession)
        period = await self.statutory_service.get_period_by_code(
            legal_case.organization_id, "SARFAESI_17_APPEAL"
        )
        if period:
            await self.statutory_service.start_period_tracking(
                organization_id=legal_case.organization_id,
                legal_case_id=legal_case.id,
                statutory_period_id=period.id,
                trigger_event="Possession taken under Section 13(4)",
                trigger_date=possession_date,
                action_required="Borrower may file appeal to DRT within 45 days",
                loan_account_id=legal_case.loan_account_id,
                created_by=updated_by,
            )

        await self.db.flush()
        return legal_case

    # =========================================================================
    # Auction
    # =========================================================================

    async def schedule_auction(
        self,
        legal_case_id: UUID,
        loan_security_id: Optional[UUID],
        property_description: str,
        property_address: str,
        market_value: Decimal,
        forced_sale_value: Decimal,
        reserve_price: Decimal,
        auction_date: date,
        auction_time: str,
        auction_venue: str,
        is_e_auction: bool = False,
        e_auction_portal: Optional[str] = None,
        emd_percent: Decimal = Decimal("10.00"),
        publication_date: Optional[date] = None,
        newspapers: Optional[str] = None,
        created_by: Optional[UUID] = None,
    ) -> PropertyAuction:
        """Schedule auction under Rule 8 & 9.

        Auction notice must be published at least 30 days before auction.
        """
        result = await self.db.execute(
            select(LegalCase).where(LegalCase.id == legal_case_id)
        )
        legal_case = result.scalar_one_or_none()
        if not legal_case:
            raise ValueError(f"Legal case {legal_case_id} not found")

        # Get auction number
        count_query = select(func.count()).where(
            PropertyAuction.legal_case_id == legal_case_id
        )
        auction_count = (await self.db.execute(count_query)).scalar() or 0

        # Generate auction reference
        auction_reference = f"{legal_case.case_reference}/AUC/{auction_count + 1:02d}"

        # Calculate EMD amount
        emd_amount = reserve_price * emd_percent / 100

        auction = PropertyAuction(
            legal_case_id=legal_case_id,
            loan_security_id=loan_security_id,
            auction_reference=auction_reference,
            auction_number=auction_count + 1,
            status=AuctionStatus.SCHEDULED,
            property_description=property_description,
            property_address=property_address,
            market_value=market_value,
            forced_sale_value=forced_sale_value,
            reserve_price=reserve_price,
            emd_amount=emd_amount,
            emd_percent=emd_percent,
            publication_date=publication_date,
            newspapers=newspapers,
            auction_date=auction_date,
            auction_time=auction_time,
            auction_venue=auction_venue,
            is_e_auction=is_e_auction,
            e_auction_portal=e_auction_portal,
            created_by=created_by,
        )
        self.db.add(auction)

        # Update case stage
        legal_case.sarfaesi_stage = SARFAESIStage.AUCTION_13_4
        legal_case.updated_by = created_by

        # Generate auction notice
        await self.notice_service.generate_notice(
            organization_id=legal_case.organization_id,
            loan_account_id=legal_case.loan_account_id,
            notice_type=NoticeType.SARFAESI_AUCTION,
            borrower_name="",
            borrower_address=property_address,
            loan_account_number="",
            principal_outstanding=legal_case.claim_principal,
            interest_outstanding=legal_case.claim_interest,
            legal_case_id=legal_case.id,
            security_description=property_description,
            security_address=property_address,
            security_value=reserve_price,
            created_by=created_by,
        )

        await self.db.flush()
        return auction

    async def record_auction_result(
        self,
        auction_id: UUID,
        status: AuctionStatus,
        number_of_bidders: int = 0,
        highest_bid: Optional[Decimal] = None,
        successful_bidder_name: Optional[str] = None,
        successful_bidder_address: Optional[str] = None,
        cancellation_reason: Optional[str] = None,
        updated_by: Optional[UUID] = None,
    ) -> PropertyAuction:
        """Record auction result."""
        result = await self.db.execute(
            select(PropertyAuction).where(PropertyAuction.id == auction_id)
        )
        auction = result.scalar_one_or_none()
        if not auction:
            raise ValueError(f"Auction {auction_id} not found")

        auction.status = status
        auction.number_of_bidders = number_of_bidders
        auction.highest_bid = highest_bid
        auction.successful_bidder_name = successful_bidder_name
        auction.successful_bidder_address = successful_bidder_address
        auction.cancellation_reason = cancellation_reason
        auction.updated_by = updated_by

        await self.db.flush()
        return auction

    async def confirm_sale(
        self,
        auction_id: UUID,
        sale_confirmation_date: date,
        sale_amount: Decimal,
        updated_by: Optional[UUID] = None,
    ) -> PropertyAuction:
        """Confirm auction sale."""
        result = await self.db.execute(
            select(PropertyAuction).where(PropertyAuction.id == auction_id)
        )
        auction = result.scalar_one_or_none()
        if not auction:
            raise ValueError(f"Auction {auction_id} not found")

        auction.sale_confirmed = True
        auction.sale_confirmation_date = sale_confirmation_date
        auction.sale_amount = sale_amount
        auction.status = AuctionStatus.COMPLETED
        auction.updated_by = updated_by

        # Update legal case
        case_result = await self.db.execute(
            select(LegalCase).where(LegalCase.id == auction.legal_case_id)
        )
        legal_case = case_result.scalar_one_or_none()
        if legal_case:
            legal_case.sarfaesi_stage = SARFAESIStage.SALE_COMPLETED
            legal_case.recovery_through_case = sale_amount
            legal_case.updated_by = updated_by

        await self.db.flush()
        return auction

    # =========================================================================
    # Timeline & Status
    # =========================================================================

    async def get_sarfaesi_timeline(
        self, legal_case_id: UUID
    ) -> Dict[str, Any]:
        """Get complete SARFAESI timeline for a case."""
        result = await self.db.execute(
            select(LegalCase)
            .options(
                selectinload(LegalCase.hearings),
                selectinload(LegalCase.auctions),
            )
            .where(LegalCase.id == legal_case_id)
        )
        legal_case = result.scalar_one_or_none()
        if not legal_case:
            raise ValueError(f"Legal case {legal_case_id} not found")

        timeline = {
            "case_reference": legal_case.case_reference,
            "current_stage": legal_case.sarfaesi_stage.value if legal_case.sarfaesi_stage else None,
            "status": legal_case.status.value if legal_case.status else None,
            "claim_amount": float(legal_case.total_claim),
            "events": [],
        }

        # Add demand notice event
        if legal_case.demand_notice_date:
            timeline["events"].append({
                "date": legal_case.demand_notice_date.isoformat(),
                "event": "Section 13(2) Demand Notice Issued",
                "stage": SARFAESIStage.DEMAND_13_2.value,
            })
            # Add response due date
            response_due = legal_case.demand_notice_date + timedelta(days=60)
            timeline["events"].append({
                "date": response_due.isoformat(),
                "event": "Response Period Ends (60 days)",
                "stage": SARFAESIStage.DEMAND_13_2.value,
            })

        # Add possession event
        if legal_case.possession_date:
            timeline["events"].append({
                "date": legal_case.possession_date.isoformat(),
                "event": f"{legal_case.possession_type or 'Symbolic'} Possession Taken",
                "stage": SARFAESIStage.POSSESSION_13_4.value,
            })

        # Add auction events
        for auction in legal_case.auctions:
            timeline["events"].append({
                "date": auction.auction_date.isoformat(),
                "event": f"Auction #{auction.auction_number} - {auction.status.value}",
                "stage": SARFAESIStage.AUCTION_13_4.value,
                "details": {
                    "reserve_price": float(auction.reserve_price),
                    "highest_bid": float(auction.highest_bid) if auction.highest_bid else None,
                    "status": auction.status.value,
                },
            })

        # Sort events by date
        timeline["events"].sort(key=lambda x: x["date"])

        return timeline

    # =========================================================================
    # Helper Methods
    # =========================================================================

    async def _generate_case_reference(self, organization_id: UUID) -> str:
        """Generate unique case reference."""
        today = date.today()
        prefix = f"SARF/{today.strftime('%Y')}"

        from sqlalchemy import func
        count_query = select(func.count()).where(
            and_(
                LegalCase.organization_id == organization_id,
                LegalCase.case_type == LegalCaseType.SARFAESI,
                LegalCase.case_reference.like(f"{prefix}%"),
            )
        )
        count = (await self.db.execute(count_query)).scalar() or 0

        return f"{prefix}/{count + 1:04d}"


# Import for count function
from sqlalchemy import func
