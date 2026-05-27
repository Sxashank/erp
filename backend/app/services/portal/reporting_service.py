"""Actor-scoped reporting for the integrated SFC portal."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.lending.application import LoanApplication
from app.models.lending.iif.loan_subvention_enrollment import (
    LoanSubventionEnrollment,
)
from app.models.lending.iif.subvention_claim import SubventionClaim
from app.models.lending.loan_account import LoanAccount
from app.models.portal.portal_user import PortalUser
from app.schemas.portal.reporting import (
    PortalReportApplicationSummary,
    PortalReportBorrowerBreakdownItem,
    PortalReportClaimSummary,
    PortalReportingResponse,
    PortalReportRecentReleaseItem,
    PortalReportReviewBreakdownItem,
    PortalReportStatusBreakdownItem,
)
from app.services.portal.actor_roles import is_borrower_role, portal_actor_role
from app.services.portal.entity_access import get_accessible_entity_ids
from app.services.portal.scheme_rules import derive_scheme_application_status

APPLICATION_BREAKDOWN_ORDER = [
    "DRAFT",
    "LENDER_REVIEW",
    "LENDER_VALIDATED",
    "SMFCL_PRELIM_REVIEW",
    "QUERY_PENDING",
    "SMFCL_APPRAISAL",
    "APPROVED",
    "SANCTION_ISSUED",
    "CLAIM_OPEN",
    "RELEASE_IN_PROGRESS",
    "RELEASED",
    "CLOSED",
    "REJECTED",
]

CLAIM_BREAKDOWN_ORDER = [
    "DRAFT",
    "SUBMITTED",
    "VERIFIED",
    "RELEASE_IN_PROGRESS",
    "RELEASED",
    "REJECTED",
    "CANCELLED",
]

APPROVED_APPLICATION_STATUSES = {
    "APPROVED",
    "SANCTION_ISSUED",
    "CLAIM_OPEN",
    "RELEASE_IN_PROGRESS",
    "RELEASED",
    "CLOSED",
}

UNDER_REVIEW_APPLICATION_STATUSES = {
    "LENDER_REVIEW",
    "LENDER_VALIDATED",
    "SMFCL_PRELIM_REVIEW",
    "SMFCL_APPRAISAL",
}


class PortalReportingService:
    """Build reporting summaries for borrower, SFC, and ministry roles."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_summary(
        self,
        portal_user: PortalUser,
    ) -> PortalReportingResponse:
        accessible_entity_ids: set[UUID] | None = None
        if is_borrower_role(portal_user):
            accessible = await get_accessible_entity_ids(portal_user, self.db)
            accessible_entity_ids = set(accessible)

        applications = await self._load_applications(
            portal_user.organization_id,
            accessible_entity_ids,
        )
        claims = await self._load_claims(
            portal_user.organization_id,
            accessible_entity_ids,
        )

        application_statuses = [
            derive_scheme_application_status(
                app.status,
                app.stage,
                app.extra_data or {},
            )
            for app in applications
        ]
        claim_statuses = [claim.status or "DRAFT" for claim in claims]

        return PortalReportingResponse(
            actor_role=portal_actor_role(portal_user),
            generated_at=datetime.now(UTC),
            application_summary=self._application_summary(
                applications,
                application_statuses,
            ),
            claim_summary=self._claim_summary(claims, claim_statuses),
            application_status_breakdown=self._status_breakdown(
                application_statuses,
                APPLICATION_BREAKDOWN_ORDER,
            ),
            claim_status_breakdown=self._status_breakdown(
                claim_statuses,
                CLAIM_BREAKDOWN_ORDER,
            ),
            borrower_breakdown=self._borrower_breakdown(
                applications,
                application_statuses,
                claims,
            ),
            review_breakdown=self._review_breakdown(
                applications,
                application_statuses,
            ),
            recent_releases=self._recent_releases(claims),
        )

    async def _load_applications(
        self,
        organization_id: UUID | None,
        accessible_entity_ids: set[UUID] | None,
    ) -> list[LoanApplication]:
        if organization_id is None:
            return []
        stmt = (
            select(LoanApplication)
            .options(selectinload(LoanApplication.entity))
            .where(
                LoanApplication.organization_id == organization_id,
                LoanApplication.deleted_at.is_(None),
            )
            .order_by(LoanApplication.updated_at.desc().nullslast())
        )
        if accessible_entity_ids is not None:
            if not accessible_entity_ids:
                return []
            stmt = stmt.where(LoanApplication.entity_id.in_(accessible_entity_ids))
        return list((await self.db.execute(stmt)).scalars().all())

    async def _load_claims(
        self,
        organization_id: UUID | None,
        accessible_entity_ids: set[UUID] | None,
    ) -> list[SubventionClaim]:
        if organization_id is None:
            return []
        stmt = (
            select(SubventionClaim)
            .join(
                LoanSubventionEnrollment,
                SubventionClaim.enrollment_id == LoanSubventionEnrollment.id,
            )
            .join(
                LoanAccount,
                LoanSubventionEnrollment.loan_account_id == LoanAccount.id,
            )
            .options(
                selectinload(SubventionClaim.enrollment)
                .selectinload(LoanSubventionEnrollment.loan_account)
                .selectinload(LoanAccount.entity),
                selectinload(SubventionClaim.enrollment).selectinload(
                    LoanSubventionEnrollment.scheme
                ),
            )
            .where(
                SubventionClaim.organization_id == organization_id,
                SubventionClaim.deleted_at.is_(None),
            )
            .order_by(SubventionClaim.paid_date.desc().nullslast())
        )
        if accessible_entity_ids is not None:
            if not accessible_entity_ids:
                return []
            stmt = stmt.where(LoanAccount.entity_id.in_(accessible_entity_ids))
        return list((await self.db.execute(stmt)).scalars().all())

    def _application_summary(
        self,
        applications: list[LoanApplication],
        statuses: Iterable[str],
    ) -> PortalReportApplicationSummary:
        status_list = list(statuses)
        return PortalReportApplicationSummary(
            total=len(applications),
            submitted=sum(status != "DRAFT" for status in status_list),
            under_review=sum(status in UNDER_REVIEW_APPLICATION_STATUSES for status in status_list),
            query_pending=sum(status == "QUERY_PENDING" for status in status_list),
            approved=sum(status in APPROVED_APPLICATION_STATUSES for status in status_list),
            released=sum(status in {"RELEASED", "CLOSED"} for status in status_list),
            requested_amount=sum((app.requested_amount or Decimal("0")) for app in applications),
        )

    def _claim_summary(
        self,
        claims: list[SubventionClaim],
        statuses: Iterable[str],
    ) -> PortalReportClaimSummary:
        status_list = list(statuses)
        return PortalReportClaimSummary(
            total=len(claims),
            draft=sum(status == "DRAFT" for status in status_list),
            submitted=sum(status == "SUBMITTED" for status in status_list),
            verified=sum(status == "VERIFIED" for status in status_list),
            release_in_progress=sum(status == "RELEASE_IN_PROGRESS" for status in status_list),
            released=sum(status == "RELEASED" for status in status_list),
            rejected=sum(status == "REJECTED" for status in status_list),
            released_amount=sum(
                (
                    claim.applicable_subvention_amount or Decimal("0")
                    for claim in claims
                    if claim.status == "RELEASED"
                ),
                start=Decimal("0"),
            ),
        )

    def _status_breakdown(
        self,
        statuses: Iterable[str],
        order: list[str],
    ) -> list[PortalReportStatusBreakdownItem]:
        counts = Counter(statuses)
        items = [
            PortalReportStatusBreakdownItem(status=status, count=counts[status])
            for status in order
            if counts[status] > 0
        ]
        for status, count in counts.items():
            if status not in order:
                items.append(PortalReportStatusBreakdownItem(status=status, count=count))
        return items

    def _borrower_breakdown(
        self,
        applications: list[LoanApplication],
        application_statuses: list[str],
        claims: list[SubventionClaim],
    ) -> list[PortalReportBorrowerBreakdownItem]:
        summary: dict[UUID, dict[str, object]] = {}
        for app, status in zip(applications, application_statuses):
            entity = app.entity
            if entity is None:
                continue
            bucket = summary.setdefault(
                entity.id,
                {
                    "entity_id": entity.id,
                    "entity_legal_name": entity.legal_name,
                    "application_count": 0,
                    "approved_count": 0,
                    "requested_amount": Decimal("0"),
                    "claims_released_count": 0,
                    "claims_released_amount": Decimal("0"),
                },
            )
            bucket["application_count"] = int(bucket["application_count"]) + 1
            bucket["requested_amount"] = Decimal(bucket["requested_amount"]) + (
                app.requested_amount or Decimal("0")
            )
            if status in APPROVED_APPLICATION_STATUSES:
                bucket["approved_count"] = int(bucket["approved_count"]) + 1

        for claim in claims:
            enrollment = claim.enrollment
            loan_account = enrollment.loan_account if enrollment else None
            entity = loan_account.entity if loan_account else None
            if entity is None or claim.status != "RELEASED":
                continue
            bucket = summary.setdefault(
                entity.id,
                {
                    "entity_id": entity.id,
                    "entity_legal_name": entity.legal_name,
                    "application_count": 0,
                    "approved_count": 0,
                    "requested_amount": Decimal("0"),
                    "claims_released_count": 0,
                    "claims_released_amount": Decimal("0"),
                },
            )
            bucket["claims_released_count"] = int(bucket["claims_released_count"]) + 1
            bucket["claims_released_amount"] = Decimal(bucket["claims_released_amount"]) + (
                claim.applicable_subvention_amount or Decimal("0")
            )

        ordered = sorted(
            summary.values(),
            key=lambda row: (
                Decimal(row["requested_amount"]),
                int(row["claims_released_count"]),
            ),
            reverse=True,
        )
        return [PortalReportBorrowerBreakdownItem(**row) for row in ordered[:10]]

    def _review_breakdown(
        self,
        applications: list[LoanApplication],
        application_statuses: list[str],
    ) -> list[PortalReportReviewBreakdownItem]:
        summary: dict[str, dict[str, object]] = {}
        for app, status in zip(applications, application_statuses):
            review_owner = "SFC"
            bucket = summary.setdefault(
                review_owner,
                {
                    "review_owner": review_owner,
                    "application_count": 0,
                    "pending_sfc_review": 0,
                    "approved_count": 0,
                    "requested_amount": Decimal("0"),
                },
            )
            bucket["application_count"] = int(bucket["application_count"]) + 1
            bucket["requested_amount"] = Decimal(bucket["requested_amount"]) + (
                app.requested_amount or Decimal("0")
            )
            if status == "LENDER_REVIEW":
                bucket["pending_sfc_review"] = int(bucket["pending_sfc_review"]) + 1
            if status in APPROVED_APPLICATION_STATUSES:
                bucket["approved_count"] = int(bucket["approved_count"]) + 1

        ordered = sorted(
            summary.values(),
            key=lambda row: (
                Decimal(row["requested_amount"]),
                int(row["application_count"]),
            ),
            reverse=True,
        )
        return [PortalReportReviewBreakdownItem(**row) for row in ordered[:10]]

    def _recent_releases(
        self,
        claims: list[SubventionClaim],
    ) -> list[PortalReportRecentReleaseItem]:
        released = [claim for claim in claims if claim.status == "RELEASED"]
        released.sort(
            key=lambda claim: (
                claim.paid_date or datetime.min.date(),
                claim.updated_at or claim.created_at,
            ),
            reverse=True,
        )
        return [
            PortalReportRecentReleaseItem(
                claim_id=claim.id,
                claim_reference=claim.claim_reference,
                entity_legal_name=(
                    claim.enrollment.loan_account.entity.legal_name
                    if claim.enrollment
                    and claim.enrollment.loan_account
                    and claim.enrollment.loan_account.entity
                    else None
                ),
                scheme_name=(
                    claim.enrollment.scheme.scheme_name
                    if claim.enrollment and claim.enrollment.scheme
                    else None
                ),
                applicable_subvention_amount=claim.applicable_subvention_amount,
                released_date=claim.paid_date,
                release_reference=claim.utr_reference,
            )
            for claim in released[:10]
        ]
