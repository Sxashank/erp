"""Manual-first loan closure and security release cockpit service."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lending.entity import Entity
from app.models.lending.enums import LoanAccountStatus, ReceiptStatus, ReceiptType, SecurityStatus
from app.models.lending.loan_account import LoanAccount, LoanReceipt
from app.models.lending.sanction import LoanSecurity
from app.schemas.lending.closure_cockpit import (
    ClosureCandidateItem,
    ClosureCockpitResponse,
    ClosureCockpitSummary,
    RecentClosureReceiptItem,
    SecurityReleaseItem,
)

MONEY = Decimal("0.01")
OPEN_LOAN_STATUSES = (
    LoanAccountStatus.ACTIVE,
    LoanAccountStatus.DORMANT,
    LoanAccountStatus.FROZEN,
    LoanAccountStatus.RECALLED,
)
CLOSURE_RECEIPT_TYPES = (
    ReceiptType.PREPAYMENT,
    ReceiptType.FORECLOSURE,
    ReceiptType.OTS_SETTLEMENT,
    ReceiptType.LEGAL_RECOVERY,
)
ACTIVE_RECEIPT_STATUSES = (ReceiptStatus.PENDING, ReceiptStatus.ALLOCATED)


class ClosureCockpitService:
    """Builds management controls for manual loan closure and release actions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_cockpit(
        self,
        organization_id: UUID,
        *,
        limit: int = 10,
        recent_days: int = 30,
    ) -> ClosureCockpitResponse:
        closure_candidates = await self._closure_candidates(organization_id, limit)
        pending_security_releases = await self._pending_security_releases(organization_id, limit)
        recent_closure_receipts = await self._recent_closure_receipts(
            organization_id,
            limit,
            recent_days,
        )
        blocked_count, blocked_amount = await self._blocked_by_outstanding(organization_id)

        return ClosureCockpitResponse(
            summary=ClosureCockpitSummary(
                closure_ready_count=sum(
                    1 for item in closure_candidates if item.closure_status == "READY_FOR_CLOSURE"
                ),
                closure_ready_outstanding=self._money(
                    sum(
                        (
                            item.total_outstanding
                            for item in closure_candidates
                            if item.closure_status == "READY_FOR_CLOSURE"
                        ),
                        Decimal("0"),
                    )
                ),
                closed_pending_release_count=sum(
                    1
                    for item in closure_candidates
                    if item.closure_status == "CLOSED_PENDING_RELEASE"
                ),
                unreleased_security_count=len(pending_security_releases),
                unreleased_security_value=self._money(
                    sum((item.net_value for item in pending_security_releases), Decimal("0"))
                ),
                recent_closure_receipt_count=len(recent_closure_receipts),
                recent_closure_receipt_amount=self._money(
                    sum((item.receipt_amount for item in recent_closure_receipts), Decimal("0"))
                ),
                blocked_by_outstanding_count=blocked_count,
                blocked_by_outstanding_amount=blocked_amount,
            ),
            closure_candidates=closure_candidates,
            pending_security_releases=pending_security_releases,
            recent_closure_receipts=recent_closure_receipts,
        )

    async def _closure_candidates(
        self,
        organization_id: UUID,
        limit: int,
    ) -> list[ClosureCandidateItem]:
        security_count = func.count(LoanSecurity.id).filter(
            LoanSecurity.status != SecurityStatus.RELEASED
        )
        security_value = func.coalesce(
            func.sum(LoanSecurity.net_value).filter(LoanSecurity.status != SecurityStatus.RELEASED),
            0,
        )
        original_docs_held = func.count(LoanSecurity.id).filter(
            LoanSecurity.status != SecurityStatus.RELEASED,
            LoanSecurity.original_documents_received.is_(True),
        )

        result = await self.db.execute(
            select(
                LoanAccount.id,
                LoanAccount.loan_account_number,
                Entity.legal_name,
                LoanAccount.status,
                LoanAccount.total_outstanding,
                LoanAccount.principal_outstanding,
                LoanAccount.interest_outstanding,
                LoanAccount.charges_outstanding,
                LoanAccount.maturity_date,
                LoanAccount.closure_date,
                security_count,
                security_value,
                original_docs_held,
            )
            .join(Entity, Entity.id == LoanAccount.entity_id)
            .outerjoin(LoanSecurity, LoanSecurity.sanction_id == LoanAccount.sanction_id)
            .where(
                LoanAccount.organization_id == organization_id,
                LoanAccount.deleted_at.is_(None),
                Entity.deleted_at.is_(None),
                LoanAccount.status.in_((*OPEN_LOAN_STATUSES, LoanAccountStatus.CLOSED)),
            )
            .group_by(LoanAccount.id, Entity.id)
            .having(
                (LoanAccount.total_outstanding <= 0)
                | ((LoanAccount.status == LoanAccountStatus.CLOSED) & (security_count > 0))
            )
            .order_by(
                LoanAccount.status.asc(),
                LoanAccount.closure_date.asc().nullslast(),
                LoanAccount.maturity_date.asc().nullslast(),
            )
            .limit(limit)
        )

        return [
            ClosureCandidateItem(
                loan_account_id=row[0],
                loan_account_number=row[1],
                borrower_name=row[2],
                status=self._enum_value(row[3]),
                total_outstanding=self._money(row[4]),
                principal_outstanding=self._money(row[5]),
                interest_outstanding=self._money(row[6]),
                charges_outstanding=self._money(row[7]),
                maturity_date=row[8].isoformat() if row[8] else None,
                closure_date=row[9].isoformat() if row[9] else None,
                closure_status=self._closure_status(row[3], int(row[10] or 0)),
                unreleased_security_count=int(row[10] or 0),
                unreleased_security_value=self._money(row[11]),
                original_documents_held=int(row[12] or 0),
            )
            for row in result.all()
        ]

    async def _pending_security_releases(
        self,
        organization_id: UUID,
        limit: int,
    ) -> list[SecurityReleaseItem]:
        result = await self.db.execute(
            select(
                LoanSecurity.id,
                LoanAccount.id,
                LoanAccount.loan_account_number,
                Entity.legal_name,
                LoanSecurity.security_type,
                LoanSecurity.security_category,
                LoanSecurity.description,
                LoanSecurity.acceptable_value,
                LoanSecurity.net_value,
                LoanSecurity.status,
                LoanSecurity.original_documents_received,
                LoanSecurity.document_location,
                LoanSecurity.release_date,
            )
            .join(LoanAccount, LoanAccount.sanction_id == LoanSecurity.sanction_id)
            .join(Entity, Entity.id == LoanAccount.entity_id)
            .where(
                LoanAccount.organization_id == organization_id,
                LoanAccount.deleted_at.is_(None),
                Entity.deleted_at.is_(None),
                LoanSecurity.deleted_at.is_(None),
                LoanSecurity.status != SecurityStatus.RELEASED,
                (
                    (LoanAccount.status == LoanAccountStatus.CLOSED)
                    | (LoanAccount.total_outstanding <= 0)
                ),
            )
            .order_by(
                LoanAccount.closure_date.asc().nullslast(),
                LoanSecurity.security_category.asc(),
                LoanSecurity.security_number.asc(),
            )
            .limit(limit)
        )

        return [
            SecurityReleaseItem(
                security_id=row[0],
                loan_account_id=row[1],
                loan_account_number=row[2],
                borrower_name=row[3],
                security_type=self._enum_value(row[4]),
                security_category=self._enum_value(row[5]),
                description=row[6],
                acceptable_value=self._money(row[7]),
                net_value=self._money(row[8]),
                status=self._enum_value(row[9]),
                original_documents_received=bool(row[10]),
                document_location=row[11],
                release_date=row[12].isoformat() if row[12] else None,
            )
            for row in result.all()
        ]

    async def _recent_closure_receipts(
        self,
        organization_id: UUID,
        limit: int,
        recent_days: int,
    ) -> list[RecentClosureReceiptItem]:
        period_start = date.today() - timedelta(days=recent_days)
        result = await self.db.execute(
            select(
                LoanReceipt.id,
                LoanAccount.id,
                LoanAccount.loan_account_number,
                Entity.legal_name,
                LoanReceipt.receipt_number,
                LoanReceipt.receipt_date,
                LoanReceipt.receipt_type,
                LoanReceipt.receipt_amount,
                LoanReceipt.allocated_amount,
                LoanReceipt.unallocated_amount,
                LoanReceipt.status,
                LoanReceipt.instrument_number,
            )
            .join(LoanAccount, LoanAccount.id == LoanReceipt.loan_account_id)
            .join(Entity, Entity.id == LoanAccount.entity_id)
            .where(
                LoanAccount.organization_id == organization_id,
                LoanAccount.deleted_at.is_(None),
                Entity.deleted_at.is_(None),
                LoanReceipt.deleted_at.is_(None),
                LoanReceipt.bounced.is_(False),
                LoanReceipt.status.in_(ACTIVE_RECEIPT_STATUSES),
                LoanReceipt.receipt_type.in_(CLOSURE_RECEIPT_TYPES),
                LoanReceipt.receipt_date >= period_start,
            )
            .order_by(LoanReceipt.receipt_date.desc(), LoanReceipt.created_at.desc())
            .limit(limit)
        )

        return [
            RecentClosureReceiptItem(
                receipt_id=row[0],
                loan_account_id=row[1],
                loan_account_number=row[2],
                borrower_name=row[3],
                receipt_number=row[4],
                receipt_date=row[5].isoformat(),
                receipt_type=self._enum_value(row[6]),
                receipt_amount=self._money(row[7]),
                allocated_amount=self._money(row[8]),
                unallocated_amount=self._money(row[9]),
                status=self._enum_value(row[10]),
                instrument_number=row[11],
            )
            for row in result.all()
        ]

    async def _blocked_by_outstanding(self, organization_id: UUID) -> tuple[int, Decimal]:
        result = await self.db.execute(
            select(
                func.count(LoanAccount.id),
                func.coalesce(func.sum(LoanAccount.total_outstanding), 0),
            ).where(
                LoanAccount.organization_id == organization_id,
                LoanAccount.deleted_at.is_(None),
                LoanAccount.status.in_(OPEN_LOAN_STATUSES),
                LoanAccount.total_outstanding > 0,
                LoanAccount.maturity_date <= date.today(),
            )
        )
        count, amount = result.one()
        return int(count or 0), self._money(amount)

    def _closure_status(self, loan_status: LoanAccountStatus, unreleased_securities: int) -> str:
        if loan_status == LoanAccountStatus.CLOSED and unreleased_securities > 0:
            return "CLOSED_PENDING_RELEASE"
        if loan_status == LoanAccountStatus.CLOSED:
            return "CLOSED"
        return "READY_FOR_CLOSURE"

    def _enum_value(self, value: object) -> str:
        return value.value if hasattr(value, "value") else str(value)

    def _money(self, value: Decimal | int | float | None) -> Decimal:
        return Decimal(value or 0).quantize(MONEY, rounding=ROUND_HALF_UP)
