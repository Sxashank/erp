"""Statutory Period Calculator Service.

Provides business logic for tracking limitation periods
and statutory deadlines under Indian law.
"""

from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.legal.statutory_period import (
    StatutoryPeriod,
    PeriodTracking,
    LimitationAlert,
)
from app.models.legal.enums import AlertPriority
from app.models.lending.enums import LegalCaseType, LegalForumType


class StatutoryService:
    """Service for managing statutory periods and limitations."""

    # Standard limitation periods under Indian law
    STANDARD_PERIODS = {
        # SARFAESI Act 2002
        "SARFAESI_13_2": {
            "days": 60,
            "act": "SARFAESI Act 2002",
            "section": "Section 13(2)",
            "start_event": "Date of notice receipt",
            "consequence": "Borrower must respond within 60 days",
        },
        "SARFAESI_13_3A": {
            "days": 45,
            "act": "SARFAESI Act 2002",
            "section": "Section 13(3A)",
            "start_event": "After 60 days of Section 13(2) notice",
            "consequence": "Bank must consider objection within 45 days",
        },
        "SARFAESI_17_APPEAL": {
            "days": 45,
            "act": "SARFAESI Act 2002",
            "section": "Section 17",
            "start_event": "Date of possession/measure taken",
            "consequence": "Time-barred if not filed within 45 days",
        },
        # DRT Act
        "DRT_APPLICATION": {
            "years": 3,
            "act": "Limitation Act 1963",
            "section": "Article 137",
            "start_event": "Date of cause of action (default)",
            "consequence": "Application becomes time-barred",
        },
        # Negotiable Instruments Act
        "NI_ACT_138": {
            "days": 30,
            "act": "Negotiable Instruments Act 1881",
            "section": "Section 138/142",
            "start_event": "Date of receipt of cheque return memo",
            "consequence": "Complaint must be filed within 30 days of cause of action",
        },
        # Execution
        "EXECUTION_PETITION": {
            "years": 12,
            "act": "Limitation Act 1963",
            "section": "Article 136",
            "start_event": "Date of decree",
            "consequence": "Decree becomes unenforceable",
        },
        # IBC
        "IBC_APPLICATION": {
            "days": 14,
            "act": "Insolvency and Bankruptcy Code 2016",
            "section": "Section 7/9",
            "start_event": "Date of NCLT admission",
            "consequence": "CIRP proceedings timeline",
        },
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Statutory Period Masters
    # =========================================================================

    async def create_statutory_period(
        self,
        organization_id: UUID,
        provision_code: str,
        provision_name: str,
        act_name: str,
        section_reference: str,
        period_days: int,
        start_event: str,
        consequence: str,
        period_months: Optional[int] = None,
        period_years: Optional[int] = None,
        includes_holidays: bool = True,
        extension_allowed: bool = False,
        extension_grounds: Optional[str] = None,
        applicable_forums: Optional[List[str]] = None,
        applicable_case_types: Optional[List[str]] = None,
        alert_before_days: Optional[List[int]] = None,
        created_by: Optional[UUID] = None,
    ) -> StatutoryPeriod:
        """Create a new statutory period definition."""
        # Calculate period description
        parts = []
        if period_years:
            parts.append(f"{period_years} year{'s' if period_years > 1 else ''}")
        if period_months:
            parts.append(f"{period_months} month{'s' if period_months > 1 else ''}")
        if period_days:
            parts.append(f"{period_days} day{'s' if period_days > 1 else ''}")
        period_description = " ".join(parts) if parts else f"{period_days} days"

        period = StatutoryPeriod(
            organization_id=organization_id,
            provision_code=provision_code,
            provision_name=provision_name,
            act_name=act_name,
            section_reference=section_reference,
            period_days=period_days,
            period_months=period_months,
            period_years=period_years,
            period_description=period_description,
            start_event=start_event,
            includes_holidays=includes_holidays,
            extension_allowed=extension_allowed,
            extension_grounds=extension_grounds,
            consequence=consequence,
            applicable_forums={"items": applicable_forums} if applicable_forums else None,
            applicable_case_types={"items": applicable_case_types} if applicable_case_types else None,
            alert_before_days={"days": alert_before_days or [30, 15, 7, 1]},
            created_by=created_by,
        )
        self.db.add(period)
        await self.db.flush()
        return period

    async def get_statutory_period(
        self, period_id: UUID
    ) -> Optional[StatutoryPeriod]:
        """Get statutory period by ID."""
        result = await self.db.execute(
            select(StatutoryPeriod).where(StatutoryPeriod.id == period_id)
        )
        return result.scalar_one_or_none()

    async def get_period_by_code(
        self, organization_id: UUID, provision_code: str
    ) -> Optional[StatutoryPeriod]:
        """Get statutory period by provision code."""
        result = await self.db.execute(
            select(StatutoryPeriod).where(
                and_(
                    StatutoryPeriod.organization_id == organization_id,
                    StatutoryPeriod.provision_code == provision_code,
                    StatutoryPeriod.is_active == True,
                )
            )
        )
        return result.scalar_one_or_none()

    # =========================================================================
    # Period Tracking
    # =========================================================================

    async def start_period_tracking(
        self,
        organization_id: UUID,
        legal_case_id: UUID,
        statutory_period_id: UUID,
        trigger_event: str,
        trigger_date: date,
        action_required: str,
        loan_account_id: Optional[UUID] = None,
        start_date: Optional[date] = None,
        created_by: Optional[UUID] = None,
    ) -> PeriodTracking:
        """Start tracking a statutory period for a case."""
        # Get period definition
        period = await self.get_statutory_period(statutory_period_id)
        if not period:
            raise ValueError(f"Statutory period {statutory_period_id} not found")

        # Calculate dates
        actual_start = start_date or trigger_date
        deadline = self.calculate_limitation_date(
            start_date=actual_start,
            period_days=period.period_days,
            period_months=period.period_months,
            period_years=period.period_years,
        )
        days_remaining = (deadline - date.today()).days

        # Determine alert priority
        alert_priority = self._calculate_alert_priority(days_remaining)

        tracking = PeriodTracking(
            organization_id=organization_id,
            legal_case_id=legal_case_id,
            loan_account_id=loan_account_id,
            statutory_period_id=statutory_period_id,
            period_name=period.provision_name,
            provision_reference=f"{period.act_name}, {period.section_reference}",
            trigger_event=trigger_event,
            trigger_date=trigger_date,
            start_date=actual_start,
            deadline_date=deadline,
            period_days=period.period_days,
            status="ACTIVE",
            action_required=action_required,
            days_remaining=days_remaining,
            last_calculated_at=datetime.utcnow(),
            alert_priority=alert_priority,
            created_by=created_by,
        )
        self.db.add(tracking)
        await self.db.flush()

        # Create initial alerts
        await self._create_scheduled_alerts(tracking, period)

        return tracking

    async def mark_complied(
        self,
        tracking_id: UUID,
        action_taken_date: date,
        action_taken_details: str,
        compliance_verified_by: str,
        updated_by: Optional[UUID] = None,
    ) -> PeriodTracking:
        """Mark a statutory period as complied."""
        result = await self.db.execute(
            select(PeriodTracking).where(PeriodTracking.id == tracking_id)
        )
        tracking = result.scalar_one_or_none()
        if not tracking:
            raise ValueError(f"Period tracking {tracking_id} not found")

        tracking.status = "COMPLIED"
        tracking.action_taken_date = action_taken_date
        tracking.action_taken_details = action_taken_details
        tracking.compliance_verified_by = compliance_verified_by
        tracking.compliance_verified_date = datetime.utcnow()
        tracking.updated_by = updated_by

        await self.db.flush()
        return tracking

    async def extend_deadline(
        self,
        tracking_id: UUID,
        extended_deadline: date,
        extension_reason: str,
        extension_approved_by: str,
        updated_by: Optional[UUID] = None,
    ) -> PeriodTracking:
        """Extend a statutory deadline (if allowed)."""
        result = await self.db.execute(
            select(PeriodTracking)
            .options(selectinload(PeriodTracking.statutory_period))
            .where(PeriodTracking.id == tracking_id)
        )
        tracking = result.scalar_one_or_none()
        if not tracking:
            raise ValueError(f"Period tracking {tracking_id} not found")

        if tracking.statutory_period and not tracking.statutory_period.extension_allowed:
            raise ValueError("Extension not allowed for this statutory period")

        tracking.is_extended = True
        tracking.extension_reason = extension_reason
        tracking.extended_deadline = extended_deadline
        tracking.extension_approved_by = extension_approved_by
        tracking.updated_by = updated_by

        # Recalculate days remaining
        tracking.days_remaining = (extended_deadline - date.today()).days
        tracking.alert_priority = self._calculate_alert_priority(tracking.days_remaining)
        tracking.last_calculated_at = datetime.utcnow()

        await self.db.flush()
        return tracking

    # =========================================================================
    # Calculations
    # =========================================================================

    def calculate_limitation_date(
        self,
        start_date: date,
        period_days: int = 0,
        period_months: Optional[int] = None,
        period_years: Optional[int] = None,
    ) -> date:
        """Calculate limitation date from start date."""
        result_date = start_date

        # Add years
        if period_years:
            result_date = date(
                result_date.year + period_years,
                result_date.month,
                result_date.day,
            )

        # Add months
        if period_months:
            new_month = result_date.month + period_months
            new_year = result_date.year + (new_month - 1) // 12
            new_month = ((new_month - 1) % 12) + 1
            # Handle month-end dates
            import calendar
            max_day = calendar.monthrange(new_year, new_month)[1]
            new_day = min(result_date.day, max_day)
            result_date = date(new_year, new_month, new_day)

        # Add days
        if period_days:
            result_date = result_date + timedelta(days=period_days)

        return result_date

    def calculate_appeal_deadline(
        self,
        order_date: date,
        forum_type: LegalForumType,
    ) -> date:
        """Calculate appeal deadline based on forum."""
        appeal_periods = {
            LegalForumType.DRT: 30,  # Days to appeal to DRAT
            LegalForumType.NCLT: 30,  # Days to appeal to NCLAT
            LegalForumType.CIVIL_COURT: 30,  # Days to High Court
            LegalForumType.HIGH_COURT: 90,  # Days to Supreme Court
            LegalForumType.LOK_ADALAT: 0,  # No appeal
        }
        days = appeal_periods.get(forum_type, 30)
        return order_date + timedelta(days=days)

    def calculate_sarfaesi_timeline(
        self, demand_notice_date: date
    ) -> Dict[str, date]:
        """Calculate complete SARFAESI timeline from demand notice date."""
        timeline = {
            "demand_notice_date": demand_notice_date,
            "response_due_date": demand_notice_date + timedelta(days=60),
            "objection_disposal_date": demand_notice_date + timedelta(days=105),  # 60 + 45
            "earliest_possession_date": demand_notice_date + timedelta(days=60),
            "appeal_deadline": demand_notice_date + timedelta(days=105),  # 60 + 45 days from possession
        }
        return timeline

    # =========================================================================
    # Queries
    # =========================================================================

    async def get_upcoming_deadlines(
        self,
        organization_id: UUID,
        days_ahead: int = 30,
        legal_case_id: Optional[UUID] = None,
    ) -> List[PeriodTracking]:
        """Get upcoming statutory deadlines."""
        deadline_date = date.today() + timedelta(days=days_ahead)

        query = select(PeriodTracking).where(
            and_(
                PeriodTracking.organization_id == organization_id,
                PeriodTracking.is_active == True,
                PeriodTracking.status == "ACTIVE",
                PeriodTracking.deadline_date <= deadline_date,
            )
        )

        if legal_case_id:
            query = query.where(PeriodTracking.legal_case_id == legal_case_id)

        query = query.order_by(PeriodTracking.deadline_date)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_overdue_periods(
        self, organization_id: UUID
    ) -> List[PeriodTracking]:
        """Get periods that are past deadline without compliance."""
        result = await self.db.execute(
            select(PeriodTracking).where(
                and_(
                    PeriodTracking.organization_id == organization_id,
                    PeriodTracking.is_active == True,
                    PeriodTracking.status == "ACTIVE",
                    PeriodTracking.deadline_date < date.today(),
                )
            )
        )
        return list(result.scalars().all())

    async def check_limitation_status(
        self, legal_case_id: UUID
    ) -> Dict[str, Any]:
        """Check limitation status for all periods in a case."""
        result = await self.db.execute(
            select(PeriodTracking).where(
                and_(
                    PeriodTracking.legal_case_id == legal_case_id,
                    PeriodTracking.is_active == True,
                )
            )
        )
        trackings = list(result.scalars().all())

        status = {
            "total_periods": len(trackings),
            "active": 0,
            "complied": 0,
            "expired": 0,
            "critical": [],
            "overdue": [],
        }

        today = date.today()
        for tracking in trackings:
            if tracking.status == "COMPLIED":
                status["complied"] += 1
            elif tracking.status == "ACTIVE":
                status["active"] += 1
                effective_deadline = tracking.extended_deadline or tracking.deadline_date
                if effective_deadline < today:
                    status["expired"] += 1
                    status["overdue"].append({
                        "id": str(tracking.id),
                        "name": tracking.period_name,
                        "deadline": effective_deadline.isoformat(),
                        "days_overdue": (today - effective_deadline).days,
                    })
                elif (effective_deadline - today).days <= 7:
                    status["critical"].append({
                        "id": str(tracking.id),
                        "name": tracking.period_name,
                        "deadline": effective_deadline.isoformat(),
                        "days_remaining": (effective_deadline - today).days,
                    })

        return status

    # =========================================================================
    # Alert Management
    # =========================================================================

    async def _create_scheduled_alerts(
        self, tracking: PeriodTracking, period: StatutoryPeriod
    ) -> None:
        """Create scheduled alerts for a period tracking."""
        alert_days = period.alert_before_days.get("days", [30, 15, 7, 1]) if period.alert_before_days else [30, 15, 7, 1]
        today = date.today()

        for days_before in alert_days:
            alert_date = tracking.deadline_date - timedelta(days=days_before)
            if alert_date >= today:
                priority = self._calculate_alert_priority(days_before)
                alert = LimitationAlert(
                    period_tracking_id=tracking.id,
                    alert_date=alert_date,
                    alert_type="SCHEDULED",
                    priority=priority,
                    status="PENDING",
                    alert_title=f"Deadline Alert: {tracking.period_name}",
                    alert_message=f"{days_before} days remaining for {tracking.period_name}. "
                                  f"Action required: {tracking.action_required}",
                    days_to_deadline=days_before,
                    created_by=tracking.created_by,
                )
                self.db.add(alert)

        await self.db.flush()

    def _calculate_alert_priority(self, days_remaining: int) -> AlertPriority:
        """Calculate alert priority based on days remaining."""
        if days_remaining < 0:
            return AlertPriority.OVERDUE
        elif days_remaining <= 7:
            return AlertPriority.CRITICAL
        elif days_remaining <= 14:
            return AlertPriority.HIGH
        elif days_remaining <= 30:
            return AlertPriority.MEDIUM
        else:
            return AlertPriority.LOW

    async def update_all_periods(self, organization_id: UUID) -> int:
        """Update days remaining and alert priority for all active periods."""
        result = await self.db.execute(
            select(PeriodTracking).where(
                and_(
                    PeriodTracking.organization_id == organization_id,
                    PeriodTracking.is_active == True,
                    PeriodTracking.status == "ACTIVE",
                )
            )
        )
        trackings = list(result.scalars().all())

        today = date.today()
        updated_count = 0

        for tracking in trackings:
            effective_deadline = tracking.extended_deadline or tracking.deadline_date
            tracking.days_remaining = (effective_deadline - today).days
            tracking.alert_priority = self._calculate_alert_priority(tracking.days_remaining)
            tracking.last_calculated_at = datetime.utcnow()

            # Check if expired
            if tracking.days_remaining < 0:
                tracking.status = "EXPIRED"

            updated_count += 1

        await self.db.flush()
        return updated_count
