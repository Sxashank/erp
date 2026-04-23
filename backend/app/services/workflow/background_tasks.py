"""Background tasks for workflow processing."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings
from app.database import async_session_factory

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler: Optional[AsyncIOScheduler] = None


async def check_escalations_task():
    """Background task to check and process escalations."""
    logger.info("Running scheduled escalation check...")
    try:
        async with async_session_factory() as db:
            from app.services.workflow.escalation_service import EscalationService
            service = EscalationService(db)
            count = await service.check_and_escalate()
            logger.info(f"Escalation check completed. Processed {count} escalations.")
    except Exception as e:
        logger.error(f"Error in escalation check task: {e}")


async def send_daily_digest_task():
    """Background task to send daily approval digest."""
    logger.info("Running scheduled daily digest...")
    try:
        async with async_session_factory() as db:
            from app.services.workflow.escalation_service import EscalationService
            service = EscalationService(db)
            count = await service.send_daily_digest()
            logger.info(f"Daily digest completed. Sent {count} emails.")
    except Exception as e:
        logger.error(f"Error in daily digest task: {e}")


async def cleanup_old_instances_task():
    """Background task to cleanup old workflow instances."""
    logger.info("Running scheduled cleanup of old instances...")
    try:
        async with async_session_factory() as db:
            from app.services.workflow.escalation_service import EscalationService
            service = EscalationService(db)
            count = await service.cleanup_old_instances(days_old=90)
            logger.info(f"Cleanup completed. Archived {count} old instances.")
    except Exception as e:
        logger.error(f"Error in cleanup task: {e}")


async def compute_audit_anchors_job():
    """Background task: compute yesterday's audit hash-chain anchors.

    Every organization with audit activity on the target day gets one
    `audit_day_anchor` row. The NULL-org bucket (system-global audit)
    is included if present. Idempotent — re-running on an already-anchored
    day is a no-op update (see `hash_chain_service.persist_day_chain`).
    Scheduled at 00:15 IST via `setup_scheduler()` below.
    """
    from datetime import date, timedelta

    from app.services.audit.audit_log_loader import (
        distinct_org_ids_with_audit_rows,
        load_rows_by_day,
    )
    from app.services.audit.hash_chain_service import persist_day_chain

    target_day = date.today() - timedelta(days=1)
    logger.info(f"Running audit-chain anchor computation for {target_day.isoformat()}")
    try:
        async with async_session_factory() as db:
            org_ids = await distinct_org_ids_with_audit_rows(db, target_day=target_day)
            if not org_ids:
                logger.info("No audit rows for target day; skipping anchor job.")
                return
            for org_id in org_ids:
                rows_by_day = await load_rows_by_day(
                    db,
                    organization_id=org_id,
                    start_day=target_day,
                    end_day=target_day,
                )
                await persist_day_chain(
                    db, organization_id=org_id, rows_by_day=rows_by_day
                )
            logger.info(
                f"Audit anchors persisted for {len(org_ids)} organization(s) on {target_day}."
            )
    except Exception as e:
        logger.error(f"Error in audit-chain anchor job: {e}")


def setup_scheduler() -> AsyncIOScheduler:
    """
    Setup and configure the background task scheduler.

    Returns:
        Configured AsyncIOScheduler instance
    """
    global scheduler

    if scheduler is not None:
        return scheduler

    scheduler = AsyncIOScheduler()

    # Escalation check - runs every N minutes
    escalation_interval = settings.WORKFLOW_ESCALATION_CHECK_MINUTES
    scheduler.add_job(
        check_escalations_task,
        trigger=IntervalTrigger(minutes=escalation_interval),
        id="workflow_escalation_check",
        name="Check workflow escalations",
        replace_existing=True,
    )
    logger.info(f"Scheduled escalation check every {escalation_interval} minutes")

    # Daily digest - runs at configured hour
    digest_hour = settings.WORKFLOW_DIGEST_HOUR
    scheduler.add_job(
        send_daily_digest_task,
        trigger=CronTrigger(hour=digest_hour, minute=0),
        id="workflow_daily_digest",
        name="Send daily approval digest",
        replace_existing=True,
    )
    logger.info(f"Scheduled daily digest at {digest_hour}:00")

    # Weekly cleanup - runs every Sunday at 2 AM
    scheduler.add_job(
        cleanup_old_instances_task,
        trigger=CronTrigger(day_of_week="sun", hour=2, minute=0),
        id="workflow_cleanup",
        name="Cleanup old workflow instances",
        replace_existing=True,
    )
    logger.info("Scheduled weekly cleanup on Sundays at 2:00 AM")

    # Daily audit-chain anchor computation — 00:15 IST. IST = UTC+5:30, so
    # 00:15 IST = 18:45 UTC the previous day. APScheduler CronTrigger
    # honors the process TZ; we pass UTC explicitly to stay deterministic.
    scheduler.add_job(
        compute_audit_anchors_job,
        trigger=CronTrigger(hour=18, minute=45, timezone="UTC"),
        id="audit_chain_anchors",
        name="Compute daily audit hash-chain anchors",
        replace_existing=True,
    )
    logger.info("Scheduled audit-chain anchor computation at 18:45 UTC (00:15 IST)")

    return scheduler


def start_scheduler():
    """Start the background task scheduler."""
    global scheduler

    if scheduler is None:
        scheduler = setup_scheduler()

    if not scheduler.running:
        scheduler.start()
        logger.info("Workflow background scheduler started")


def stop_scheduler():
    """Stop the background task scheduler."""
    global scheduler

    if scheduler is not None and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Workflow background scheduler stopped")


@asynccontextmanager
async def lifespan_scheduler():
    """
    Context manager for scheduler lifecycle.

    Use with FastAPI lifespan:

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        async with lifespan_scheduler():
            yield
    """
    start_scheduler()
    try:
        yield
    finally:
        stop_scheduler()


async def run_escalation_check_now():
    """
    Manually trigger an escalation check.

    Useful for testing or admin-triggered checks.
    """
    await check_escalations_task()


async def run_daily_digest_now():
    """
    Manually trigger daily digest.

    Useful for testing or admin-triggered digests.
    """
    await send_daily_digest_task()
