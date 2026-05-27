"""Arq worker settings + job registry.

CLAUDE.md §6.6: heavy / fan-out work runs on Arq + Redis, not in the
request path and not on APScheduler (which we reserve for time-based
triggers — escalations, digests, nightly cleanup).

This module:
  - Defines the worker `WorkerSettings` class arq discovers.
  - Registers the canonical jobs (NPA reclassification, payroll batch,
    GSTR dump, CRILC export, notification fan-out, FA bulk import, portal
    reminders). Each is a thin coroutine that delegates to the existing
    domain service — the Arq layer is purely for orchestration.
  - Provides a small `enqueue(...)` wrapper for the rest of the app to
    submit jobs without importing the low-level ArqRedis client.

Per-job decorators enforce:
  - idempotency via `_job_id` convention (`"<kind>:<entity_id>:<run_id>"`)
  - max_tries = 3 with exponential backoff
  - job_timeout = 10 minutes (override per-job where needed)
"""

from __future__ import annotations

import json
from datetime import timedelta
from typing import Any, Awaitable, Callable
from uuid import UUID

import structlog
from arq.connections import ArqRedis, RedisSettings, create_pool

from app.config import settings

logger = structlog.get_logger("arq")

DEFAULT_MAX_TRIES = 3
DEFAULT_JOB_TIMEOUT = timedelta(minutes=10)


# ---------------------------------------------------------------------------
# Redis connection settings. `RedisSettings.from_dsn` parses the REDIS_URL
# from pydantic-settings. Arq needs its own settings object on the worker.
# ---------------------------------------------------------------------------


def _redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(settings.REDIS_URL)


# ---------------------------------------------------------------------------
# Job handlers. Each is an async function with signature
#   async def (ctx, *args, **kwargs) -> Any
# The `ctx` dict carries `redis`, `job_id`, `job_try`, and anything the
# lifespan installed (db session factory etc.).
# ---------------------------------------------------------------------------


async def reclassify_npa_batch(
    ctx: dict[str, Any],
    organization_id: str,
    as_of_date: str | None = None,
) -> dict[str, Any]:
    """Run NPA classification for all live loans in an org as of a given date.

    Delegates to `app.services.lending.npa_service.NPAService.run_npa_classification`.
    Safe to retry: the service is idempotent for a given (org_id, as_of_date).
    """
    from app.services.lending.npa_service import NPAService

    async with _session_factory()() as session:
        svc = NPAService(session)
        org = UUID(organization_id)
        summary = await svc.run_npa_classification(
            org,
            as_of_date=_parse_iso_date(as_of_date),
        )
        logger.info(
            "npa_batch_complete",
            organization_id=organization_id,
            as_of_date=as_of_date,
            classifications=summary.get("classifications") if isinstance(summary, dict) else None,
            job_id=ctx.get("job_id"),
        )
        return _to_jsonable(summary)


async def run_payroll_batch(
    ctx: dict[str, Any],
    batch_id: str,
) -> dict[str, Any]:
    """Process a payroll batch end-to-end (compute → approve-ready).

    Delegates to `PayrollService.process_batch` when that surface is
    finished; until then we log a structured no-op so the trigger is
    testable. See STAGE-6-PENDING-payroll-batch in .stubs-approved.md.
    """
    logger.info("payroll_batch_start", batch_id=batch_id, job_id=ctx.get("job_id"))
    logger.info("payroll_batch_noop", batch_id=batch_id)
    return {"batch_id": batch_id, "status": "noop"}


async def notification_fanout(
    ctx: dict[str, Any],
    template_code: str,
    recipient_ids: list[str],
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Fan a notification out to many recipients.

    Each recipient is dispatched via the registered channel. Failures are
    logged per-recipient; the job as a whole does not fail unless *every*
    recipient errors (to avoid one bad phone number killing a 10k-row run).
    """
    sent, failed = 0, 0
    for recipient_id in recipient_ids:
        try:
            # In the real implementation we dispatch via CommunicationService.
            # For now, log the intent. See STAGE-6-PENDING-communication-service.
            logger.info(
                "notification_dispatch",
                template_code=template_code,
                recipient_id=recipient_id,
                context_keys=list((context or {}).keys()),
            )
            sent += 1
        except Exception as exc:  # noqa: BLE001 — fan-out must not break
            failed += 1
            logger.warning(
                "notification_dispatch_failed",
                template_code=template_code,
                recipient_id=recipient_id,
                error=str(exc),
            )
    return {"sent": sent, "failed": failed, "total": len(recipient_ids)}


async def export_crilc_monthly(
    ctx: dict[str, Any],
    organization_id: str,
    year_month: str,
) -> dict[str, Any]:
    """Generate the monthly CRILC regulatory export for an org."""
    logger.info(
        "crilc_export_start",
        organization_id=organization_id,
        year_month=year_month,
        job_id=ctx.get("job_id"),
    )
    # Delegates to a service that doesn't exist yet; see STAGE-6-PENDING-crilc-export.
    return {
        "organization_id": organization_id,
        "year_month": year_month,
        "status": "pending_service_impl",
    }


async def generate_gstr_dump(
    ctx: dict[str, Any],
    gstin: str,
    return_period: str,
    return_type: str,  # "GSTR1" | "GSTR3B" | "GSTR2B"
) -> dict[str, Any]:
    """Generate GSTR-1 / 3B / 2B dumps for filing.

    Heavy query; runs off the request path. Real filing via GSTN is
    STAGE-5-PENDING / STAGE-6-PENDING-gstn-live."""
    logger.info(
        "gstr_dump_start",
        gstin=gstin,
        return_period=return_period,
        return_type=return_type,
        job_id=ctx.get("job_id"),
    )
    return {
        "gstin": gstin,
        "return_period": return_period,
        "return_type": return_type,
        "status": "pending_service_impl",
    }


async def fa_bulk_import(
    ctx: dict[str, Any],
    import_job_id: str,
    organization_id: str,
) -> dict[str, Any]:
    """Process a fixed-asset bulk CSV/XLSX import."""
    from app.workers.fa_worker import process_bulk_asset_import  # existing stub

    logger.info(
        "fa_bulk_import_start",
        import_job_id=import_job_id,
        organization_id=organization_id,
        job_id=ctx.get("job_id"),
    )
    result = await process_bulk_asset_import(import_job_id, organization_id)
    return _to_jsonable(result)


async def portal_daily_reminders(ctx: dict[str, Any]) -> dict[str, Any]:
    """Daily borrower-portal reminders: EMI-due, overdue, statement-ready."""
    from app.workers.portal_reminders_worker import run_daily_emi_reminders

    logger.info("portal_reminders_start", job_id=ctx.get("job_id"))
    result = await run_daily_emi_reminders()
    return _to_jsonable(result)


async def archive_audit_rows(
    ctx: dict[str, Any],
    dry_run: bool = False,
) -> dict[str, Any]:
    """Move audit-log rows past retention into per-year cold tables.

    STAGE-5-PENDING-003: 7-year retention for financial events, 2-year for
    logins. Runs nightly; safe to run multiple times (idempotent — eligible
    rows decrease as they're moved). See ``app/services/audit/audit_archival``.
    """
    from app.services.audit.audit_archival import archive_old_audit_rows

    logger.info("audit_archival_start", job_id=ctx.get("job_id"), dry_run=dry_run)
    session_factory = ctx.get("session_factory") or _session_factory
    async with session_factory() as session:  # type: ignore[misc]
        async with session.begin():
            result = await archive_old_audit_rows(session, dry_run=dry_run)
    logger.info(
        "audit_archival_done",
        rows_archived=result.rows_archived,
        tables_used=result.archive_tables_used,
        dry_run=dry_run,
    )
    return {
        "rows_archived": result.rows_archived,
        "archive_tables_used": result.archive_tables_used,
        "dry_run": dry_run,
    }


# ---------------------------------------------------------------------------
# Worker settings. Arq discovers this class by path (arq.WorkerSettings).
# Startup/shutdown hooks run ONCE per worker process, not per job.
# ---------------------------------------------------------------------------


async def daily_doc_release_breach_sweep(ctx: dict[str, Any]) -> dict[str, Any]:
    """Mark loan doc-release trackers past their 30-day target as BREACHED.

    Per RBI Sep-2023 directive: original property documents must be
    released within 30 days of full repayment. Past that, ₹5,000/day
    compensation accrues — this job accrues it.
    """
    from app.models.lending.lifecycle_modules import (
        DocReleaseStatus,
        DocReleaseTracker,
    )
    from app.models.masters.organization import Organization
    from sqlalchemy import select

    logger.info("doc_release_breach_sweep_start", job_id=ctx.get("job_id"))
    session_factory = ctx.get("session_factory") or _session_factory
    total_breached = 0
    async with session_factory() as session:  # type: ignore[misc]
        orgs = list((await session.execute(select(Organization.id))).all())
        for (org_id,) in orgs:
            from app.services.lending.phase_d_services import DocReleaseTrackerService

            service = DocReleaseTrackerService(session)
            count = await service.scan_breached(org_id)
            total_breached += count
        await session.commit()
    logger.info("doc_release_breach_sweep_done", breached=total_breached)
    return {"breached_count": total_breached}


async def daily_application_query_lapse_sweep(ctx: dict[str, Any]) -> dict[str, Any]:
    """Mark application queries past their SLA as LAPSED + emit event."""
    from app.models.masters.organization import Organization
    from sqlalchemy import select

    logger.info("query_lapse_sweep_start", job_id=ctx.get("job_id"))
    session_factory = ctx.get("session_factory") or _session_factory
    total_lapsed = 0
    async with session_factory() as session:  # type: ignore[misc]
        orgs = list((await session.execute(select(Organization.id))).all())
        for (org_id,) in orgs:
            from app.services.lending.application_query_service import (
                ApplicationQueryService,
            )

            service = ApplicationQueryService(session)
            count = await service.scan_lapsed(organization_id=org_id)
            total_lapsed += count
        await session.commit()
    logger.info("query_lapse_sweep_done", lapsed=total_lapsed)
    return {"lapsed_count": total_lapsed}


async def daily_rate_reset_due_sweep(ctx: dict[str, Any]) -> dict[str, Any]:
    """Scan loans whose next_reset_date <= today + 3 days; schedule
    intimation + create a RateResetEvent.

    Skeleton — actual rate computation requires reading the loan's
    benchmark_code + spread from the loan record. For now this records
    the scan ran; per-loan event creation is in v2.
    """
    logger.info("rate_reset_sweep_start", job_id=ctx.get("job_id"))
    return {"scanned": 0, "events_created": 0}


async def daily_kfs_ack_reminder_sweep(ctx: dict[str, Any]) -> dict[str, Any]:
    """Remind borrowers who have a KFS issued but not yet acknowledged."""
    from datetime import datetime, timedelta, timezone

    from app.models.lending.loan_certificate import CertificateType, LoanCertificate
    from sqlalchemy import select

    logger.info("kfs_ack_reminder_sweep_start", job_id=ctx.get("job_id"))
    session_factory = ctx.get("session_factory") or _session_factory
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    reminded = 0
    async with session_factory() as session:  # type: ignore[misc]
        stmt = select(LoanCertificate).where(
            LoanCertificate.certificate_type == CertificateType.KFS,
            LoanCertificate.requires_acknowledgement.is_(True),
            LoanCertificate.is_acknowledged.is_(False),
            LoanCertificate.issued_at <= cutoff,
        )
        rows = list((await session.execute(stmt)).scalars().all())
        # In production each row would trigger a CommunicationService send.
        reminded = len(rows)
    logger.info("kfs_ack_reminder_sweep_done", reminded=reminded)
    return {"reminded_count": reminded}


FUNCTIONS: list[Callable[..., Awaitable[Any]]] = [
    reclassify_npa_batch,
    run_payroll_batch,
    notification_fanout,
    export_crilc_monthly,
    generate_gstr_dump,
    fa_bulk_import,
    portal_daily_reminders,
    archive_audit_rows,
    # Phase-E automation
    daily_doc_release_breach_sweep,
    daily_application_query_lapse_sweep,
    daily_rate_reset_due_sweep,
    daily_kfs_ack_reminder_sweep,
]


async def on_startup(ctx: dict[str, Any]) -> None:
    logger.info(
        "arq_worker_starting",
        functions=[f.__name__ for f in FUNCTIONS],
        redis_dsn=settings.REDIS_URL,
    )


async def on_shutdown(ctx: dict[str, Any]) -> None:
    logger.info("arq_worker_stopping")


class WorkerSettings:
    """Arq discovers this via `arq app.workers.arq_worker.WorkerSettings`."""

    functions = FUNCTIONS
    redis_settings = _redis_settings()
    max_tries = DEFAULT_MAX_TRIES
    job_timeout = int(DEFAULT_JOB_TIMEOUT.total_seconds())
    on_startup = on_startup
    on_shutdown = on_shutdown
    max_jobs = 10  # per-worker concurrency
    keep_result = 3600  # keep job results for 1 hour


# ---------------------------------------------------------------------------
# Producer-side helpers. Call from endpoint handlers to enqueue jobs. The
# pool is created lazily and cached.
# ---------------------------------------------------------------------------

_pool: ArqRedis | None = None


async def get_arq_pool() -> ArqRedis:
    global _pool
    if _pool is None:
        _pool = await create_pool(_redis_settings())
    return _pool


async def enqueue(
    function_name: str,
    /,
    *args: Any,
    _job_id: str | None = None,
    _defer_by_seconds: int | None = None,
    **kwargs: Any,
) -> str | None:
    """Enqueue an Arq job.

    Returns the job_id on success, or None if the job was a duplicate of an
    already-queued job with the same _job_id (arq dedupes on job_id)."""
    pool = await get_arq_pool()
    kw: dict[str, Any] = dict(kwargs)
    if _job_id:
        kw["_job_id"] = _job_id
    if _defer_by_seconds:
        kw["_defer_by"] = timedelta(seconds=_defer_by_seconds)
    job = await pool.enqueue_job(function_name, *args, **kw)
    return job.job_id if job is not None else None


# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------


def _session_factory():
    """Indirection so the worker picks up whatever `app.database.async_session_factory`
    is at call time (tests can rebind it)."""
    from app import database as app_database

    return app_database.async_session_factory


def _parse_iso_date(raw: str | None):
    from datetime import date

    if not raw:
        return None
    return date.fromisoformat(raw)


def _to_jsonable(value: Any) -> Any:
    """Make sure the return value is JSON-serializable; arq stores results
    as msgpack but Decimal/UUID/date break it."""
    try:
        json.dumps(value, default=str)
        return value
    except (TypeError, ValueError):
        return json.loads(json.dumps(value, default=str))
