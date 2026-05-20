"""Borrower-portal: IIF subsidy claims.

Read-only mirror of the admin claims surface, scoped to loan accounts
whose entity belongs to the borrower's accessible set. CSV streaming
reuses :func:`app.api.v1.lending.iif.claims._report_to_csv`.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db
from app.api.v1.lending.iif.claims import _report_to_csv
from app.api.v1.portal.auth import get_portal_db_with_tenant, get_portal_user
from app.core.exceptions import NotFoundException
from app.models.lending.iif.loan_subvention_enrollment import (
    LoanSubventionEnrollment,
)
from app.models.lending.iif.subvention_claim import SubventionClaim
from app.schemas.base import CamelSchema
from app.services.lending.iif.subvention_claim_service import (
    SubventionClaimService,
)
from app.services.portal.entity_access import assert_loan_access

router = APIRouter(prefix="/loans", tags=["Borrower Portal · Subsidy"])


# ---------------------------------------------------------------------------
# Wire shape
# ---------------------------------------------------------------------------


class BorrowerClaimItem(CamelSchema):
    """Borrower-visible subset of a SubventionClaim."""

    id: UUID
    claim_reference: str
    period_start: datetime
    period_end: datetime
    status: str
    applicable_subvention_amount: Decimal
    interest_paid_in_period: Decimal
    paid_date: datetime | None = None
    utr_reference: str | None = None


class BorrowerClaimsResponse(CamelSchema):
    items: list[BorrowerClaimItem] = Field(default_factory=list)
    total: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/{loan_account_id}/iif/claims",
    response_model=BorrowerClaimsResponse,
    response_model_by_alias=True,
    summary="List IIF subsidy claims for one of the borrower's loans",
)
async def list_claims(
    loan_account_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200, alias="pageSize"),
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
) -> BorrowerClaimsResponse:
    loan = await assert_loan_access(user, loan_account_id, db)

    # Pull all claims whose enrolment is on this loan, scoped to its org.
    stmt = (
        select(SubventionClaim)
        .options(
            selectinload(SubventionClaim.enrollment).selectinload(
                LoanSubventionEnrollment.loan_account
            )
        )
        .where(
            SubventionClaim.organization_id == loan.organization_id,
            SubventionClaim.deleted_at.is_(None),
            SubventionClaim.enrollment_id.in_(
                select(LoanSubventionEnrollment.id).where(
                    LoanSubventionEnrollment.loan_account_id == loan_account_id,
                    LoanSubventionEnrollment.deleted_at.is_(None),
                )
            ),
        )
        .order_by(SubventionClaim.period_end.desc())
    )
    all_rows = list((await db.execute(stmt)).scalars().all())
    total = len(all_rows)

    start = (page - 1) * page_size
    page_rows = all_rows[start : start + page_size]

    return BorrowerClaimsResponse(
        items=[
            BorrowerClaimItem(
                id=row.id,
                claim_reference=row.claim_reference,
                period_start=datetime.combine(row.period_start, datetime.min.time()),
                period_end=datetime.combine(row.period_end, datetime.min.time()),
                status=row.status,
                applicable_subvention_amount=row.applicable_subvention_amount,
                interest_paid_in_period=row.interest_paid_in_period,
                paid_date=(
                    datetime.combine(row.paid_date, datetime.min.time()) if row.paid_date else None
                ),
                utr_reference=row.utr_reference,
            )
            for row in page_rows
        ],
        total=total,
    )


@router.get(
    "/{loan_account_id}/iif/claims/{claim_id}/report.csv",
    summary="Download the IIF claim report as CSV",
)
async def claim_report_csv(
    loan_account_id: UUID,
    claim_id: UUID,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
) -> StreamingResponse:
    """Pre-filter by entity-access, then stream the CSV the admin uses."""
    loan = await assert_loan_access(user, loan_account_id, db)

    # Verify the claim belongs to this loan (no cross-loan leakage).
    stmt = select(SubventionClaim).where(
        SubventionClaim.id == claim_id,
        SubventionClaim.organization_id == loan.organization_id,
        SubventionClaim.deleted_at.is_(None),
        SubventionClaim.enrollment_id.in_(
            select(LoanSubventionEnrollment.id).where(
                LoanSubventionEnrollment.loan_account_id == loan_account_id,
            )
        ),
    )
    claim = (await db.execute(stmt)).scalar_one_or_none()
    if claim is None:
        raise NotFoundException(
            "Claim not found",
            error_code="CLAIM_NOT_FOUND",
        )

    service = SubventionClaimService(db)
    payload = await service.generate_claim_report(loan.organization_id, claim_id)
    csv_text = _report_to_csv(payload)
    filename = f"IIF-{claim.claim_reference.replace('/', '_')}.csv"
    return StreamingResponse(
        iter([csv_text]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
