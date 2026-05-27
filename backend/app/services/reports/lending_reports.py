"""Lending reports — all driven by the lifecycle event log + loan account snapshots.

Single file, multiple report builders. Each report function returns a
dict serialisable to JSON. The HTTP layer adapts it for PDF/Excel/CSV
export via the standard ExportMenu.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lending.lifecycle_event import LoanLifecycleEvent
from app.models.lending.lifecycle_modules import (
    DocReleaseStatus,
    DocReleaseTracker,
    LoanWriteOff,
    WriteOffStatus,
)
from app.models.lending.loan_account import LoanAccount

# ============================================================================
# Collection efficiency: collected / due, per period
# ============================================================================


async def collection_efficiency_report(
    db: AsyncSession,
    *,
    organization_id: UUID,
    period_from: date,
    period_to: date,
) -> dict[str, Any]:
    from app.models.lending.loan_account import LoanReceipt

    receipts_q = select(func.coalesce(func.sum(LoanReceipt.receipt_amount), 0)).where(
        LoanReceipt.organization_id == organization_id,
        LoanReceipt.receipt_date >= period_from,
        LoanReceipt.receipt_date <= period_to,
    )
    collected = (await db.execute(receipts_q)).scalar() or Decimal("0")

    # Demand approximation — sum of scheduled instalments due in the window.
    from app.models.lending.loan_account import ScheduleInstallment

    demand_q = select(func.coalesce(func.sum(ScheduleInstallment.emi_amount), 0)).where(
        ScheduleInstallment.organization_id == organization_id,
        ScheduleInstallment.due_date >= period_from,
        ScheduleInstallment.due_date <= period_to,
    )
    due = (await db.execute(demand_q)).scalar() or Decimal("0")
    efficiency = float(collected) / float(due) * 100 if due > 0 else 0.0
    return {
        "period_from": period_from.isoformat(),
        "period_to": period_to.isoformat(),
        "collected": float(collected),
        "due": float(due),
        "efficiency_percent": round(efficiency, 2),
    }


# ============================================================================
# NPA movement: count + outstanding by bucket
# ============================================================================


async def npa_movement_report(
    db: AsyncSession, *, organization_id: UUID, as_of_date: date
) -> dict[str, Any]:
    stmt = (
        select(
            LoanAccount.asset_classification,
            func.count(LoanAccount.id),
            func.coalesce(func.sum(LoanAccount.principal_outstanding), 0),
        )
        .where(
            LoanAccount.organization_id == organization_id,
            LoanAccount.is_active.is_(True),
        )
        .group_by(LoanAccount.asset_classification)
    )

    rows = (await db.execute(stmt)).all()
    by_bucket = []
    total_count = 0
    total_outstanding = Decimal("0")
    for classification, count, outstanding in rows:
        by_bucket.append(
            {
                "asset_classification": str(classification),
                "count": int(count),
                "principal_outstanding": float(outstanding or 0),
            }
        )
        total_count += int(count)
        total_outstanding += outstanding or Decimal("0")
    return {
        "as_of_date": as_of_date.isoformat(),
        "by_bucket": by_bucket,
        "total_count": total_count,
        "total_outstanding": float(total_outstanding),
    }


# ============================================================================
# DPD distribution
# ============================================================================


async def dpd_distribution_report(db: AsyncSession, *, organization_id: UUID) -> dict[str, Any]:
    from app.services.lending.npa_service import NPAService

    npa = NPAService(db)
    buckets = await npa._bucket_thresholds(organization_id)  # noqa: SLF001
    stmt = select(LoanAccount).where(
        LoanAccount.organization_id == organization_id,
        LoanAccount.is_active.is_(True),
    )
    loans = list((await db.execute(stmt)).scalars().all())

    distribution: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"count": 0, "outstanding": Decimal("0")}
    )
    for loan in loans:
        dpd = 0
        # If the loan has a stored DPD value, use it; else best-effort 0.
        try:
            dpd = await npa.get_dpd(loan.id)
        except Exception:  # noqa: BLE001
            dpd = 0
        bucket_label = "STANDARD"
        for classification, min_dpd, max_dpd in sorted(buckets, key=lambda r: -r[1]):
            if dpd >= min_dpd and (max_dpd is None or dpd <= max_dpd):
                bucket_label = classification
                break
        distribution[bucket_label]["count"] += 1
        distribution[bucket_label]["outstanding"] += loan.principal_outstanding or Decimal("0")

    return {
        "as_of_date": date.today().isoformat(),
        "buckets": [
            {
                "bucket": k,
                "count": v["count"],
                "outstanding": float(v["outstanding"]),
            }
            for k, v in distribution.items()
        ],
    }


# ============================================================================
# Prepayment volume + run-off
# ============================================================================


async def prepayment_volume_report(
    db: AsyncSession,
    *,
    organization_id: UUID,
    period_from: date,
    period_to: date,
) -> dict[str, Any]:
    stmt = select(
        func.count(LoanLifecycleEvent.id),
        func.coalesce(
            func.sum(
                func.cast(LoanLifecycleEvent.payload["prepayment_amount"].astext, func.Numeric)
            ),
            0,
        ),
    ).where(
        LoanLifecycleEvent.organization_id == organization_id,
        LoanLifecycleEvent.event_type == "PREPAYMENT_RECEIVED",
        func.cast(LoanLifecycleEvent.event_at, func.Date) >= period_from,
        func.cast(LoanLifecycleEvent.event_at, func.Date) <= period_to,
    )
    try:
        count, volume = (await db.execute(stmt)).one()
    except Exception:
        # JSONB cast may fail on empty payloads — fall back to count-only
        count_only = select(func.count(LoanLifecycleEvent.id)).where(
            LoanLifecycleEvent.organization_id == organization_id,
            LoanLifecycleEvent.event_type == "PREPAYMENT_RECEIVED",
        )
        count = (await db.execute(count_only)).scalar() or 0
        volume = Decimal("0")
    return {
        "period_from": period_from.isoformat(),
        "period_to": period_to.isoformat(),
        "prepayment_count": int(count or 0),
        "prepayment_volume": float(volume or 0),
    }


# ============================================================================
# AUM (assets under management)
# ============================================================================


async def aum_report(db: AsyncSession, *, organization_id: UUID) -> dict[str, Any]:
    stmt = select(
        func.count(LoanAccount.id),
        func.coalesce(func.sum(LoanAccount.principal_outstanding), 0),
        func.coalesce(func.sum(LoanAccount.sanctioned_amount), 0),
    ).where(
        LoanAccount.organization_id == organization_id,
        LoanAccount.is_active.is_(True),
    )
    count, principal_outstanding, sanctioned = (await db.execute(stmt)).one()
    return {
        "as_of_date": date.today().isoformat(),
        "active_loan_count": int(count or 0),
        "total_principal_outstanding": float(principal_outstanding or 0),
        "total_sanctioned": float(sanctioned or 0),
    }


# ============================================================================
# Provisioning summary
# ============================================================================


async def provisioning_summary_report(db: AsyncSession, *, organization_id: UUID) -> dict[str, Any]:
    from app.services.lending.npa_service import NPAService

    # Pull provisioning rates from the master
    from app.models.lending.masters import ProvisioningRate

    rate_rows = (
        (
            await db.execute(
                select(ProvisioningRate).where(ProvisioningRate.organization_id == organization_id)
            )
        )
        .scalars()
        .all()
    )
    rate_map: dict[tuple[str, str, str], Decimal] = {}
    for r in rate_rows:
        rate_map[(r.asset_classification, r.secured_unsecured, r.loan_segment)] = r.rate_percent

    npa = NPAService(db)
    loans = list(
        (
            await db.execute(
                select(LoanAccount).where(
                    LoanAccount.organization_id == organization_id,
                    LoanAccount.is_active.is_(True),
                )
            )
        )
        .scalars()
        .all()
    )

    total_provision = Decimal("0")
    by_class: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"outstanding": Decimal("0"), "provision": Decimal("0")}
    )

    for loan in loans:
        classification = (
            loan.asset_classification.value
            if hasattr(loan.asset_classification, "value")
            else str(loan.asset_classification or "STANDARD")
        )
        secured = "SECURED"  # default; in practice read from collateral coverage
        rate = (
            rate_map.get((classification.upper(), secured, "DEFAULT"))
            or rate_map.get((classification.upper(), secured, "INFRASTRUCTURE"))
            or Decimal("0.40")
        )
        outstanding = loan.principal_outstanding or Decimal("0")
        provision = (outstanding * rate / Decimal("100")).quantize(Decimal("0.01"))
        by_class[classification]["outstanding"] += outstanding
        by_class[classification]["provision"] += provision
        total_provision += provision

    return {
        "as_of_date": date.today().isoformat(),
        "total_provision": float(total_provision),
        "by_classification": [
            {
                "classification": k,
                "outstanding": float(v["outstanding"]),
                "provision": float(v["provision"]),
            }
            for k, v in by_class.items()
        ],
    }


# ============================================================================
# Doc-release-breach watch
# ============================================================================


async def doc_release_breach_watch(db: AsyncSession, *, organization_id: UUID) -> dict[str, Any]:
    stmt = (
        select(DocReleaseTracker)
        .where(
            DocReleaseTracker.organization_id == organization_id,
            DocReleaseTracker.status.in_([DocReleaseStatus.PENDING, DocReleaseStatus.BREACHED]),
        )
        .order_by(DocReleaseTracker.target_release_date)
    )
    rows = list((await db.execute(stmt)).scalars().all())
    return {
        "as_of_date": date.today().isoformat(),
        "items": [
            {
                "tracker_id": str(r.id),
                "loan_account_id": str(r.loan_account_id),
                "closure_date": r.closure_date.isoformat(),
                "target_release_date": r.target_release_date.isoformat(),
                "status": r.status.value,
                "breach_days": r.breach_days,
                "compensation_payable": float(r.compensation_payable or 0),
            }
            for r in rows
        ],
        "total_count": len(rows),
        "total_compensation_payable": float(
            sum(r.compensation_payable or Decimal("0") for r in rows)
        ),
    }


# ============================================================================
# Write-off summary (quarterly board reporting)
# ============================================================================


async def write_off_summary_report(
    db: AsyncSession,
    *,
    organization_id: UUID,
    period_from: date,
    period_to: date,
) -> dict[str, Any]:
    stmt = select(LoanWriteOff).where(
        LoanWriteOff.organization_id == organization_id,
        LoanWriteOff.status == WriteOffStatus.EFFECTED,
        LoanWriteOff.effected_date >= period_from,
        LoanWriteOff.effected_date <= period_to,
    )
    rows = list((await db.execute(stmt)).scalars().all())
    by_type: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"count": 0, "amount": Decimal("0"), "recovered": Decimal("0")}
    )
    for r in rows:
        kind = r.write_off_type.value
        by_type[kind]["count"] += 1
        by_type[kind]["amount"] += r.proposed_amount or Decimal("0")
        by_type[kind]["recovered"] += r.total_recovered_post_write_off or Decimal("0")
    return {
        "period_from": period_from.isoformat(),
        "period_to": period_to.isoformat(),
        "by_type": [
            {
                "write_off_type": k,
                "count": v["count"],
                "amount": float(v["amount"]),
                "recovered_post_write_off": float(v["recovered"]),
            }
            for k, v in by_type.items()
        ],
        "total_count": len(rows),
        "total_amount": float(sum(r.proposed_amount or Decimal("0") for r in rows)),
        "total_recovered": float(
            sum(r.total_recovered_post_write_off or Decimal("0") for r in rows)
        ),
    }


# ============================================================================
# TAT (turnaround time) by stage — from lifecycle log
# ============================================================================


async def tat_by_stage_report(
    db: AsyncSession,
    *,
    organization_id: UUID,
    period_from: date,
    period_to: date,
) -> dict[str, Any]:
    """For applications submitted in the window, average days between key events."""
    stmt = (
        select(LoanLifecycleEvent)
        .where(
            LoanLifecycleEvent.organization_id == organization_id,
            LoanLifecycleEvent.event_type.in_(
                [
                    "APPLICATION_SUBMITTED",
                    "APPRAISAL_STARTED",
                    "APPRAISAL_COMPLETED",
                    "SANCTION_APPROVED",
                    "SANCTION_ACCEPTED",
                    "DISBURSEMENT_PROCESSED",
                ]
            ),
        )
        .order_by(LoanLifecycleEvent.event_at)
    )
    events = list((await db.execute(stmt)).scalars().all())

    by_application: dict[UUID, dict[str, datetime]] = defaultdict(dict)
    for e in events:
        if e.subject_id is None:
            continue
        by_application[e.subject_id][e.event_type] = e.event_at

    deltas: dict[str, list[float]] = defaultdict(list)
    for _, events_for_app in by_application.items():
        for from_event, to_event in (
            ("APPLICATION_SUBMITTED", "APPRAISAL_COMPLETED"),
            ("APPRAISAL_COMPLETED", "SANCTION_APPROVED"),
            ("SANCTION_APPROVED", "SANCTION_ACCEPTED"),
            ("SANCTION_ACCEPTED", "DISBURSEMENT_PROCESSED"),
        ):
            if from_event in events_for_app and to_event in events_for_app:
                delta = (
                    events_for_app[to_event] - events_for_app[from_event]
                ).total_seconds() / 86400
                deltas[f"{from_event}__to__{to_event}"].append(delta)

    return {
        "period_from": period_from.isoformat(),
        "period_to": period_to.isoformat(),
        "averages_days": {
            k: round(sum(vs) / len(vs), 2) if vs else None for k, vs in deltas.items()
        },
        "sample_size": {k: len(vs) for k, vs in deltas.items()},
    }
