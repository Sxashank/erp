"""Arq worker unit tests.

These test the job handlers + registry without Redis. A full redis-backed
end-to-end test requires a running redis container and is deferred to
Stage 6-PENDING.

CLAUDE.md §6.6.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.workers import arq_worker


# ---------------------------------------------------------------------------
# Registry invariants.
# ---------------------------------------------------------------------------

def test_every_registered_function_is_a_coroutine() -> None:
    import inspect

    for fn in arq_worker.FUNCTIONS:
        assert inspect.iscoroutinefunction(fn), f"{fn.__name__} must be async"


def test_worker_settings_exposes_required_fields() -> None:
    assert arq_worker.WorkerSettings.functions is arq_worker.FUNCTIONS
    assert arq_worker.WorkerSettings.max_tries == 3
    assert arq_worker.WorkerSettings.job_timeout == 600
    assert arq_worker.WorkerSettings.max_jobs == 10


def test_registered_function_names_are_unique() -> None:
    names = [fn.__name__ for fn in arq_worker.FUNCTIONS]
    assert len(names) == len(set(names))


def test_critical_jobs_are_registered() -> None:
    """The plan gate requires these specific fan-out jobs. If any is
    accidentally removed, this test surfaces it."""
    names = {fn.__name__ for fn in arq_worker.FUNCTIONS}
    required = {
        "reclassify_npa_batch",
        "run_payroll_batch",
        "notification_fanout",
        "export_crilc_monthly",
        "generate_gstr_dump",
        "fa_bulk_import",
        "portal_daily_reminders",
    }
    missing = required - names
    assert not missing, f"Missing registered jobs: {missing}"


# ---------------------------------------------------------------------------
# Job bodies — each can be called with a fake ctx.
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_notification_fanout_counts_per_recipient() -> None:
    ctx = {"job_id": "test-1"}
    result = await arq_worker.notification_fanout(
        ctx,
        template_code="EMI_DUE",
        recipient_ids=["r1", "r2", "r3"],
    )
    assert result == {"sent": 3, "failed": 0, "total": 3}


@pytest.mark.asyncio
async def test_notification_fanout_empty_list() -> None:
    result = await arq_worker.notification_fanout(
        {"job_id": "test-2"},
        template_code="EMI_DUE",
        recipient_ids=[],
    )
    assert result == {"sent": 0, "failed": 0, "total": 0}


@pytest.mark.asyncio
async def test_export_crilc_monthly_returns_pending_status() -> None:
    out = await arq_worker.export_crilc_monthly(
        {"job_id": "t"}, organization_id="org-1", year_month="2026-04"
    )
    assert out["organization_id"] == "org-1"
    assert out["year_month"] == "2026-04"
    assert out["status"] == "pending_service_impl"


@pytest.mark.asyncio
async def test_generate_gstr_dump_returns_pending_status() -> None:
    out = await arq_worker.generate_gstr_dump(
        {"job_id": "t"},
        gstin="27AAAAA0000A1Z5",
        return_period="042026",
        return_type="GSTR1",
    )
    assert out["return_type"] == "GSTR1"
    assert out["status"] == "pending_service_impl"


@pytest.mark.asyncio
async def test_run_payroll_batch_delegates_to_payroll_processing_service() -> None:
    """STAGE-6-PENDING-payroll-batch closure — job delegates to
    PayrollProcessingService.process_payroll and returns structured result."""
    from types import SimpleNamespace

    fake_session_ctx = MagicMock()
    fake_session_ctx.__aenter__ = AsyncMock(return_value=MagicMock())
    fake_session_ctx.__aexit__ = AsyncMock(return_value=False)
    fake_factory = MagicMock(return_value=fake_session_ctx)

    fake_batch = SimpleNamespace(
        status=SimpleNamespace(value="PROCESSED"),
        total_employees=42,
        total_net="425000.00",
    )

    with patch("app.workers.arq_worker._session_factory", return_value=fake_factory):
        with patch(
            "app.services.payroll.payroll_service.PayrollProcessingService"
        ) as svc_cls:
            svc_instance = svc_cls.return_value
            svc_instance.process_payroll = AsyncMock(return_value=fake_batch)
            batch_id = str(uuid4())
            out = await arq_worker.run_payroll_batch(
                {"job_id": "t"},
                batch_id=batch_id,
            )
            svc_instance.process_payroll.assert_awaited_once()

    assert out["batch_id"] == batch_id
    assert out["status"] == "PROCESSED"
    assert out["total_employees"] == 42
    assert out["total_net"] == "425000.00"


@pytest.mark.asyncio
async def test_reclassify_npa_batch_delegates_to_service() -> None:
    """Patch `NPAService.run_npa_classification` and assert it gets called
    with the right args."""
    # Stub out async_session_factory so we don't hit a real DB.
    fake_session_ctx = MagicMock()
    fake_session_ctx.__aenter__ = AsyncMock(return_value=MagicMock())
    fake_session_ctx.__aexit__ = AsyncMock(return_value=False)

    fake_factory = MagicMock(return_value=fake_session_ctx)
    with patch("app.workers.arq_worker._session_factory", return_value=fake_factory):
        with patch("app.services.lending.npa_service.NPAService") as svc_cls:
            svc_instance = svc_cls.return_value
            svc_instance.run_npa_classification = AsyncMock(
                return_value={"classifications": {"standard": 5}}
            )
            org = uuid4()
            out = await arq_worker.reclassify_npa_batch(
                {"job_id": "t"},
                organization_id=str(org),
                as_of_date="2026-04-22",
            )
            assert out["classifications"]["standard"] == 5
            svc_instance.run_npa_classification.assert_awaited_once()


@pytest.mark.asyncio
async def test_notification_fanout_handles_per_recipient_failure() -> None:
    """Monkey-patch the inner logger.info to raise for one recipient —
    the job should keep going and count the failure."""
    ctx = {"job_id": "t"}
    call_count = {"n": 0}

    original_info = arq_worker.logger.info

    def flaky_info(event: str, **kwargs) -> None:
        if event == "notification_dispatch":
            call_count["n"] += 1
            if call_count["n"] == 2:
                raise RuntimeError("provider down")
        return original_info(event, **kwargs)

    with patch.object(arq_worker.logger, "info", side_effect=flaky_info):
        result = await arq_worker.notification_fanout(
            ctx,
            template_code="EMI_DUE",
            recipient_ids=["r1", "r2", "r3"],
        )
    assert result["total"] == 3
    assert result["failed"] == 1
    assert result["sent"] == 2


# ---------------------------------------------------------------------------
# enqueue() producer wrapper.
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_enqueue_forwards_job_id_and_defer() -> None:
    fake_pool = MagicMock()
    fake_job = MagicMock()
    fake_job.job_id = "job-xyz"
    fake_pool.enqueue_job = AsyncMock(return_value=fake_job)

    with patch("app.workers.arq_worker.get_arq_pool", return_value=fake_pool):
        out = await arq_worker.enqueue(
            "notification_fanout",
            "EMI_DUE",
            ["r1"],
            _job_id="dedupe-key-1",
            _defer_by_seconds=60,
        )
    assert out == "job-xyz"
    fake_pool.enqueue_job.assert_awaited_once()
    call_kwargs = fake_pool.enqueue_job.await_args.kwargs
    assert call_kwargs["_job_id"] == "dedupe-key-1"
    assert call_kwargs["_defer_by"].total_seconds() == 60


@pytest.mark.asyncio
async def test_enqueue_returns_none_on_duplicate() -> None:
    """Arq's enqueue_job returns None if a job with the same _job_id is
    already queued — our wrapper propagates that."""
    fake_pool = MagicMock()
    fake_pool.enqueue_job = AsyncMock(return_value=None)

    with patch("app.workers.arq_worker.get_arq_pool", return_value=fake_pool):
        out = await arq_worker.enqueue(
            "notification_fanout",
            "EMI_DUE",
            ["r1"],
            _job_id="dedupe-key-1",
        )
    assert out is None


def test_redis_settings_parses_from_dsn() -> None:
    settings = arq_worker._redis_settings()
    assert settings is not None
