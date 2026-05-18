"""Credit Bureau Service.

Business logic for credit bureau operations including:
- Credit report pulls from CIBIL, Experian, Equifax
- Report caching and validity management
- Score analysis and risk assessment
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.lending.credit_pull import (
    CreditPull,
    CreditAccount,
    CreditEnquiry,
    CreditBureau,
    CreditPullType,
    CreditPullStatus,
    CreditAccountType,
    CreditAccountStatus,
    AccountOwnership,
)
from app.integrations.bureau.base import BureauConfig, CustomerInfo, BureauReport
from app.integrations.bureau.cibil import CIBILClient
from app.integrations.bureau.experian import ExperianClient
from app.integrations.bureau.parser import BureauReportParser
from app.services.core.integration_service import IntegrationService

logger = logging.getLogger(__name__)


class CreditService:
    """Service for credit bureau operations."""

    # Report validity period (days)
    REPORT_VALIDITY_DAYS = 30

    def __init__(self, db: AsyncSession):
        """Initialize credit service.

        Args:
            db: Database session
        """
        self.db = db

    async def pull_credit_report(
        self,
        organization_id: UUID,
        bureau: str,
        customer_name: str,
        pan_number: Optional[str] = None,
        aadhaar_last4: Optional[str] = None,
        mobile_number: Optional[str] = None,
        email: Optional[str] = None,
        date_of_birth: Optional[datetime] = None,
        address_line1: Optional[str] = None,
        address_line2: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        pincode: Optional[str] = None,
        pull_type: str = "SOFT",
        entity_id: Optional[UUID] = None,
        loan_application_id: Optional[UUID] = None,
        purpose: Optional[str] = None,
        user_id: Optional[UUID] = None,
        force_refresh: bool = False,
    ) -> CreditPull:
        """Pull credit report from specified bureau.

        Args:
            organization_id: Organization ID
            bureau: Bureau name (CIBIL, EXPERIAN, EQUIFAX, CRIF)
            customer_name: Customer full name
            pan_number: PAN number
            aadhaar_last4: Last 4 digits of Aadhaar
            mobile_number: Mobile number
            email: Email address
            date_of_birth: Date of birth
            address_line1: Address line 1
            address_line2: Address line 2
            city: City
            state: State
            pincode: Pincode
            pull_type: SOFT or HARD inquiry
            entity_id: Optional entity ID
            loan_application_id: Optional loan application ID
            purpose: Purpose of pull
            user_id: User initiating the pull
            force_refresh: Force new pull even if valid report exists

        Returns:
            CreditPull record with report data
        """
        bureau_enum = CreditBureau(bureau.upper())
        pull_type_enum = CreditPullType(pull_type.upper())

        # Check for existing valid report
        if not force_refresh:
            existing = await self._get_valid_report(
                organization_id, pan_number, bureau_enum
            )
            if existing:
                logger.info(f"Using cached credit report: {existing.id}")
                return existing

        # Create credit pull record
        credit_pull = CreditPull(
            organization_id=organization_id,
            entity_id=entity_id,
            loan_application_id=loan_application_id,
            bureau=bureau_enum,
            pull_type=pull_type_enum,
            customer_name=customer_name,
            pan_number=pan_number.upper() if pan_number else None,
            aadhaar_last4=aadhaar_last4,
            mobile_number=mobile_number,
            email=email,
            date_of_birth=date_of_birth.date() if date_of_birth else None,
            address_line1=address_line1,
            address_line2=address_line2,
            city=city,
            state=state,
            pincode=pincode,
            status=CreditPullStatus.PENDING,
            pulled_by=user_id,
            purpose=purpose,
        )
        self.db.add(credit_pull)
        await self.db.flush()

        # Get bureau client configuration
        try:
            config = await self._get_bureau_config(organization_id, bureau_enum)
            client = self._get_bureau_client(bureau_enum, config)

            # Build customer info
            customer = CustomerInfo(
                name=customer_name,
                pan=pan_number,
                aadhaar_last4=aadhaar_last4,
                mobile=mobile_number,
                email=email,
                date_of_birth=date_of_birth.date() if date_of_birth else None,
                address_line1=address_line1,
                address_line2=address_line2,
                city=city,
                state=state,
                pincode=pincode,
            )

            # Update status
            credit_pull.status = CreditPullStatus.IN_PROGRESS
            await self.db.flush()

            # Pull report
            report = await client.pull_report(
                customer=customer,
                inquiry_type=pull_type,
                purpose=purpose or "ACCOUNT_REVIEW",
            )

            # Update credit pull with results
            await self._update_from_report(credit_pull, report)

            await client.close()

        except Exception as e:
            logger.error(f"Credit pull failed: {e}")
            credit_pull.status = CreditPullStatus.FAILED
            credit_pull.error_code = "PULL_FAILED"
            credit_pull.error_message = str(e)

        await self.db.flush()
        await self.db.refresh(credit_pull)

        return credit_pull

    async def get_credit_pull(self, pull_id: UUID) -> Optional[CreditPull]:
        """Get credit pull by ID with full details.

        Args:
            pull_id: Credit pull ID

        Returns:
            Credit pull with accounts and enquiries
        """
        query = (
            select(CreditPull)
            .options(
                selectinload(CreditPull.accounts),
                selectinload(CreditPull.enquiries),
            )
            .where(CreditPull.id == pull_id)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_credit_pulls(
        self,
        organization_id: UUID,
        entity_id: Optional[UUID] = None,
        loan_application_id: Optional[UUID] = None,
        bureau: Optional[str] = None,
        status: Optional[str] = None,
        pan_number: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """List credit pulls with filtering.

        Args:
            organization_id: Organization ID
            entity_id: Filter by entity
            loan_application_id: Filter by loan application
            bureau: Filter by bureau
            status: Filter by status
            pan_number: Filter by PAN
            page: Page number
            page_size: Items per page

        Returns:
            Paginated list of credit pulls
        """
        query = (
            select(CreditPull)
            .where(CreditPull.organization_id == organization_id)
            .order_by(desc(CreditPull.created_at))
        )

        if entity_id:
            query = query.where(CreditPull.entity_id == entity_id)
        if loan_application_id:
            query = query.where(CreditPull.loan_application_id == loan_application_id)
        if bureau:
            query = query.where(CreditPull.bureau == CreditBureau(bureau.upper()))
        if status:
            query = query.where(CreditPull.status == CreditPullStatus(status.upper()))
        if pan_number:
            query = query.where(CreditPull.pan_number == pan_number.upper())

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar()

        # Paginate
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        items = result.scalars().all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    async def get_latest_score(
        self,
        organization_id: UUID,
        entity_id: Optional[UUID] = None,
        pan_number: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Get latest credit score for entity or PAN.

        Args:
            organization_id: Organization ID
            entity_id: Entity ID
            pan_number: PAN number

        Returns:
            Latest score information
        """
        query = (
            select(CreditPull)
            .where(
                and_(
                    CreditPull.organization_id == organization_id,
                    CreditPull.status == CreditPullStatus.SUCCESS,
                    CreditPull.credit_score.isnot(None),
                )
            )
            .order_by(desc(CreditPull.pulled_at))
        )

        if entity_id:
            query = query.where(CreditPull.entity_id == entity_id)
        elif pan_number:
            query = query.where(CreditPull.pan_number == pan_number.upper())
        else:
            return None

        result = await self.db.execute(query.limit(1))
        pull = result.scalar_one_or_none()

        if not pull:
            return None

        return {
            "credit_score": pull.credit_score,
            "score_band": BureauReportParser.get_score_band(pull.credit_score),
            "score_date": pull.score_date,
            "bureau": pull.bureau.value,
            "pull_id": pull.id,
            "is_valid": pull.is_valid(),
        }

    async def get_credit_summary(
        self,
        organization_id: UUID,
        entity_id: Optional[UUID] = None,
        loan_application_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """Get credit summary for entity or application.

        Args:
            organization_id: Organization ID
            entity_id: Entity ID
            loan_application_id: Loan application ID

        Returns:
            Credit summary
        """
        query = (
            select(CreditPull)
            .where(CreditPull.organization_id == organization_id)
        )

        if entity_id:
            query = query.where(CreditPull.entity_id == entity_id)
        elif loan_application_id:
            query = query.where(CreditPull.loan_application_id == loan_application_id)
        else:
            return {"total_pulls": 0}

        result = await self.db.execute(query)
        pulls = result.scalars().all()

        if not pulls:
            return {
                "entity_id": entity_id,
                "loan_application_id": loan_application_id,
                "total_pulls": 0,
                "has_valid_report": False,
            }

        # Get latest successful pull
        successful = [p for p in pulls if p.status == CreditPullStatus.SUCCESS]
        latest = max(successful, key=lambda p: p.pulled_at) if successful else None

        # Count by bureau
        by_bureau = {}
        for pull in pulls:
            bureau = pull.bureau.value
            by_bureau[bureau] = by_bureau.get(bureau, 0) + 1

        return {
            "entity_id": entity_id,
            "loan_application_id": loan_application_id,
            "total_pulls": len(pulls),
            "latest_score": latest.credit_score if latest else None,
            "latest_score_date": latest.score_date if latest else None,
            "latest_bureau": latest.bureau.value if latest else None,
            "score_band": BureauReportParser.get_score_band(latest.credit_score) if latest else None,
            "pulls_by_bureau": by_bureau,
            "has_valid_report": any(p.is_valid() for p in successful),
        }

    async def analyze_report(self, pull_id: UUID) -> Dict[str, Any]:
        """Analyze credit report in detail.

        Args:
            pull_id: Credit pull ID

        Returns:
            Detailed analysis
        """
        pull = await self.get_credit_pull(pull_id)
        if not pull:
            raise ValueError("Credit pull not found")

        if pull.status != CreditPullStatus.SUCCESS:
            return {
                "pull_id": pull_id,
                "status": pull.status.value,
                "error": pull.error_message,
            }

        # Build report object for parser
        report = BureauReport(
            bureau=pull.bureau.value,
            credit_score=pull.credit_score,
            score_version=pull.score_version,
            score_date=pull.score_date,
            total_accounts=pull.total_accounts or 0,
            active_accounts=pull.active_accounts or 0,
            total_sanctioned=pull.total_sanctioned or Decimal("0"),
            total_outstanding=pull.total_outstanding or Decimal("0"),
            total_overdue=pull.total_overdue or Decimal("0"),
            max_dpd_last_12m=pull.max_dpd_last_12m or 0,
            max_dpd_last_24m=pull.max_dpd_last_24m or 0,
            enquiries_last_30d=pull.enquiries_last_30d or 0,
            enquiries_last_12m=pull.enquiries_last_12m or 0,
        )

        # Convert accounts
        for acc in pull.accounts:
            report.accounts.append(self._convert_account_to_base(acc))

        # Convert enquiries
        for enq in pull.enquiries:
            report.enquiries.append(self._convert_enquiry_to_base(enq))

        # Generate analysis
        return BureauReportParser.generate_summary(report)

    async def get_statistics(
        self,
        organization_id: UUID,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get credit bureau usage statistics.

        Args:
            organization_id: Organization ID
            from_date: Start date filter
            to_date: End date filter

        Returns:
            Statistics summary
        """
        query = select(CreditPull).where(
            CreditPull.organization_id == organization_id
        )

        if from_date:
            query = query.where(CreditPull.created_at >= from_date)
        if to_date:
            query = query.where(CreditPull.created_at <= to_date)

        result = await self.db.execute(query)
        pulls = result.scalars().all()

        if not pulls:
            return {
                "total_pulls": 0,
                "successful_pulls": 0,
                "failed_pulls": 0,
                "pulls_by_bureau": {},
                "pulls_by_status": {},
            }

        # Calculate stats
        by_bureau: Dict[str, int] = {}
        by_status: Dict[str, int] = {}
        scores = []

        for pull in pulls:
            bureau = pull.bureau.value
            status = pull.status.value
            by_bureau[bureau] = by_bureau.get(bureau, 0) + 1
            by_status[status] = by_status.get(status, 0) + 1
            if pull.credit_score:
                scores.append(pull.credit_score)

        # Score distribution
        score_dist = {
            "EXCELLENT": 0,
            "GOOD": 0,
            "FAIR": 0,
            "POOR": 0,
            "VERY_POOR": 0,
        }
        for score in scores:
            band = BureauReportParser.get_score_band(score)
            if band in score_dist:
                score_dist[band] += 1

        return {
            "total_pulls": len(pulls),
            "successful_pulls": by_status.get("SUCCESS", 0),
            "failed_pulls": by_status.get("FAILED", 0),
            "no_hit_pulls": by_status.get("NO_HIT", 0),
            "pulls_by_bureau": by_bureau,
            "pulls_by_status": by_status,
            "average_score": sum(scores) / len(scores) if scores else None,
            "score_distribution": score_dist,
        }

    async def _get_valid_report(
        self,
        organization_id: UUID,
        pan_number: Optional[str],
        bureau: CreditBureau,
    ) -> Optional[CreditPull]:
        """Get existing valid report for customer.

        Args:
            organization_id: Organization ID
            pan_number: PAN number
            bureau: Bureau

        Returns:
            Valid credit pull if exists
        """
        if not pan_number:
            return None

        validity_cutoff = datetime.utcnow() - timedelta(days=self.REPORT_VALIDITY_DAYS)

        query = (
            select(CreditPull)
            .options(
                selectinload(CreditPull.accounts),
                selectinload(CreditPull.enquiries),
            )
            .where(
                and_(
                    CreditPull.organization_id == organization_id,
                    CreditPull.pan_number == pan_number.upper(),
                    CreditPull.bureau == bureau,
                    CreditPull.status == CreditPullStatus.SUCCESS,
                    CreditPull.pulled_at >= validity_cutoff,
                )
            )
            .order_by(desc(CreditPull.pulled_at))
            .limit(1)
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _get_bureau_config(
        self,
        organization_id: UUID,
        bureau: CreditBureau,
    ) -> BureauConfig:
        """Get bureau configuration from integration settings.

        Args:
            organization_id: Organization ID
            bureau: Bureau

        Returns:
            Bureau configuration
        """
        integration_service = IntegrationService(self.db)

        # Map bureau to integration type
        provider_map = {
            CreditBureau.CIBIL: "CIBIL",
            CreditBureau.EXPERIAN: "EXPERIAN",
            CreditBureau.EQUIFAX: "EQUIFAX",
            CreditBureau.CRIF: "CRIF",
        }

        config = await integration_service.get_by_type(
            organization_id=organization_id,
            integration_type="CREDIT_BUREAU",
            provider=provider_map[bureau],
        )

        if not config:
            raise ValueError(f"No {bureau.value} integration configured")

        config_data = config.get_decrypted_config()

        return BureauConfig(
            member_id=config_data.get("member_id", ""),
            password=config_data.get("password", ""),
            api_key=config_data.get("api_key"),
            secret_key=config_data.get("secret_key"),
            base_url=config.base_url or "",
            sandbox_url=config.sandbox_url,
            sandbox_mode=config.sandbox_mode,
        )

    def _get_bureau_client(
        self,
        bureau: CreditBureau,
        config: BureauConfig,
    ):
        """Get bureau client instance.

        Args:
            bureau: Bureau
            config: Bureau configuration

        Returns:
            Bureau client
        """
        clients = {
            CreditBureau.CIBIL: CIBILClient,
            CreditBureau.EXPERIAN: ExperianClient,
        }

        client_class = clients.get(bureau)
        if not client_class:
            raise ValueError(f"No client available for {bureau.value}")

        return client_class(config)

    async def _update_from_report(
        self,
        credit_pull: CreditPull,
        report: BureauReport,
    ):
        """Update credit pull record from bureau report.

        Args:
            credit_pull: Credit pull record
            report: Bureau report
        """
        credit_pull.request_reference = report.request_reference
        credit_pull.bureau_reference = report.bureau_reference

        if report.success:
            credit_pull.status = CreditPullStatus.SUCCESS
            credit_pull.credit_score = report.credit_score
            credit_pull.score_version = report.score_version
            credit_pull.score_date = report.score_date
            credit_pull.total_accounts = report.total_accounts
            credit_pull.active_accounts = report.active_accounts
            credit_pull.total_sanctioned = report.total_sanctioned
            credit_pull.total_outstanding = report.total_outstanding
            credit_pull.total_overdue = report.total_overdue
            credit_pull.max_dpd_last_12m = report.max_dpd_last_12m
            credit_pull.max_dpd_last_24m = report.max_dpd_last_24m
            credit_pull.enquiries_last_30d = report.enquiries_last_30d
            credit_pull.enquiries_last_12m = report.enquiries_last_12m
            credit_pull.report_data = report.raw_response
            credit_pull.report_xml = report.raw_xml
            credit_pull.pulled_at = datetime.utcnow()
            credit_pull.expires_at = datetime.utcnow() + timedelta(days=self.REPORT_VALIDITY_DAYS)

            # Add accounts
            for acc in report.accounts:
                credit_account = CreditAccount(
                    credit_pull_id=credit_pull.id,
                    account_number_masked=acc.account_number_masked,
                    bureau_account_id=acc.bureau_account_id,
                    institution_name=acc.institution_name,
                    institution_type=acc.institution_type,
                    account_type=CreditAccountType(acc.account_type),
                    account_status=CreditAccountStatus(acc.account_status),
                    ownership=AccountOwnership(acc.ownership),
                    sanctioned_amount=acc.sanctioned_amount,
                    current_balance=acc.current_balance,
                    overdue_amount=acc.overdue_amount,
                    emi_amount=acc.emi_amount,
                    credit_limit=acc.credit_limit,
                    high_credit=acc.high_credit,
                    write_off_amount=acc.write_off_amount,
                    opened_date=acc.opened_date,
                    closed_date=acc.closed_date,
                    last_payment_date=acc.last_payment_date,
                    reported_date=acc.reported_date,
                    tenure_months=acc.tenure_months,
                    remaining_tenure=acc.remaining_tenure,
                    dpd_history=acc.dpd_history,
                    max_dpd=acc.max_dpd,
                    is_secured=acc.is_secured,
                    has_dispute=acc.has_dispute,
                    raw_data=acc.raw_data,
                )
                self.db.add(credit_account)

            # Add enquiries
            for enq in report.enquiries:
                credit_enquiry = CreditEnquiry(
                    credit_pull_id=credit_pull.id,
                    enquiry_date=enq.enquiry_date,
                    institution_name=enq.institution_name,
                    enquiry_purpose=enq.enquiry_purpose,
                    enquiry_amount=enq.enquiry_amount,
                    raw_data=enq.raw_data,
                )
                self.db.add(credit_enquiry)

        elif report.error_code == "NO_HIT":
            credit_pull.status = CreditPullStatus.NO_HIT
            credit_pull.error_code = report.error_code
            credit_pull.error_message = report.error_message
            credit_pull.pulled_at = datetime.utcnow()
        else:
            credit_pull.status = CreditPullStatus.FAILED
            credit_pull.error_code = report.error_code
            credit_pull.error_message = report.error_message

    def _convert_account_to_base(self, acc: CreditAccount):
        """Convert database account to base account type."""
        from app.integrations.bureau.base import CreditAccount as BaseAccount
        return BaseAccount(
            account_number_masked=acc.account_number_masked,
            bureau_account_id=acc.bureau_account_id,
            institution_name=acc.institution_name,
            institution_type=acc.institution_type,
            account_type=acc.account_type.value,
            account_status=acc.account_status.value,
            ownership=acc.ownership.value,
            sanctioned_amount=acc.sanctioned_amount,
            current_balance=acc.current_balance,
            overdue_amount=acc.overdue_amount,
            emi_amount=acc.emi_amount,
            credit_limit=acc.credit_limit,
            high_credit=acc.high_credit,
            write_off_amount=acc.write_off_amount,
            opened_date=acc.opened_date,
            closed_date=acc.closed_date,
            last_payment_date=acc.last_payment_date,
            reported_date=acc.reported_date,
            tenure_months=acc.tenure_months,
            remaining_tenure=acc.remaining_tenure,
            dpd_history=acc.dpd_history,
            max_dpd=acc.max_dpd,
            is_secured=acc.is_secured,
            has_dispute=acc.has_dispute,
        )

    def _convert_enquiry_to_base(self, enq: CreditEnquiry):
        """Convert database enquiry to base enquiry type."""
        from app.integrations.bureau.base import CreditEnquiry as BaseEnquiry
        return BaseEnquiry(
            enquiry_date=enq.enquiry_date,
            institution_name=enq.institution_name,
            enquiry_purpose=enq.enquiry_purpose,
            enquiry_amount=enq.enquiry_amount,
        )
