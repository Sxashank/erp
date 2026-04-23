"""Portal Reminders Background Worker.

Handles scheduled tasks for customer portal:
- EMI due reminders
- Overdue notifications
- Document expiry reminders
- Service request follow-ups
"""

import asyncio
import logging
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.common.background_job import BackgroundJob, JobType, JobStatus
from app.services.common.job_service import BackgroundJobRunner

logger = logging.getLogger(__name__)


async def process_portal_reminders(
    job: BackgroundJob,
    runner: BackgroundJobRunner,
) -> Dict[str, Any]:
    """
    Process portal reminders and send notifications.

    This job runs daily to:
    1. Send EMI due reminders (7 days, 3 days, 1 day before)
    2. Send overdue notifications
    3. Send document expiry reminders
    4. Follow up on pending service requests
    """
    from app.database import async_session_maker

    input_data = job.input_data or {}
    reminder_type = input_data.get("reminder_type", "all")

    reminders_sent = 0
    errors: List[Dict] = []

    async with async_session_maker() as session:
        try:
            results = {}

            if reminder_type in ["all", "emi_due"]:
                count = await _send_emi_due_reminders(session, job.organization_id)
                results["emi_due_reminders"] = count
                reminders_sent += count

            if reminder_type in ["all", "overdue"]:
                count = await _send_overdue_notifications(session, job.organization_id)
                results["overdue_notifications"] = count
                reminders_sent += count

            if reminder_type in ["all", "document_expiry"]:
                count = await _send_document_expiry_reminders(session, job.organization_id)
                results["document_expiry_reminders"] = count
                reminders_sent += count

            if reminder_type in ["all", "service_request"]:
                count = await _send_service_request_followups(session, job.organization_id)
                results["service_request_followups"] = count
                reminders_sent += count

            await session.commit()

            await runner.update_progress(
                job,
                processed=reminders_sent,
                successful=reminders_sent,
                failed=0,
            )

            return {
                "total_reminders_sent": reminders_sent,
                "breakdown": results,
                "errors": errors,
            }

        except Exception as e:
            logger.error(f"Error processing portal reminders: {e}")
            errors.append({"error": str(e)})
            return {
                "total_reminders_sent": reminders_sent,
                "errors": errors,
            }


async def _send_emi_due_reminders(
    session: AsyncSession,
    organization_id: UUID,
) -> int:
    """Send EMI due reminders before due date."""
    # from app.models.lending.lms import LoanAccount, RepaymentSchedule
    # from app.integrations.communication import CommunicationService

    reminders_sent = 0
    today = date.today()

    # Reminder schedule: 7 days, 3 days, 1 day before
    reminder_days = [7, 3, 1]

    for days_before in reminder_days:
        due_date = today + timedelta(days=days_before)

        # Query loans with EMI due on this date
        # query = select(RepaymentSchedule).join(LoanAccount).where(
        #     and_(
        #         LoanAccount.organization_id == organization_id,
        #         RepaymentSchedule.due_date == due_date,
        #         RepaymentSchedule.status == "UNPAID",
        #         LoanAccount.account_status == "ACTIVE",
        #     )
        # )

        # result = await session.execute(query)
        # schedules = result.scalars().all()

        # for schedule in schedules:
        #     # Get customer contact
        #     customer = await _get_customer_contact(session, schedule.loan_account.customer_id)
        #
        #     # Send reminder
        #     await _send_reminder(
        #         channel="SMS",
        #         recipient=customer.mobile,
        #         template="emi_due_reminder",
        #         params={
        #             "customer_name": customer.name,
        #             "loan_account": schedule.loan_account.account_number,
        #             "amount": str(schedule.emi_amount),
        #             "due_date": due_date.strftime("%d-%b-%Y"),
        #             "days_before": days_before,
        #         }
        #     )
        #     reminders_sent += 1

        # Placeholder implementation
        logger.info(f"Sending EMI reminders for due date: {due_date}")

    return reminders_sent


async def _send_overdue_notifications(
    session: AsyncSession,
    organization_id: UUID,
) -> int:
    """Send overdue notifications."""
    # from app.models.lending.lms import LoanAccount, RepaymentSchedule

    reminders_sent = 0
    today = date.today()

    # Notification schedule: 1 day, 3 days, 7 days, 15 days, 30 days overdue
    overdue_days = [1, 3, 7, 15, 30]

    for days_overdue in overdue_days:
        overdue_date = today - timedelta(days=days_overdue)

        # Query overdue EMIs
        # query = select(RepaymentSchedule).join(LoanAccount).where(
        #     and_(
        #         LoanAccount.organization_id == organization_id,
        #         RepaymentSchedule.due_date == overdue_date,
        #         RepaymentSchedule.status == "UNPAID",
        #     )
        # )

        # For severe overdue (> 7 days), escalate with call + SMS
        # For initial overdue, send SMS only

        logger.info(f"Sending overdue notifications for {days_overdue} days overdue")

    return reminders_sent


async def _send_document_expiry_reminders(
    session: AsyncSession,
    organization_id: UUID,
) -> int:
    """Send document expiry reminders."""
    # from app.models.portal.document import PortalDocument

    reminders_sent = 0
    today = date.today()

    # Documents that expire in 30, 15, 7 days
    expiry_days = [30, 15, 7]

    for days_to_expiry in expiry_days:
        expiry_date = today + timedelta(days=days_to_expiry)

        # Query documents expiring on this date
        # - Insurance policies
        # - KYC documents (ID proof, address proof)
        # - Other time-sensitive documents

        logger.info(f"Sending document expiry reminders for date: {expiry_date}")

    return reminders_sent


async def _send_service_request_followups(
    session: AsyncSession,
    organization_id: UUID,
) -> int:
    """Send follow-ups for pending service requests."""
    from app.models.portal.service_request import PortalServiceRequest
    from app.models.portal.enums import ServiceRequestStatus

    reminders_sent = 0
    today = date.today()

    # Query service requests pending for more than 3 days
    threshold_date = today - timedelta(days=3)

    query = select(PortalServiceRequest).where(
        and_(
            PortalServiceRequest.organization_id == organization_id,
            PortalServiceRequest.status.in_([
                ServiceRequestStatus.SUBMITTED,
                ServiceRequestStatus.UNDER_REVIEW,
            ]),
            func.date(PortalServiceRequest.created_at) <= threshold_date,
        )
    )

    result = await session.execute(query)
    requests = result.scalars().all()

    for request in requests:
        days_pending = (today - request.created_at.date()).days

        # Notify internal team for follow-up
        logger.info(
            f"Service request {request.id} pending for {days_pending} days"
        )
        reminders_sent += 1

    return reminders_sent


# Scheduled task functions

async def run_daily_emi_reminders():
    """Run daily EMI reminder job."""
    from app.database import async_session_maker
    from app.services.common.job_service import JobService, BackgroundJobRunner

    logger.info("Starting daily EMI reminders job")

    async with async_session_maker() as session:
        job_service = JobService(session)

        # In production, iterate over all organizations
        organization_id = UUID("00000000-0000-0000-0000-000000000000")

        job = await job_service.create_job(
            organization_id=organization_id,
            job_type=JobType.PORTAL_REMINDERS,
            job_name="Daily EMI Reminders",
            created_by=organization_id,
            input_data={"reminder_type": "emi_due"},
        )

        runner = BackgroundJobRunner(session)
        result = await process_portal_reminders(job, runner)

        logger.info(f"Daily EMI reminders completed: {result}")


async def run_overdue_notifications():
    """Run overdue notification job."""
    from app.database import async_session_maker
    from app.services.common.job_service import JobService, BackgroundJobRunner

    logger.info("Starting overdue notifications job")

    async with async_session_maker() as session:
        job_service = JobService(session)

        organization_id = UUID("00000000-0000-0000-0000-000000000000")

        job = await job_service.create_job(
            organization_id=organization_id,
            job_type=JobType.PORTAL_REMINDERS,
            job_name="Overdue Notifications",
            created_by=organization_id,
            input_data={"reminder_type": "overdue"},
        )

        runner = BackgroundJobRunner(session)
        result = await process_portal_reminders(job, runner)

        logger.info(f"Overdue notifications completed: {result}")
