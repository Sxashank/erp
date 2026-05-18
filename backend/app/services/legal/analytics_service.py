"""Legal Analytics Service.

Provides business logic for generating legal portfolio
reports, recovery metrics, and performance analytics.
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.legal.advocate import AdvocateAssignment
from app.models.legal.expense import LegalExpense
from app.models.legal.notice import LegalNotice
from app.models.legal.statutory_period import PeriodTracking
from app.models.lending.collections import LegalCase, LegalHearing
from app.models.lending.enums import (
    LegalCaseStatus,
)


class LegalAnalyticsService:
    """Service for legal analytics and reporting."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Dashboard
    # =========================================================================

    async def get_dashboard(
        self,
        organization_id: UUID,
        as_of_date: date | None = None,
    ) -> dict[str, Any]:
        """Get legal dashboard summary."""
        check_date = as_of_date or date.today()

        dashboard = {
            "as_of_date": check_date.isoformat(),
            "portfolio_summary": await self.get_portfolio_legal_status(organization_id),
            "upcoming_deadlines": await self._get_deadline_summary(organization_id),
            "upcoming_hearings": await self._get_upcoming_hearings_summary(organization_id),
            "recent_activity": await self._get_recent_activity(organization_id),
            "recovery_metrics": await self.get_recovery_efficiency(organization_id),
        }

        return dashboard

    # =========================================================================
    # Portfolio Analysis
    # =========================================================================

    async def get_portfolio_legal_status(self, organization_id: UUID) -> dict[str, Any]:
        """Get legal portfolio status summary."""
        # Total cases
        total_query = select(func.count()).where(
            and_(
                LegalCase.organization_id == organization_id,
                LegalCase.is_active == True,
            )
        )
        total_cases = (await self.db.execute(total_query)).scalar() or 0

        # Cases by status
        status_query = (
            select(
                LegalCase.status,
                func.count().label("count"),
                func.sum(LegalCase.total_claim).label("total_claim"),
            )
            .where(
                and_(
                    LegalCase.organization_id == organization_id,
                    LegalCase.is_active == True,
                )
            )
            .group_by(LegalCase.status)
        )
        status_result = await self.db.execute(status_query)
        status_breakdown = {
            row.status.value if row.status else "UNKNOWN": {
                "count": row.count,
                "total_claim": float(row.total_claim or 0),
            }
            for row in status_result
        }

        # Cases by type
        type_query = (
            select(
                LegalCase.case_type,
                func.count().label("count"),
                func.sum(LegalCase.total_claim).label("total_claim"),
            )
            .where(
                and_(
                    LegalCase.organization_id == organization_id,
                    LegalCase.is_active == True,
                )
            )
            .group_by(LegalCase.case_type)
        )
        type_result = await self.db.execute(type_query)
        type_breakdown = {
            row.case_type.value if row.case_type else "UNKNOWN": {
                "count": row.count,
                "total_claim": float(row.total_claim or 0),
            }
            for row in type_result
        }

        # Cases by forum
        forum_query = (
            select(
                LegalCase.forum_type,
                func.count().label("count"),
                func.sum(LegalCase.total_claim).label("total_claim"),
            )
            .where(
                and_(
                    LegalCase.organization_id == organization_id,
                    LegalCase.is_active == True,
                )
            )
            .group_by(LegalCase.forum_type)
        )
        forum_result = await self.db.execute(forum_query)
        forum_breakdown = {
            row.forum_type.value if row.forum_type else "UNKNOWN": {
                "count": row.count,
                "total_claim": float(row.total_claim or 0),
            }
            for row in forum_result
        }

        # Total claim and recovery
        totals_query = select(
            func.sum(LegalCase.total_claim).label("total_claim"),
            func.sum(LegalCase.recovery_through_case).label("total_recovery"),
            func.sum(LegalCase.legal_costs_incurred).label("total_costs"),
        ).where(
            and_(
                LegalCase.organization_id == organization_id,
                LegalCase.is_active == True,
            )
        )
        totals = (await self.db.execute(totals_query)).first()

        return {
            "total_cases": total_cases,
            "total_claim_amount": float(totals.total_claim or 0),
            "total_recovery_amount": float(totals.total_recovery or 0),
            "total_legal_costs": float(totals.total_costs or 0),
            "by_status": status_breakdown,
            "by_type": type_breakdown,
            "by_forum": forum_breakdown,
        }

    # =========================================================================
    # Recovery Analysis
    # =========================================================================

    async def get_recovery_efficiency(
        self,
        organization_id: UUID,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> dict[str, Any]:
        """Get recovery efficiency metrics."""
        query = select(
            func.sum(LegalCase.total_claim).label("total_claim"),
            func.sum(LegalCase.recovery_through_case).label("total_recovery"),
            func.count().label("total_cases"),
            func.sum(case((LegalCase.status == LegalCaseStatus.CLOSED, 1), else_=0)).label(
                "closed_cases"
            ),
            func.sum(case((LegalCase.status == LegalCaseStatus.SETTLED, 1), else_=0)).label(
                "settled_cases"
            ),
        ).where(
            and_(
                LegalCase.organization_id == organization_id,
                LegalCase.is_active == True,
            )
        )

        if from_date:
            query = query.where(LegalCase.filing_date >= from_date)
        if to_date:
            query = query.where(LegalCase.filing_date <= to_date)

        result = (await self.db.execute(query)).first()

        total_claim = float(result.total_claim or 0)
        total_recovery = float(result.total_recovery or 0)

        recovery_rate = (total_recovery / total_claim * 100) if total_claim > 0 else 0

        return {
            "total_claim_amount": total_claim,
            "total_recovery_amount": total_recovery,
            "recovery_rate_percentage": round(recovery_rate, 2),
            "total_cases": result.total_cases or 0,
            "recovered_cases": result.closed_cases or 0,
            "settled_cases": result.settled_cases or 0,
            "pending_amount": total_claim - total_recovery,
        }

    # =========================================================================
    # Advocate Performance
    # =========================================================================

    async def get_advocate_wise_performance(
        self,
        organization_id: UUID,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Get advocate-wise performance metrics."""
        query = (
            select(
                AdvocateAssignment.advocate_id,
                func.count().label("total_cases"),
                func.sum(case((AdvocateAssignment.is_active == True, 1), else_=0)).label(
                    "active_cases"
                ),
            )
            .group_by(AdvocateAssignment.advocate_id)
            .order_by(func.count().desc())
            .limit(limit)
        )

        result = await self.db.execute(query)
        assignments = list(result.all())

        performance_list = []
        for row in assignments:
            # Get advocate details
            from app.models.legal.advocate import Advocate

            adv_result = await self.db.execute(
                select(Advocate).where(Advocate.id == row.advocate_id)
            )
            advocate = adv_result.scalar_one_or_none()

            if advocate:
                performance_list.append(
                    {
                        "advocate_id": str(row.advocate_id),
                        "advocate_name": advocate.full_name,
                        "total_cases": row.total_cases,
                        "active_cases": row.active_cases,
                    }
                )

        return performance_list

    # =========================================================================
    # Forum Analysis
    # =========================================================================

    async def get_forum_wise_analysis(self, organization_id: UUID) -> list[dict[str, Any]]:
        """Get forum-wise case analysis."""
        query = (
            select(
                LegalCase.forum_type,
                func.count().label("total_cases"),
                func.sum(LegalCase.total_claim).label("total_claim"),
                func.sum(LegalCase.recovery_through_case).label("total_recovery"),
                func.avg(func.extract("day", LegalCase.closure_date - LegalCase.filing_date)).label(
                    "avg_resolution_days"
                ),
            )
            .where(
                and_(
                    LegalCase.organization_id == organization_id,
                    LegalCase.is_active == True,
                )
            )
            .group_by(LegalCase.forum_type)
        )

        result = await self.db.execute(query)

        return [
            {
                "forum_type": row.forum_type.value if row.forum_type else "UNKNOWN",
                "total_cases": row.total_cases,
                "total_claim": float(row.total_claim or 0),
                "total_recovery": float(row.total_recovery or 0),
                "avg_resolution_days": int(row.avg_resolution_days or 0),
                "recovery_rate": round(
                    float(row.total_recovery or 0) / float(row.total_claim or 1) * 100, 2
                ),
            }
            for row in result
        ]

    # =========================================================================
    # Aging Analysis
    # =========================================================================

    async def get_aging_analysis(self, organization_id: UUID) -> dict[str, Any]:
        """Get aging analysis of legal cases."""
        today = date.today()

        # Define aging buckets (in days)
        buckets = [
            (0, 30, "0-30 days"),
            (31, 90, "31-90 days"),
            (91, 180, "91-180 days"),
            (181, 365, "181-365 days"),
            (366, None, ">365 days"),
        ]

        aging_data = {"buckets": [], "total": 0, "total_amount": Decimal("0")}

        for min_days, max_days, label in buckets:
            conditions = [
                LegalCase.organization_id == organization_id,
                LegalCase.is_active == True,
                LegalCase.status.not_in(
                    [
                        LegalCaseStatus.SETTLED,
                        LegalCaseStatus.CLOSED,
                    ]
                ),
            ]

            if max_days:
                cutoff_date = today - timedelta(days=max_days)
                conditions.append(LegalCase.filing_date >= cutoff_date)

            if min_days > 0:
                cutoff_date = today - timedelta(days=min_days)
                conditions.append(LegalCase.filing_date < cutoff_date)

            query = select(
                func.count().label("count"),
                func.sum(LegalCase.total_claim).label("amount"),
            ).where(and_(*conditions))

            result = (await self.db.execute(query)).first()

            bucket_data = {
                "label": label,
                "count": result.count or 0,
                "amount": float(result.amount or 0),
            }
            aging_data["buckets"].append(bucket_data)
            aging_data["total"] += bucket_data["count"]
            aging_data["total_amount"] += Decimal(str(bucket_data["amount"]))

        aging_data["total_amount"] = float(aging_data["total_amount"])

        return aging_data

    # =========================================================================
    # Expense Analysis
    # =========================================================================

    async def get_expense_recovery_ratio(self, organization_id: UUID) -> dict[str, Any]:
        """Get expense to recovery ratio."""
        # Total expenses
        expense_query = select(
            func.sum(LegalExpense.gross_amount).label("total_expense"),
            func.sum(LegalExpense.amount_recovered).label("recovered"),
        ).where(
            and_(
                LegalExpense.organization_id == organization_id,
                LegalExpense.is_active == True,
            )
        )
        expense_result = (await self.db.execute(expense_query)).first()

        # Total recovery
        recovery_query = select(
            func.sum(LegalCase.recovery_through_case).label("total_recovery"),
        ).where(
            and_(
                LegalCase.organization_id == organization_id,
                LegalCase.is_active == True,
            )
        )
        recovery_result = (await self.db.execute(recovery_query)).first()

        total_expense = float(expense_result.total_expense or 0)
        expense_recovered = float(expense_result.recovered or 0)
        total_recovery = float(recovery_result.total_recovery or 0)

        # Expense to recovery ratio
        ratio = (total_expense / total_recovery * 100) if total_recovery > 0 else 0

        return {
            "total_expense": total_expense,
            "expense_recovered": expense_recovered,
            "total_recovery": total_recovery,
            "expense_to_recovery_ratio": round(ratio, 2),
            "net_recovery": total_recovery - total_expense + expense_recovered,
        }

    # =========================================================================
    # Helper Methods
    # =========================================================================

    async def _get_deadline_summary(self, organization_id: UUID) -> dict[str, Any]:
        """Get upcoming deadline summary."""
        today = date.today()

        # Critical deadlines (within 7 days)
        critical_query = select(func.count()).where(
            and_(
                PeriodTracking.organization_id == organization_id,
                PeriodTracking.is_active == True,
                PeriodTracking.status == "ACTIVE",
                PeriodTracking.deadline_date <= today + timedelta(days=7),
                PeriodTracking.deadline_date >= today,
            )
        )
        critical = (await self.db.execute(critical_query)).scalar() or 0

        # Overdue
        overdue_query = select(func.count()).where(
            and_(
                PeriodTracking.organization_id == organization_id,
                PeriodTracking.is_active == True,
                PeriodTracking.status == "ACTIVE",
                PeriodTracking.deadline_date < today,
            )
        )
        overdue = (await self.db.execute(overdue_query)).scalar() or 0

        # Next 30 days
        upcoming_query = select(func.count()).where(
            and_(
                PeriodTracking.organization_id == organization_id,
                PeriodTracking.is_active == True,
                PeriodTracking.status == "ACTIVE",
                PeriodTracking.deadline_date <= today + timedelta(days=30),
                PeriodTracking.deadline_date > today + timedelta(days=7),
            )
        )
        upcoming = (await self.db.execute(upcoming_query)).scalar() or 0

        return {
            "critical": critical,
            "overdue": overdue,
            "upcoming_30_days": upcoming,
        }

    async def _get_upcoming_hearings_summary(self, organization_id: UUID) -> dict[str, Any]:
        """Get upcoming hearings summary."""
        today = date.today()

        # This week
        week_query = select(func.count()).where(
            and_(
                LegalHearing.is_active == True,
                LegalHearing.hearing_date >= today,
                LegalHearing.hearing_date <= today + timedelta(days=7),
            )
        )
        this_week = (await self.db.execute(week_query)).scalar() or 0

        # Next 30 days
        month_query = select(func.count()).where(
            and_(
                LegalHearing.is_active == True,
                LegalHearing.hearing_date >= today,
                LegalHearing.hearing_date <= today + timedelta(days=30),
            )
        )
        next_30_days = (await self.db.execute(month_query)).scalar() or 0

        return {
            "this_week": this_week,
            "next_30_days": next_30_days,
        }

    async def _get_recent_activity(
        self,
        organization_id: UUID,
        days: int = 7,
    ) -> dict[str, Any]:
        """Get recent activity summary."""
        since_date = date.today() - timedelta(days=days)

        # New cases
        new_cases_query = select(func.count()).where(
            and_(
                LegalCase.organization_id == organization_id,
                LegalCase.is_active == True,
                LegalCase.created_at >= since_date,
            )
        )
        new_cases = (await self.db.execute(new_cases_query)).scalar() or 0

        # Notices issued
        notices_query = select(func.count()).where(
            and_(
                LegalNotice.organization_id == organization_id,
                LegalNotice.is_active == True,
                LegalNotice.notice_date >= since_date,
            )
        )
        notices = (await self.db.execute(notices_query)).scalar() or 0

        # Expenses recorded
        expenses_query = select(func.count()).where(
            and_(
                LegalExpense.organization_id == organization_id,
                LegalExpense.is_active == True,
                LegalExpense.expense_date >= since_date,
            )
        )
        expenses = (await self.db.execute(expenses_query)).scalar() or 0

        return {
            "period_days": days,
            "new_cases": new_cases,
            "notices_issued": notices,
            "expenses_recorded": expenses,
        }
