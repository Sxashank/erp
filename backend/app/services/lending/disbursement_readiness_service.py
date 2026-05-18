"""Manual-first disbursement readiness cockpit service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lending.application import LoanApplication
from app.models.lending.checklist.loan_checklist import LoanChecklist, LoanChecklistItem
from app.models.lending.entity import Entity
from app.models.lending.enums import DisbursementStatus, SanctionStatus
from app.models.lending.loan_account import Disbursement, LoanAccount
from app.models.lending.sanction import LoanSanction
from app.schemas.lending.disbursement_readiness import (
    DisbursementReadinessResponse,
    DisbursementReadinessSummary,
    PendingDisbursementItem,
    ReadinessBlockerItem,
    ReadinessBucketMetric,
)

MONEY = Decimal("0.01")
READY_SANCTION_STATUSES = (
    SanctionStatus.APPROVED,
    SanctionStatus.ACCEPTED,
    SanctionStatus.ACTIVE,
)
PENDING_DISBURSEMENT_STATUSES = (
    DisbursementStatus.PENDING,
    DisbursementStatus.APPROVED,
)
CHECKLIST_CLOSED_STATUSES = ("MET", "WAIVED", "NOT_APPLICABLE")


@dataclass(frozen=True)
class SanctionReadinessRow:
    """Internal row for readiness calculations."""

    sanction_id: UUID
    sanction_number: str
    application_id: UUID
    application_number: str
    borrower_name: str
    project_name: str | None
    sanctioned_amount: Decimal
    disbursed_amount: Decimal
    validity_date: date | None
    first_disbursement_deadline: date | None
    status: str
    pending_disbursement_amount: Decimal


class DisbursementReadinessService:
    """Builds sanctioned-not-disbursed and manual disbursement control metrics."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_cockpit(
        self,
        organization_id: UUID,
        *,
        limit: int = 10,
    ) -> DisbursementReadinessResponse:
        today = date.today()
        sanction_rows = await self._sanction_rows(organization_id)
        application_ids = [row.application_id for row in sanction_rows]
        checklist_pending = await self._checklist_pending_by_application(application_ids, today)

        blockers: list[ReadinessBlockerItem] = []
        bucket_totals = {
            "ready": {
                "label": "Ready for manual disbursement",
                "count": 0,
                "amount": Decimal("0"),
            },
            "condition_blocked": {
                "label": "Condition blocked",
                "count": 0,
                "amount": Decimal("0"),
            },
            "expired": {"label": "Validity expired", "count": 0, "amount": Decimal("0")},
        }

        for row in sanction_rows:
            undisbursed_amount = self._money(row.sanctioned_amount - row.disbursed_amount)
            if undisbursed_amount <= 0:
                continue

            pending_count, overdue_count = checklist_pending.get(row.application_id, (0, 0))
            readiness_status = self._readiness_status(row, pending_count, today)
            bucket = bucket_totals[readiness_status]
            bucket["count"] += 1
            bucket["amount"] = self._money(bucket["amount"] + undisbursed_amount)

            blockers.append(
                ReadinessBlockerItem(
                    sanction_id=row.sanction_id,
                    sanction_number=row.sanction_number,
                    application_id=row.application_id,
                    application_number=row.application_number,
                    borrower_name=row.borrower_name,
                    project_name=row.project_name,
                    sanctioned_amount=self._money(row.sanctioned_amount),
                    undisbursed_amount=undisbursed_amount,
                    validity_date=row.validity_date.isoformat() if row.validity_date else None,
                    first_disbursement_deadline=(
                        row.first_disbursement_deadline.isoformat()
                        if row.first_disbursement_deadline
                        else None
                    ),
                    status=row.status,
                    readiness_status=readiness_status,
                    mandatory_pending=pending_count,
                    mandatory_overdue=overdue_count,
                    pending_disbursement_amount=self._money(row.pending_disbursement_amount),
                )
            )

        pending_disbursements = await self._pending_disbursement_items(organization_id, limit)
        pending_totals = await self._pending_disbursement_totals(organization_id)
        processed_this_month_amount = await self._processed_this_month_amount(
            organization_id,
            today,
        )

        buckets = [
            ReadinessBucketMetric(
                bucket=bucket,
                label=str(values["label"]),
                count=int(values["count"]),
                amount=self._money(values["amount"]),
            )
            for bucket, values in bucket_totals.items()
        ]

        blockers.sort(
            key=lambda item: (
                item.readiness_status != "condition_blocked",
                item.readiness_status != "expired",
                -item.mandatory_overdue,
                -item.mandatory_pending,
                str(item.first_disbursement_deadline or item.validity_date or ""),
            )
        )

        return DisbursementReadinessResponse(
            summary=DisbursementReadinessSummary(
                sanctioned_not_disbursed_count=sum(bucket.count for bucket in buckets),
                sanctioned_not_disbursed_amount=self._money(
                    sum((bucket.amount for bucket in buckets), Decimal("0"))
                ),
                ready_count=int(bucket_totals["ready"]["count"]),
                ready_amount=self._money(bucket_totals["ready"]["amount"]),
                condition_blocked_count=int(bucket_totals["condition_blocked"]["count"]),
                condition_blocked_amount=self._money(bucket_totals["condition_blocked"]["amount"]),
                expired_count=int(bucket_totals["expired"]["count"]),
                expired_amount=self._money(bucket_totals["expired"]["amount"]),
                pending_disbursement_count=pending_totals["pending_count"],
                pending_disbursement_amount=pending_totals["pending_amount"],
                approved_pending_processing_count=pending_totals["approved_count"],
                approved_pending_processing_amount=pending_totals["approved_amount"],
                processed_this_month_amount=processed_this_month_amount,
            ),
            readiness_buckets=buckets,
            blockers=blockers[:limit],
            pending_disbursements=pending_disbursements,
        )

    async def _sanction_rows(self, organization_id: UUID) -> list[SanctionReadinessRow]:
        disbursed_amount = func.coalesce(LoanAccount.total_disbursed_amount, 0)
        pending_disbursement_amount = func.coalesce(
            func.sum(
                func.coalesce(Disbursement.approved_amount, Disbursement.requested_amount)
            ).filter(Disbursement.status.in_(PENDING_DISBURSEMENT_STATUSES)),
            0,
        )

        result = await self.db.execute(
            select(
                LoanSanction.id,
                LoanSanction.sanction_number,
                LoanApplication.id,
                LoanApplication.application_number,
                Entity.legal_name,
                LoanApplication.project_name,
                LoanSanction.sanctioned_amount,
                disbursed_amount,
                LoanSanction.validity_date,
                LoanSanction.first_disbursement_deadline,
                LoanSanction.status,
                pending_disbursement_amount,
            )
            .join(LoanApplication, LoanApplication.id == LoanSanction.application_id)
            .join(Entity, Entity.id == LoanSanction.entity_id)
            .outerjoin(LoanAccount, LoanAccount.sanction_id == LoanSanction.id)
            .outerjoin(Disbursement, Disbursement.loan_account_id == LoanAccount.id)
            .where(
                LoanSanction.organization_id == organization_id,
                LoanSanction.deleted_at.is_(None),
                LoanApplication.deleted_at.is_(None),
                Entity.deleted_at.is_(None),
                LoanSanction.status.in_(READY_SANCTION_STATUSES),
            )
            .group_by(
                LoanSanction.id,
                LoanApplication.id,
                Entity.id,
                LoanAccount.total_disbursed_amount,
            )
        )

        return [
            SanctionReadinessRow(
                sanction_id=row[0],
                sanction_number=row[1],
                application_id=row[2],
                application_number=row[3],
                borrower_name=row[4],
                project_name=row[5],
                sanctioned_amount=row[6] or Decimal("0"),
                disbursed_amount=row[7] or Decimal("0"),
                validity_date=row[8],
                first_disbursement_deadline=row[9],
                status=row[10].value if hasattr(row[10], "value") else str(row[10]),
                pending_disbursement_amount=row[11] or Decimal("0"),
            )
            for row in result.all()
        ]

    async def _checklist_pending_by_application(
        self,
        application_ids: list[UUID],
        today: date,
    ) -> dict[UUID, tuple[int, int]]:
        if not application_ids:
            return {}

        result = await self.db.execute(
            select(
                LoanChecklist.application_id,
                func.count(LoanChecklistItem.id),
                func.count(LoanChecklistItem.id).filter(LoanChecklistItem.due_date < today),
            )
            .join(LoanChecklistItem, LoanChecklistItem.checklist_id == LoanChecklist.id)
            .where(
                LoanChecklist.application_id.in_(application_ids),
                LoanChecklist.deleted_at.is_(None),
                LoanChecklistItem.deleted_at.is_(None),
                LoanChecklistItem.is_mandatory.is_(True),
                LoanChecklistItem.status.notin_(CHECKLIST_CLOSED_STATUSES),
            )
            .group_by(LoanChecklist.application_id)
        )
        return {row[0]: (int(row[1] or 0), int(row[2] or 0)) for row in result.all()}

    async def _pending_disbursement_items(
        self,
        organization_id: UUID,
        limit: int,
    ) -> list[PendingDisbursementItem]:
        result = await self.db.execute(
            select(
                Disbursement.id,
                LoanAccount.id,
                LoanAccount.loan_account_number,
                Entity.legal_name,
                Disbursement.disbursement_reference,
                Disbursement.requested_amount,
                Disbursement.approved_amount,
                Disbursement.scheduled_date,
                Disbursement.request_date,
                Disbursement.status,
                Disbursement.conditions_verified,
                Disbursement.utr_number,
            )
            .join(LoanAccount, LoanAccount.id == Disbursement.loan_account_id)
            .join(Entity, Entity.id == LoanAccount.entity_id)
            .where(
                LoanAccount.organization_id == organization_id,
                LoanAccount.deleted_at.is_(None),
                Entity.deleted_at.is_(None),
                Disbursement.deleted_at.is_(None),
                Disbursement.status.in_(PENDING_DISBURSEMENT_STATUSES),
            )
            .order_by(
                Disbursement.status.asc(),
                Disbursement.scheduled_date.asc().nullslast(),
                Disbursement.request_date.asc(),
            )
            .limit(limit)
        )

        return [
            PendingDisbursementItem(
                disbursement_id=row[0],
                loan_account_id=row[1],
                loan_account_number=row[2],
                borrower_name=row[3],
                reference=row[4],
                requested_amount=self._money(row[5]),
                approved_amount=self._money(row[6]) if row[6] is not None else None,
                scheduled_date=row[7].isoformat() if row[7] else None,
                request_date=row[8].isoformat(),
                status=row[9].value if hasattr(row[9], "value") else str(row[9]),
                conditions_verified=bool(row[10]),
                utr_number=row[11],
            )
            for row in result.all()
        ]

    async def _pending_disbursement_totals(
        self,
        organization_id: UUID,
    ) -> dict[str, Decimal | int]:
        result = await self.db.execute(
            select(
                Disbursement.status,
                func.count(Disbursement.id),
                func.coalesce(
                    func.sum(
                        func.coalesce(
                            Disbursement.approved_amount,
                            Disbursement.requested_amount,
                        )
                    ),
                    0,
                ),
            )
            .join(LoanAccount, LoanAccount.id == Disbursement.loan_account_id)
            .where(
                LoanAccount.organization_id == organization_id,
                LoanAccount.deleted_at.is_(None),
                Disbursement.deleted_at.is_(None),
                Disbursement.status.in_(PENDING_DISBURSEMENT_STATUSES),
            )
            .group_by(Disbursement.status)
        )

        totals: dict[str, Decimal | int] = {
            "pending_count": 0,
            "pending_amount": Decimal("0"),
            "approved_count": 0,
            "approved_amount": Decimal("0"),
        }
        for status, count, amount in result.all():
            key_prefix = "approved" if status == DisbursementStatus.APPROVED else "pending"
            totals[f"{key_prefix}_count"] = int(count or 0)
            totals[f"{key_prefix}_amount"] = self._money(amount)
        return totals

    async def _processed_this_month_amount(
        self,
        organization_id: UUID,
        today: date,
    ) -> Decimal:
        month_start = today.replace(day=1)
        result = await self.db.execute(
            select(func.coalesce(func.sum(Disbursement.disbursed_amount), 0))
            .join(LoanAccount, LoanAccount.id == Disbursement.loan_account_id)
            .where(
                LoanAccount.organization_id == organization_id,
                LoanAccount.deleted_at.is_(None),
                Disbursement.deleted_at.is_(None),
                Disbursement.status == DisbursementStatus.PROCESSED,
                Disbursement.disbursement_date >= month_start,
                Disbursement.disbursement_date <= today,
            )
        )
        return self._money(result.scalar_one_or_none())

    def _readiness_status(
        self,
        row: SanctionReadinessRow,
        mandatory_pending: int,
        today: date,
    ) -> str:
        if row.validity_date and row.validity_date < today:
            return "expired"
        if mandatory_pending > 0:
            return "condition_blocked"
        return "ready"

    def _money(self, value: Decimal | int | float | None) -> Decimal:
        return Decimal(value or 0).quantize(MONEY, rounding=ROUND_HALF_UP)
