"""Notice Generation Service.

Provides business logic for generating, tracking, and managing
legal notices as per Indian legal requirements.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.legal.notice import (
    NoticeTemplate,
    LegalNotice,
    NoticeDelivery,
    NoticeResponse,
)
from app.models.legal.enums import (
    NoticeType,
    NoticeStatus,
    DeliveryMode,
    DeliveryStatus,
)


class NoticeService:
    """Service for managing legal notices."""

    # Statutory periods for different notice types (in days)
    STATUTORY_PERIODS = {
        NoticeType.SARFAESI_13_2: 60,
        NoticeType.SARFAESI_13_4_POSSESSION: 15,
        NoticeType.SARFAESI_AUCTION: 30,
        NoticeType.NI_ACT_138: 15,
        NoticeType.DRT_DEMAND: 30,
        NoticeType.RECALL_NOTICE: 7,
        NoticeType.ARBITRATION: 30,
        NoticeType.LOK_ADALAT: 15,
        NoticeType.FINAL_DEMAND: 15,
        NoticeType.SYMBOLIC_POSSESSION: 15,
        NoticeType.PHYSICAL_POSSESSION: 15,
        NoticeType.SALE_CONFIRMATION: 15,
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Template Management
    # =========================================================================

    async def create_template(
        self,
        organization_id: UUID,
        template_code: str,
        template_name: str,
        notice_type: NoticeType,
        act_reference: str,
        statutory_period_days: int,
        template_content: str,
        section_reference: Optional[str] = None,
        response_period_days: Optional[int] = None,
        template_format: str = "HTML",
        placeholders: Optional[List[str]] = None,
        language: str = "ENGLISH",
        is_default: bool = False,
        created_by: Optional[UUID] = None,
    ) -> NoticeTemplate:
        """Create a new notice template."""
        template = NoticeTemplate(
            organization_id=organization_id,
            template_code=template_code,
            template_name=template_name,
            notice_type=notice_type,
            act_reference=act_reference,
            section_reference=section_reference,
            statutory_period_days=statutory_period_days,
            response_period_days=response_period_days,
            template_content=template_content,
            template_format=template_format,
            placeholders={"items": placeholders} if placeholders else None,
            language=language,
            is_default=is_default,
            created_by=created_by,
        )
        self.db.add(template)
        await self.db.flush()
        return template

    async def get_template(self, template_id: UUID) -> Optional[NoticeTemplate]:
        """Get template by ID."""
        result = await self.db.execute(
            select(NoticeTemplate).where(NoticeTemplate.id == template_id)
        )
        return result.scalar_one_or_none()

    async def get_default_template(
        self,
        organization_id: UUID,
        notice_type: NoticeType,
        language: str = "ENGLISH",
    ) -> Optional[NoticeTemplate]:
        """Get default template for a notice type."""
        result = await self.db.execute(
            select(NoticeTemplate).where(
                and_(
                    NoticeTemplate.organization_id == organization_id,
                    NoticeTemplate.notice_type == notice_type,
                    NoticeTemplate.language == language,
                    NoticeTemplate.is_active == True,
                    NoticeTemplate.is_default == True,
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_templates(
        self,
        organization_id: UUID,
        notice_type: Optional[NoticeType] = None,
        language: Optional[str] = None,
    ) -> List[NoticeTemplate]:
        """List notice templates."""
        query = select(NoticeTemplate).where(
            and_(
                NoticeTemplate.organization_id == organization_id,
                NoticeTemplate.is_active == True,
            )
        )

        if notice_type:
            query = query.where(NoticeTemplate.notice_type == notice_type)
        if language:
            query = query.where(NoticeTemplate.language == language)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    # =========================================================================
    # Notice Generation
    # =========================================================================

    async def generate_notice(
        self,
        organization_id: UUID,
        loan_account_id: UUID,
        notice_type: NoticeType,
        borrower_name: str,
        borrower_address: str,
        loan_account_number: str,
        principal_outstanding: Decimal,
        interest_outstanding: Decimal,
        template_id: Optional[UUID] = None,
        legal_case_id: Optional[UUID] = None,
        notice_date: Optional[date] = None,
        penal_outstanding: Decimal = Decimal("0"),
        other_charges: Decimal = Decimal("0"),
        co_borrower_names: Optional[str] = None,
        guarantor_names: Optional[str] = None,
        security_description: Optional[str] = None,
        security_address: Optional[str] = None,
        security_value: Optional[Decimal] = None,
        future_interest_rate: Optional[Decimal] = None,
        language: str = "ENGLISH",
        created_by: Optional[UUID] = None,
    ) -> LegalNotice:
        """Generate a new legal notice."""
        # Get template if not provided
        if not template_id:
            template = await self.get_default_template(
                organization_id, notice_type, language
            )
            if template:
                template_id = template.id

        # Determine statutory period
        statutory_days = self.STATUTORY_PERIODS.get(notice_type, 30)

        # Calculate dates
        actual_notice_date = notice_date or date.today()
        response_due = self.calculate_statutory_deadline(
            notice_type, actual_notice_date
        )

        # Calculate total amount
        total_amount = (
            principal_outstanding + interest_outstanding + penal_outstanding + other_charges
        )

        # Get act reference
        act_reference = self._get_act_reference(notice_type)

        # Generate notice number
        notice_number = await self._generate_notice_number(organization_id)

        # Generate notice content (placeholder for actual template rendering)
        notice_content = await self._render_notice_content(
            template_id=template_id,
            borrower_name=borrower_name,
            borrower_address=borrower_address,
            loan_account_number=loan_account_number,
            total_amount=total_amount,
            notice_date=actual_notice_date,
            response_due=response_due,
        )

        notice = LegalNotice(
            organization_id=organization_id,
            loan_account_id=loan_account_id,
            legal_case_id=legal_case_id,
            template_id=template_id,
            notice_number=notice_number,
            notice_type=notice_type,
            status=NoticeStatus.DRAFT,
            notice_date=actual_notice_date,
            statutory_period_days=statutory_days,
            response_due_date=response_due,
            borrower_name=borrower_name,
            borrower_address=borrower_address,
            co_borrower_names=co_borrower_names,
            guarantor_names=guarantor_names,
            loan_account_number=loan_account_number,
            principal_outstanding=principal_outstanding,
            interest_outstanding=interest_outstanding,
            penal_outstanding=penal_outstanding,
            other_charges=other_charges,
            total_amount_demanded=total_amount,
            future_interest_rate=future_interest_rate,
            security_description=security_description,
            security_address=security_address,
            security_value=security_value,
            act_reference=act_reference,
            notice_content=notice_content,
            language=language,
            created_by=created_by,
        )
        self.db.add(notice)
        await self.db.flush()
        return notice

    async def approve_notice(
        self,
        notice_id: UUID,
        approved_by_id: UUID,
        approved_by_name: str,
    ) -> LegalNotice:
        """Approve a notice for dispatch."""
        result = await self.db.execute(
            select(LegalNotice).where(LegalNotice.id == notice_id)
        )
        notice = result.scalar_one_or_none()
        if not notice:
            raise ValueError(f"Notice {notice_id} not found")

        if notice.status not in [NoticeStatus.DRAFT, NoticeStatus.GENERATED]:
            raise ValueError(f"Notice cannot be approved in {notice.status} status")

        notice.status = NoticeStatus.APPROVED
        notice.approved_by_id = approved_by_id
        notice.approved_by_name = approved_by_name
        notice.approval_date = datetime.utcnow()

        await self.db.flush()
        return notice

    def calculate_statutory_deadline(
        self, notice_type: NoticeType, start_date: date
    ) -> date:
        """Calculate statutory deadline based on notice type."""
        days = self.STATUTORY_PERIODS.get(notice_type, 30)
        return start_date + timedelta(days=days)

    # =========================================================================
    # Delivery Tracking
    # =========================================================================

    async def record_dispatch(
        self,
        notice_id: UUID,
        delivery_mode: DeliveryMode,
        recipient_name: str,
        delivery_address: str,
        recipient_type: str = "BORROWER",
        dispatch_date: Optional[date] = None,
        tracking_number: Optional[str] = None,
        courier_name: Optional[str] = None,
        dispatched_by: Optional[str] = None,
        delivery_cost: Optional[Decimal] = None,
        created_by: Optional[UUID] = None,
    ) -> NoticeDelivery:
        """Record dispatch of a notice."""
        # Update notice status
        result = await self.db.execute(
            select(LegalNotice).where(LegalNotice.id == notice_id)
        )
        notice = result.scalar_one_or_none()
        if not notice:
            raise ValueError(f"Notice {notice_id} not found")

        if notice.status == NoticeStatus.DRAFT:
            raise ValueError("Notice must be approved before dispatch")

        notice.status = NoticeStatus.DISPATCHED

        # Get delivery attempt number
        count_query = select(func.count()).where(
            and_(
                NoticeDelivery.legal_notice_id == notice_id,
                NoticeDelivery.recipient_name == recipient_name,
                NoticeDelivery.delivery_mode == delivery_mode,
            )
        )
        attempt = (await self.db.execute(count_query)).scalar() or 0

        delivery = NoticeDelivery(
            legal_notice_id=notice_id,
            delivery_mode=delivery_mode,
            delivery_attempt=attempt + 1,
            delivery_status=DeliveryStatus.DISPATCHED,
            recipient_name=recipient_name,
            recipient_type=recipient_type,
            delivery_address=delivery_address,
            dispatch_date=dispatch_date or date.today(),
            dispatched_by=dispatched_by,
            tracking_number=tracking_number,
            courier_name=courier_name,
            delivery_cost=delivery_cost,
            created_by=created_by,
        )
        self.db.add(delivery)
        await self.db.flush()
        return delivery

    async def update_delivery_status(
        self,
        delivery_id: UUID,
        delivery_status: DeliveryStatus,
        delivery_date: Optional[date] = None,
        received_by: Optional[str] = None,
        relationship_to_borrower: Optional[str] = None,
        pod_document_path: Optional[str] = None,
        return_date: Optional[date] = None,
        return_reason: Optional[str] = None,
        updated_by: Optional[UUID] = None,
    ) -> NoticeDelivery:
        """Update delivery status."""
        result = await self.db.execute(
            select(NoticeDelivery).where(NoticeDelivery.id == delivery_id)
        )
        delivery = result.scalar_one_or_none()
        if not delivery:
            raise ValueError(f"Delivery {delivery_id} not found")

        delivery.delivery_status = delivery_status
        delivery.updated_by = updated_by

        if delivery_status == DeliveryStatus.DELIVERED:
            delivery.delivery_date = delivery_date or date.today()
            delivery.received_by = received_by
            delivery.relationship_to_borrower = relationship_to_borrower
            delivery.pod_document_path = pod_document_path

            # Update notice status
            notice_result = await self.db.execute(
                select(LegalNotice).where(LegalNotice.id == delivery.legal_notice_id)
            )
            notice = notice_result.scalar_one_or_none()
            if notice:
                notice.status = NoticeStatus.DELIVERED

        elif delivery_status in [
            DeliveryStatus.RETURNED_UNDELIVERED,
            DeliveryStatus.REFUSED,
            DeliveryStatus.UNCLAIMED,
        ]:
            delivery.return_date = return_date or date.today()
            delivery.return_reason = return_reason

            # Update notice status
            notice_result = await self.db.execute(
                select(LegalNotice).where(LegalNotice.id == delivery.legal_notice_id)
            )
            notice = notice_result.scalar_one_or_none()
            if notice:
                notice.status = NoticeStatus.RETURNED

        await self.db.flush()
        return delivery

    # =========================================================================
    # Notice Queries
    # =========================================================================

    async def get_notice(self, notice_id: UUID) -> Optional[LegalNotice]:
        """Get notice by ID with related data."""
        result = await self.db.execute(
            select(LegalNotice)
            .options(
                selectinload(LegalNotice.deliveries),
                selectinload(LegalNotice.responses),
            )
            .where(LegalNotice.id == notice_id)
        )
        return result.scalar_one_or_none()

    async def list_notices(
        self,
        organization_id: UUID,
        loan_account_id: Optional[UUID] = None,
        legal_case_id: Optional[UUID] = None,
        notice_type: Optional[NoticeType] = None,
        status: Optional[NoticeStatus] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[LegalNotice], int]:
        """List notices with filtering and pagination."""
        query = select(LegalNotice).where(
            and_(
                LegalNotice.organization_id == organization_id,
                LegalNotice.is_active == True,
            )
        )

        if loan_account_id:
            query = query.where(LegalNotice.loan_account_id == loan_account_id)
        if legal_case_id:
            query = query.where(LegalNotice.legal_case_id == legal_case_id)
        if notice_type:
            query = query.where(LegalNotice.notice_type == notice_type)
        if status:
            query = query.where(LegalNotice.status == status)
        if from_date:
            query = query.where(LegalNotice.notice_date >= from_date)
        if to_date:
            query = query.where(LegalNotice.notice_date <= to_date)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Apply pagination and ordering
        query = query.order_by(LegalNotice.notice_date.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_overdue_notices(
        self,
        organization_id: UUID,
        as_of_date: Optional[date] = None,
    ) -> List[LegalNotice]:
        """Get notices that are past their statutory deadline without response."""
        check_date = as_of_date or date.today()

        result = await self.db.execute(
            select(LegalNotice)
            .where(
                and_(
                    LegalNotice.organization_id == organization_id,
                    LegalNotice.is_active == True,
                    LegalNotice.status.in_([
                        NoticeStatus.DISPATCHED,
                        NoticeStatus.DELIVERED,
                    ]),
                    LegalNotice.response_due_date < check_date,
                )
            )
            .order_by(LegalNotice.response_due_date)
        )
        return list(result.scalars().all())

    # =========================================================================
    # Helper Methods
    # =========================================================================

    async def _generate_notice_number(self, organization_id: UUID) -> str:
        """Generate unique notice number."""
        today = date.today()
        prefix = f"NTC/{today.strftime('%Y%m')}"

        # Get count of notices this month
        count_query = select(func.count()).where(
            and_(
                LegalNotice.organization_id == organization_id,
                LegalNotice.notice_number.like(f"{prefix}%"),
            )
        )
        count = (await self.db.execute(count_query)).scalar() or 0

        return f"{prefix}/{count + 1:04d}"

    def _get_act_reference(self, notice_type: NoticeType) -> str:
        """Get act reference for notice type."""
        references = {
            NoticeType.SARFAESI_13_2: "SARFAESI Act 2002, Section 13(2)",
            NoticeType.SARFAESI_13_4_POSSESSION: "SARFAESI Act 2002, Section 13(4)",
            NoticeType.SARFAESI_AUCTION: "Security Interest (Enforcement) Rules 2002, Rule 8 & 9",
            NoticeType.NI_ACT_138: "Negotiable Instruments Act 1881, Section 138",
            NoticeType.DRT_DEMAND: "Recovery of Debts and Bankruptcy Act 1993, Section 25",
            NoticeType.ARBITRATION: "Arbitration and Conciliation Act 1996, Section 21",
            NoticeType.LOK_ADALAT: "Legal Services Authorities Act 1987, Section 20",
        }
        return references.get(notice_type, "General Demand Notice")

    async def _render_notice_content(
        self,
        template_id: Optional[UUID],
        borrower_name: str,
        borrower_address: str,
        loan_account_number: str,
        total_amount: Decimal,
        notice_date: date,
        response_due: date,
    ) -> str:
        """Render notice content from template."""
        # TODO: Implement actual template rendering with Jinja2
        # This is a placeholder implementation
        return f"""
LEGAL NOTICE

Date: {notice_date.strftime('%d/%m/%Y')}

To,
{borrower_name}
{borrower_address}

Subject: Notice demanding payment of outstanding dues

Dear Sir/Madam,

We hereby demand payment of Rs. {total_amount:,.2f} (Rupees {self._amount_in_words(total_amount)} only)
outstanding against Loan Account No. {loan_account_number}.

You are required to pay the above amount within the statutory period, failing which
legal action will be initiated against you without further notice.

Due Date: {response_due.strftime('%d/%m/%Y')}

This notice is issued without prejudice to our rights and remedies under law.

For and on behalf of [Company Name]
Authorized Signatory
"""

    def _amount_in_words(self, amount: Decimal) -> str:
        """Convert amount to words (placeholder)."""
        # TODO: Implement proper Indian number to words conversion
        return f"{amount:,.2f}"
