"""Scheme-portal reporting endpoints."""

from __future__ import annotations

import csv
from io import StringIO

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_db_with_tenant
from app.api.v1.portal.auth import get_portal_user
from app.schemas.portal.reporting import PortalReportingResponse
from app.services.portal.reporting_service import PortalReportingService

router = APIRouter(prefix="/reports", tags=["Scheme Portal · Reports"])


@router.get(
    "/summary",
    response_model=PortalReportingResponse,
    response_model_by_alias=True,
    summary="Get scheme-portal reporting summary",
)
async def get_reporting_summary(
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db_with_tenant),
) -> PortalReportingResponse:
    service = PortalReportingService(db)
    return await service.get_summary(user)


@router.get(
    "/summary.csv",
    summary="Download scheme-portal reporting summary as CSV",
)
async def download_reporting_summary_csv(
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db_with_tenant),
) -> StreamingResponse:
    service = PortalReportingService(db)
    summary = await service.get_summary(user)
    csv_text = _summary_to_csv(summary)
    filename = f"scheme-portal-report-{summary.generated_at.date().isoformat()}.csv"
    return StreamingResponse(
        iter([csv_text]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _summary_to_csv(summary: PortalReportingResponse) -> str:
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Section", "Metric", "Value"])
    writer.writerow(["Metadata", "Actor role", summary.actor_role])
    writer.writerow(["Metadata", "Generated at", summary.generated_at.isoformat()])
    writer.writerow(["Applications", "Total", summary.application_summary.total])
    writer.writerow(["Applications", "Submitted", summary.application_summary.submitted])
    writer.writerow(["Applications", "Under review", summary.application_summary.under_review])
    writer.writerow(["Applications", "Query pending", summary.application_summary.query_pending])
    writer.writerow(["Applications", "Approved", summary.application_summary.approved])
    writer.writerow(["Applications", "Released", summary.application_summary.released])
    writer.writerow(
        ["Applications", "Requested amount", summary.application_summary.requested_amount]
    )
    writer.writerow(["Claims", "Total", summary.claim_summary.total])
    writer.writerow(["Claims", "Draft", summary.claim_summary.draft])
    writer.writerow(["Claims", "Submitted", summary.claim_summary.submitted])
    writer.writerow(["Claims", "Verified", summary.claim_summary.verified])
    writer.writerow(["Claims", "Release in progress", summary.claim_summary.release_in_progress])
    writer.writerow(["Claims", "Released", summary.claim_summary.released])
    writer.writerow(["Claims", "Rejected", summary.claim_summary.rejected])
    writer.writerow(["Claims", "Released amount", summary.claim_summary.released_amount])

    writer.writerow([])
    writer.writerow(["Application status", "Count"])
    for item in summary.application_status_breakdown:
        writer.writerow([item.status, item.count])

    writer.writerow([])
    writer.writerow(["Claim status", "Count"])
    for item in summary.claim_status_breakdown:
        writer.writerow([item.status, item.count])

    writer.writerow([])
    writer.writerow(
        [
            "Borrower",
            "Applications",
            "Approved",
            "Requested amount",
            "Released claims",
            "Released amount",
        ]
    )
    for item in summary.borrower_breakdown:
        writer.writerow(
            [
                item.entity_legal_name,
                item.application_count,
                item.approved_count,
                item.requested_amount,
                item.claims_released_count,
                item.claims_released_amount,
            ]
        )

    writer.writerow([])
    writer.writerow(
        ["Lender", "Applications", "Pending lender review", "Approved", "Requested amount"]
    )
    for item in summary.lender_breakdown:
        writer.writerow(
            [
                item.lender_name,
                item.application_count,
                item.pending_lender_review,
                item.approved_count,
                item.requested_amount,
            ]
        )
    return buffer.getvalue()
