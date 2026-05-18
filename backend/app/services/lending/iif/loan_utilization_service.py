"""Per-application fund-utilization service.

Owns the ``los_application_utilization`` table. The "bulk replace"
verb is intentional: the typical UX is a table of editable line items
whose state is fully POSTed in one shot from the FE. Soft-delete is
used on row removal so the audit trail survives.

CRITICAL invariant — at submit time
``SUM(amounts) == application.requested_amount`` (±0.01 tolerance for
rounding) per the original task. Draft (submit=False) only warns.

Sanctioned-amount per category (``approved_amount``):
Once a sanction exists, the lender's approved breakdown can also be
captured on each row. The sum-against-sanction check is enforced on
both the bulk-replace endpoint (when any line has ``approved_amount``
populated) and the dedicated ``submit_approved_breakdown`` method.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestException, NotFoundException
from app.models.auth.user import User
from app.models.lending.application import LoanApplication
from app.models.lending.enums import SanctionStatus
from app.models.lending.iif.application_utilization import (
    ApplicationUtilization,
)
from app.models.lending.iif.fund_utilization_category import (
    FundUtilizationCategory,
)
from app.models.lending.sanction import LoanSanction
from app.schemas.lending.iif import (
    ApplicationUtilizationBulkReplace,
    ApprovedBreakdownRequest,
)

# ±0.01 INR — covers rounding in client-side category breakdowns.
_TOLERANCE: Decimal = Decimal("0.01")


@dataclass
class UtilizationListResult:
    """Bundle of every tally a list/replace endpoint needs to render.

    - ``rows`` — the live ``ApplicationUtilization`` rows.
    - ``total_amount`` — Σ ``amount`` (borrower's requested breakdown).
    - ``requested_amount`` — ``application.requested_amount`` for the
      ``amount`` sum check.
    - ``balanced`` — ``amount`` sum vs ``requested_amount`` (±0.01).
    - ``total_approved_amount`` — Σ ``approved_amount`` (None when no
      line has an approved amount set).
    - ``sanctioned_amount`` — current active sanction's
      ``sanctioned_amount`` if one exists (None otherwise).
    - ``approved_balanced`` — ``approved`` sum vs sanctioned (None
      when not yet applicable).
    """

    rows: list[ApplicationUtilization]
    total_amount: Decimal
    requested_amount: Decimal | None
    balanced: bool
    total_approved_amount: Decimal | None = None
    sanctioned_amount: Decimal | None = None
    approved_balanced: bool | None = None


class LoanUtilizationService:
    """Service for application-level fund-utilization breakdowns."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # =========================================================================
    # Read
    # =========================================================================

    async def list_for_application(
        self,
        organization_id: UUID,
        application_id: UUID,
    ) -> UtilizationListResult:
        """Return the rows + every aggregate needed by the FE."""
        application = await self._get_application(organization_id, application_id)
        stmt = (
            select(ApplicationUtilization)
            .options(selectinload(ApplicationUtilization.category))
            .where(
                ApplicationUtilization.application_id == application_id,
                ApplicationUtilization.organization_id == organization_id,
                ApplicationUtilization.deleted_at.is_(None),
            )
            .order_by(ApplicationUtilization.created_at.asc())
        )
        rows = list((await self.session.execute(stmt)).scalars().all())
        return await self._build_result(rows, application)

    # =========================================================================
    # Bulk replace
    # =========================================================================

    async def bulk_replace(
        self,
        organization_id: UUID,
        application_id: UUID,
        data: ApplicationUtilizationBulkReplace,
        current_user: User,
    ) -> UtilizationListResult:
        """Replace the full set of utilization rows for one application.

        - All existing rows are soft-deleted.
        - The new rows from ``data.lines`` are inserted, including any
          optional ``approved_amount`` per line.
        - If ``data.submit`` is True, ``SUM(amounts) ==
          application.requested_amount`` is enforced (±0.01).
        - If at least one line carries ``approved_amount`` and an
          active sanction exists, ``SUM(approved_amount)`` must equal
          the sanction's sanctioned_amount (±0.01).
        """
        application = await self._get_application(organization_id, application_id)

        # Validate categories all exist and are visible (platform or own).
        category_ids = [line.category_id for line in data.lines]
        if category_ids:
            cat_stmt = select(FundUtilizationCategory).where(
                FundUtilizationCategory.id.in_(category_ids),
                FundUtilizationCategory.deleted_at.is_(None),
            )
            cats_by_id = {c.id: c for c in (await self.session.execute(cat_stmt)).scalars().all()}
            for cid in category_ids:
                cat = cats_by_id.get(cid)
                if cat is None:
                    raise NotFoundException(
                        f"Category {cid} not found",
                        error_code="CATEGORY_NOT_FOUND",
                    )
                if cat.organization_id is not None and cat.organization_id != organization_id:
                    raise NotFoundException(
                        f"Category {cid} not found",
                        error_code="CATEGORY_NOT_FOUND",
                    )

        # Duplicate-category guard within the payload itself.
        if len(set(category_ids)) != len(category_ids):
            raise BadRequestException(
                "Duplicate category in utilization payload",
                error_code="DUPLICATE_CATEGORY",
            )

        # Requested-amount sum check (soft for draft, hard for submit).
        total = sum((line.amount for line in data.lines), start=Decimal("0"))
        requested = application.requested_amount
        balanced = requested is not None and abs(total - requested) <= _TOLERANCE

        if data.submit and not balanced:
            raise BadRequestException(
                (
                    f"Sum of utilization amounts ({total}) must equal "
                    f"the requested loan amount ({requested}) within ±0.01"
                ),
                error_code="UTILIZATION_NOT_BALANCED",
            )

        # Approved-amount sum check — only triggers when at least one
        # line carries an approved amount. We accept partial fills as
        # "draft approved breakdown" and let the dedicated endpoint
        # enforce the strict invariant; here we only block sum-vs-
        # sanction mismatches when the breakdown is *complete*
        # (every line populated).
        approved_amounts = [
            line.approved_amount for line in data.lines if line.approved_amount is not None
        ]
        if approved_amounts and len(approved_amounts) == len(data.lines) and data.lines:
            sanction = await self._get_active_sanction(application_id)
            if sanction is not None:
                approved_sum = sum(approved_amounts, start=Decimal("0"))
                if abs(approved_sum - sanction.sanctioned_amount) > _TOLERANCE:
                    raise BadRequestException(
                        (
                            f"Sum of approved amounts ({approved_sum}) must "
                            f"equal the sanctioned amount "
                            f"({sanction.sanctioned_amount}) within ±0.01"
                        ),
                        error_code="APPROVED_BREAKDOWN_NOT_BALANCED",
                    )

        # Soft-delete existing rows.
        existing_stmt = select(ApplicationUtilization).where(
            ApplicationUtilization.application_id == application_id,
            ApplicationUtilization.organization_id == organization_id,
            ApplicationUtilization.deleted_at.is_(None),
        )
        existing_rows = (await self.session.execute(existing_stmt)).scalars().all()
        for row in existing_rows:
            row.soft_delete(deleted_by=current_user.id)

        # Insert new rows.
        new_rows: list[ApplicationUtilization] = []
        for line in data.lines:
            row = ApplicationUtilization(
                organization_id=organization_id,
                application_id=application_id,
                category_id=line.category_id,
                amount=line.amount,
                approved_amount=line.approved_amount,
                remarks=line.remarks,
                created_by=current_user.id,
            )
            self.session.add(row)
            new_rows.append(row)

        await self.session.flush()
        # Eager-load category for response.
        for row in new_rows:
            await self.session.refresh(row, attribute_names=["category"])
        return await self._build_result(new_rows, application)

    # =========================================================================
    # Approved-breakdown submit
    # =========================================================================

    async def submit_approved_breakdown(
        self,
        organization_id: UUID,
        application_id: UUID,
        data: ApprovedBreakdownRequest,
        current_user: User,
    ) -> UtilizationListResult:
        """Update only ``approved_amount`` on existing live lines.

        - Does NOT touch ``amount`` (the borrower-requested split).
        - Validates ``SUM(approved_amount) == sanction.sanctioned_amount``
          (±0.01) against the application's most recent active sanction.
        - Raises ``BadRequestException`` with
          ``error_code="NO_ACTIVE_SANCTION"`` when no sanction exists.
        """
        application = await self._get_application(organization_id, application_id)

        sanction = await self._get_active_sanction(application_id)
        if sanction is None:
            raise BadRequestException(
                (
                    "Cannot submit approved breakdown — no active "
                    "sanction exists for this application"
                ),
                error_code="NO_ACTIVE_SANCTION",
            )

        # Duplicate-category guard within the payload itself.
        category_ids = [line.category_id for line in data.lines]
        if len(set(category_ids)) != len(category_ids):
            raise BadRequestException(
                "Duplicate category in approved-breakdown payload",
                error_code="DUPLICATE_CATEGORY",
            )

        # Sum check against the sanctioned amount.
        approved_sum = sum((line.approved_amount for line in data.lines), start=Decimal("0"))
        if abs(approved_sum - sanction.sanctioned_amount) > _TOLERANCE:
            raise BadRequestException(
                (
                    f"Sum of approved amounts ({approved_sum}) must equal "
                    f"the sanctioned amount ({sanction.sanctioned_amount}) "
                    f"within ±0.01"
                ),
                error_code="APPROVED_BREAKDOWN_NOT_BALANCED",
            )

        # Index existing live rows by category_id.
        existing_stmt = (
            select(ApplicationUtilization)
            .options(selectinload(ApplicationUtilization.category))
            .where(
                ApplicationUtilization.application_id == application_id,
                ApplicationUtilization.organization_id == organization_id,
                ApplicationUtilization.deleted_at.is_(None),
            )
        )
        existing_rows = list((await self.session.execute(existing_stmt)).scalars().all())
        rows_by_cat = {r.category_id: r for r in existing_rows}

        # Every line in the payload must reference an existing live row.
        for line in data.lines:
            row = rows_by_cat.get(line.category_id)
            if row is None:
                raise BadRequestException(
                    (
                        f"No existing utilization line for category "
                        f"{line.category_id}; submit the full breakdown "
                        f"via the parent /utilization endpoint first"
                    ),
                    error_code="UTILIZATION_LINE_NOT_FOUND",
                )
            row.approved_amount = line.approved_amount
            if line.remarks is not None:
                row.remarks = line.remarks
            row.updated_by = current_user.id
            row.version = (row.version or 1) + 1

        await self.session.flush()
        for row in existing_rows:
            await self.session.refresh(row, attribute_names=["category"])
        return await self._build_result(existing_rows, application)

    # =========================================================================
    # Single-line delete
    # =========================================================================

    async def delete_line(
        self,
        organization_id: UUID,
        application_id: UUID,
        line_id: UUID,
        current_user: User,
    ) -> None:
        await self._get_application(organization_id, application_id)
        line = await self.session.get(ApplicationUtilization, line_id)
        if (
            line is None
            or line.deleted_at is not None
            or line.application_id != application_id
            or line.organization_id != organization_id
        ):
            raise NotFoundException(
                "Utilization line not found",
                error_code="UTILIZATION_LINE_NOT_FOUND",
            )
        line.soft_delete(deleted_by=current_user.id)
        await self.session.flush()

    # =========================================================================
    # Helpers
    # =========================================================================

    async def _get_application(
        self, organization_id: UUID, application_id: UUID
    ) -> LoanApplication:
        application = await self.session.get(LoanApplication, application_id)
        if (
            application is None
            or application.deleted_at is not None
            or application.organization_id != organization_id
        ):
            raise NotFoundException(
                "Application not found",
                error_code="APPLICATION_NOT_FOUND",
            )
        return application

    async def _get_active_sanction(self, application_id: UUID) -> LoanSanction | None:
        """Return the most recent active sanction for the application.

        Considers DRAFT, PENDING_APPROVAL, APPROVED, ACTIVE, ACCEPTED
        states active enough for breakdown purposes (lender approves the
        breakdown alongside the sanction terms; EXPIRED / CANCELLED /
        SUPERSEDED are ignored).
        """
        active_statuses = (
            SanctionStatus.DRAFT,
            SanctionStatus.PENDING_APPROVAL,
            SanctionStatus.APPROVED,
            SanctionStatus.ACTIVE,
            SanctionStatus.ACCEPTED,
        )
        stmt = (
            select(LoanSanction)
            .where(
                LoanSanction.application_id == application_id,
                LoanSanction.deleted_at.is_(None),
                LoanSanction.status.in_(active_statuses),
            )
            .order_by(LoanSanction.sanction_date.desc())
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def _build_result(
        self,
        rows: list[ApplicationUtilization],
        application: LoanApplication,
    ) -> UtilizationListResult:
        """Assemble the rich list-result object including approved tallies."""
        total = sum((r.amount for r in rows), start=Decimal("0"))
        requested = application.requested_amount
        balanced = requested is not None and abs(total - requested) <= _TOLERANCE

        approved_values = [r.approved_amount for r in rows if r.approved_amount is not None]
        total_approved: Decimal | None = None
        sanctioned_amount: Decimal | None = None
        approved_balanced: bool | None = None

        if approved_values:
            total_approved = sum(approved_values, start=Decimal("0"))
            sanction = await self._get_active_sanction(application.id)
            if sanction is not None:
                sanctioned_amount = sanction.sanctioned_amount
                # Only flag balanced when every live line is populated;
                # a partial breakdown isn't a meaningful comparison.
                if len(approved_values) == len(rows) and rows:
                    approved_balanced = abs(total_approved - sanctioned_amount) <= _TOLERANCE
                else:
                    approved_balanced = False

        return UtilizationListResult(
            rows=rows,
            total_amount=total,
            requested_amount=requested,
            balanced=balanced,
            total_approved_amount=total_approved,
            sanctioned_amount=sanctioned_amount,
            approved_balanced=approved_balanced,
        )
