"""Legal Alerts Background Worker.

Handles scheduled tasks for legal module:
- Limitation period alerts
- Hearing reminders
- Auction reminders
- Statutory deadline alerts
- Notice expiry alerts
"""

import asyncio
import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.common.background_job import BackgroundJob, JobType, JobStatus
from app.models.legal.statutory_period import LimitationAlert, PeriodTracking
from app.models.legal.enums import AlertPriority
from app.services.common.job_service import BackgroundJobRunner

logger = logging.getLogger(__name__)


async def process_legal_alerts(
    job: BackgroundJob,
    runner: BackgroundJobRunner,
) -> Dict[str, Any]:
    """
    Process legal alerts and send notifications.

    This job runs daily to:
    1. Check limitation periods approaching deadline
    2. Generate alerts for upcoming hearings
    3. Generate alerts for upcoming auctions
    4. Check statutory deadlines
    5. Send notifications to relevant users
    """
    from app.database import async_session_maker

    input_data = job.input_data or {}
    days_ahead = input_data.get("days_ahead", 30)

    alerts_generated = 0
    notifications_sent = 0
    errors: List[Dict] = []

    async with async_session_maker() as session:
        try:
            # 1. Process limitation period alerts
            limitation_alerts = await _check_limitation_periods(
                session, job.organization_id, days_ahead
            )
            alerts_generated += len(limitation_alerts)

            # 2. Process hearing reminders
            hearing_alerts = await _check_upcoming_hearings(
                session, job.organization_id, days_ahead
            )
            alerts_generated += len(hearing_alerts)

            # 3. Process auction reminders
            auction_alerts = await _check_upcoming_auctions(
                session, job.organization_id, days_ahead
            )
            alerts_generated += len(auction_alerts)

            # 4. Process statutory deadline alerts
            deadline_alerts = await _check_statutory_deadlines(
                session, job.organization_id, days_ahead
            )
            alerts_generated += len(deadline_alerts)

            # 5. Send notifications
            all_alerts = limitation_alerts + hearing_alerts + auction_alerts + deadline_alerts
            notifications_sent = await _send_alert_notifications(
                session, all_alerts
            )

            await session.commit()

            # Update job progress
            await runner.update_progress(
                job,
                processed=alerts_generated,
                successful=notifications_sent,
                failed=alerts_generated - notifications_sent,
            )

        except Exception as e:
            logger.error(f"Error processing legal alerts: {e}")
            errors.append({"error": str(e)})

    return {
        "alerts_generated": alerts_generated,
        "notifications_sent": notifications_sent,
        "errors": errors,
    }


async def _check_limitation_periods(
    session: AsyncSession,
    organization_id: UUID,
    days_ahead: int,
) -> List[Dict[str, Any]]:
    """Check limitation periods approaching deadline."""
    alerts = []
    today = date.today()
    check_date = today + timedelta(days=days_ahead)

    # Query period tracking records with approaching deadlines
    query = select(PeriodTracking).where(
        and_(
            PeriodTracking.organization_id == organization_id,
            PeriodTracking.expiry_date <= check_date,
            PeriodTracking.expiry_date >= today,
            PeriodTracking.is_active == True,
            PeriodTracking.is_completed == False,
        )
    )

    result = await session.execute(query)
    records = result.scalars().all()

    for record in records:
        days_remaining = (record.expiry_date - today).days
        priority = _get_priority_for_days(days_remaining)

        # Check if alert already exists for today
        existing = await session.execute(
            select(LimitationAlert).where(
                and_(
                    LimitationAlert.period_tracking_id == record.id,
                    func.date(LimitationAlert.created_at) == today,
                )
            )
        )

        if not existing.scalar_one_or_none():
            alert = LimitationAlert(
                organization_id=organization_id,
                period_tracking_id=record.id,
                legal_case_id=record.legal_case_id,
                alert_type="LIMITATION_EXPIRY",
                alert_priority=priority,
                expiry_date=record.expiry_date,
                days_remaining=days_remaining,
                alert_message=f"Limitation period expiring in {days_remaining} days for {record.period_type}",
                is_acknowledged=False,
            )
            session.add(alert)

            alerts.append({
                "type": "LIMITATION_EXPIRY",
                "case_id": str(record.legal_case_id),
                "period_type": record.period_type,
                "expiry_date": record.expiry_date.isoformat(),
                "days_remaining": days_remaining,
                "priority": priority.value,
            })

    return alerts


async def _check_upcoming_hearings(
    session: AsyncSession,
    organization_id: UUID,
    days_ahead: int,
) -> List[Dict[str, Any]]:
    """Check upcoming hearing dates."""
    from app.models.lending.collections import LegalHearing

    alerts = []
    today = date.today()
    check_date = today + timedelta(days=days_ahead)

    # Query upcoming hearings
    query = select(LegalHearing).where(
        and_(
            LegalHearing.organization_id == organization_id,
            LegalHearing.hearing_date <= check_date,
            LegalHearing.hearing_date >= today,
            LegalHearing.is_cancelled == False,
        )
    )

    result = await session.execute(query)
    hearings = result.scalars().all()

    for hearing in hearings:
        days_remaining = (hearing.hearing_date - today).days
        priority = _get_priority_for_days(days_remaining)

        alerts.append({
            "type": "HEARING_REMINDER",
            "case_id": str(hearing.legal_case_id),
            "hearing_id": str(hearing.id),
            "hearing_date": hearing.hearing_date.isoformat(),
            "court_name": hearing.court_name,
            "purpose": hearing.hearing_purpose,
            "days_remaining": days_remaining,
            "priority": priority.value,
        })

    return alerts


async def _check_upcoming_auctions(
    session: AsyncSession,
    organization_id: UUID,
    days_ahead: int,
) -> List[Dict[str, Any]]:
    """Check upcoming auction dates."""
    from app.models.lending.collections import PropertyAuction

    alerts = []
    today = date.today()
    check_date = today + timedelta(days=days_ahead)

    # Query upcoming auctions
    query = select(PropertyAuction).where(
        and_(
            PropertyAuction.organization_id == organization_id,
            PropertyAuction.auction_date <= check_date,
            PropertyAuction.auction_date >= today,
            PropertyAuction.auction_status.in_(["SCHEDULED", "PUBLISHED"]),
        )
    )

    result = await session.execute(query)
    auctions = result.scalars().all()

    for auction in auctions:
        days_remaining = (auction.auction_date - today).days
        priority = _get_priority_for_days(days_remaining)

        alerts.append({
            "type": "AUCTION_REMINDER",
            "case_id": str(auction.legal_case_id),
            "auction_id": str(auction.id),
            "auction_date": auction.auction_date.isoformat(),
            "reserve_price": float(auction.reserve_price) if auction.reserve_price else None,
            "days_remaining": days_remaining,
            "priority": priority.value,
        })

    return alerts


async def _check_statutory_deadlines(
    session: AsyncSession,
    organization_id: UUID,
    days_ahead: int,
) -> List[Dict[str, Any]]:
    """Check statutory deadlines (appeal periods, objection periods, etc.)."""
    from app.models.legal.notice import LegalNotice

    alerts = []
    today = date.today()
    check_date = today + timedelta(days=days_ahead)

    # Query notices with approaching response deadlines
    query = select(LegalNotice).where(
        and_(
            LegalNotice.organization_id == organization_id,
            LegalNotice.response_due_date <= check_date,
            LegalNotice.response_due_date >= today,
            LegalNotice.notice_status.in_(["DISPATCHED", "DELIVERED"]),
        )
    )

    result = await session.execute(query)
    notices = result.scalars().all()

    for notice in notices:
        days_remaining = (notice.response_due_date - today).days
        priority = _get_priority_for_days(days_remaining)

        alerts.append({
            "type": "NOTICE_DEADLINE",
            "case_id": str(notice.legal_case_id),
            "notice_id": str(notice.id),
            "notice_type": notice.notice_type,
            "response_due_date": notice.response_due_date.isoformat(),
            "days_remaining": days_remaining,
            "priority": priority.value,
        })

    return alerts


def _get_priority_for_days(days: int) -> AlertPriority:
    """Get alert priority based on days remaining."""
    if days < 0:
        return AlertPriority.OVERDUE
    elif days <= 3:
        return AlertPriority.CRITICAL
    elif days <= 7:
        return AlertPriority.HIGH
    elif days <= 15:
        return AlertPriority.MEDIUM
    else:
        return AlertPriority.LOW


async def _send_alert_notifications(
    session: AsyncSession,
    alerts: List[Dict[str, Any]],
) -> int:
    """Send notifications for alerts."""
    # TODO: Implement notification sending using CommunicationService
    # from app.integrations.communication import CommunicationService

    notifications_sent = 0

    for alert in alerts:
        try:
            # Get users to notify (legal team, assigned advocate, etc.)
            # Send email/SMS/push based on priority and user preferences

            # For critical/high priority, send SMS
            if alert["priority"] in ["CRITICAL", "HIGH"]:
                # comm_service.send_sms(...)
                pass

            # For all priorities, send email
            # comm_service.send_email(...)

            # For critical, also send push notification
            if alert["priority"] == "CRITICAL":
                # comm_service.send_push(...)
                pass

            notifications_sent += 1

        except Exception as e:
            logger.error(f"Failed to send notification for alert: {e}")

    return notifications_sent


# Scheduled task functions for cron jobs

async def run_daily_legal_alerts():
    """Run daily legal alerts job."""
    from app.database import async_session_maker
    from app.services.common.job_service import JobService, BackgroundJobRunner

    logger.info("Starting daily legal alerts job")

    async with async_session_maker() as session:
        job_service = JobService(session)

        # Get all active organizations
        # For each organization, create and process job
        # This is a simplified version - in production, get organizations from DB

        organization_id = UUID("00000000-0000-0000-0000-000000000000")  # Placeholder

        job = await job_service.create_job(
            organization_id=organization_id,
            job_type=JobType.LEGAL_ALERTS,
            job_name="Daily Legal Alerts",
            created_by=organization_id,  # System user
            input_data={"days_ahead": 30},
        )

        runner = BackgroundJobRunner(session)
        result = await process_legal_alerts(job, runner)

        logger.info(f"Daily legal alerts completed: {result}")


async def run_limitation_check():
    """Run limitation period check (can be scheduled more frequently)."""
    logger.info("Running limitation period check")
    # Similar to daily alerts but focused only on critical deadlines
    pass


async def run_hearing_reminders():
    """Send hearing reminders (run morning of hearing date)."""
    logger.info("Running hearing reminders")
    # Send reminders for hearings scheduled today and tomorrow
    pass
