"""Subvention claim endpoints.

The largest of the IIF routers — covers lifecycle (create / submit /
verify / initiate-release / mark-released / cancel), compute previews, eligible-period
discovery, and the claim report (structured JSON + CSV streams).

Binary PDF / XLSX output is generated from the same structured
``ClaimReportResponse`` payload as CSV using dependency-free exporters.
"""

from __future__ import annotations

import csv
import io
import os
from datetime import date
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_current_user, get_db_with_tenant
from app.core.exceptions import BadRequestException
from app.models.auth.user import User
from app.schemas.base import CamelSchema
from app.schemas.document_studio import GeneratedDocumentResponse
from app.schemas.lending.iif import (
    ClaimReportResponse,
    EligibleClaimPeriodResponse,
    SubventionClaimCancelRequest,
    SubventionClaimComputeRequest,
    SubventionClaimComputeResponse,
    SubventionClaimCreate,
    SubventionClaimInitiateReleaseRequest,
    SubventionClaimListResponse,
    SubventionClaimMarkReleasedRequest,
    SubventionClaimResponse,
    SubventionClaimSubmitRequest,
    SubventionClaimUpdate,
    SubventionClaimVerifyRequest,
)
from app.services.dms.document_service import DocumentService
from app.services.lending.iif import SubventionClaimService
from app.utils.simple_exports import build_text_pdf, build_xlsx

router = APIRouter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _require_idempotency_key(key: str | None) -> None:
    if not key:
        raise BadRequestException(
            "Idempotency-Key header is required for this operation",
            error_code="IDEMPOTENCY_KEY_REQUIRED",
        )


def _require_org(user: User) -> UUID:
    if user.organization_id is None:
        raise BadRequestException(
            "Current user has no organization context",
            error_code="MISSING_ORG_CONTEXT",
        )
    return user.organization_id


# ---------------------------------------------------------------------------
# "Eligible loans" — enrolments with a claim-able next period
# ---------------------------------------------------------------------------


class EligibleLoanRow(CamelSchema):
    """One row of the ``GET /eligible-loans`` response."""

    enrollment_id: UUID
    loan_account_id: UUID
    loan_account_number: str | None = None
    scheme_id: UUID
    scheme_code: str
    claim_frequency: str
    period_start: date
    period_end: date
    label: str


class EligibleLoansResponse(CamelSchema):
    """Wrapper for the eligible-loans list."""

    items: list[EligibleLoanRow]
    total: int


@router.get(
    "/eligible-loans",
    response_model=EligibleLoansResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def list_eligible_loans(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200, alias="pageSize"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> EligibleLoansResponse:
    org_id = _require_org(current_user)
    skip = (page - 1) * page_size
    service = SubventionClaimService(db)
    items, total = await service.list_loans_due_for_claim(org_id, skip=skip, limit=page_size)
    return EligibleLoansResponse(
        items=[EligibleLoanRow.model_validate(r) for r in items],
        total=total,
    )


# ---------------------------------------------------------------------------
# Compute (preview only — does NOT persist)
# ---------------------------------------------------------------------------


@router.post(
    "/compute",
    response_model=SubventionClaimComputeResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def compute_claim(
    data: SubventionClaimComputeRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> SubventionClaimComputeResponse:
    """Preview the claim amount for a (enrollment, period) pair.

    Read-only — no Idempotency-Key required.
    """
    org_id = _require_org(current_user)
    service = SubventionClaimService(db)
    interest_paid, rate, applicable, method, eligible_base = await service.compute_claim(
        org_id, data.enrollment_id, data.period_start, data.period_end
    )
    return SubventionClaimComputeResponse(
        enrollment_id=data.enrollment_id,
        period_start=data.period_start,
        period_end=data.period_end,
        interest_paid_in_period=interest_paid,
        subvention_rate_percent=rate,
        applicable_subvention_amount=applicable,
        calculation_method=method,
        eligible_base_amount=eligible_base,
    )


# ---------------------------------------------------------------------------
# List / read
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=SubventionClaimListResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def list_claims(
    status_filter: str | None = Query(None, alias="status"),
    enrollment_id: UUID | None = Query(None, alias="enrollmentId"),
    loan_account_id: UUID | None = Query(None, alias="loanAccountId"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200, alias="pageSize"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> SubventionClaimListResponse:
    org_id = _require_org(current_user)
    skip = (page - 1) * page_size
    service = SubventionClaimService(db)
    items, total = await service.list_claims(
        organization_id=org_id,
        status=status_filter,
        enrollment_id=enrollment_id,
        loan_account_id=loan_account_id,
        skip=skip,
        limit=page_size,
    )
    return SubventionClaimListResponse.create(
        [SubventionClaimResponse.model_validate(c) for c in items],
        total,
        page,
        page_size,
    )


@router.get(
    "/{claim_id}",
    response_model=SubventionClaimResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def get_claim(
    claim_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> SubventionClaimResponse:
    org_id = _require_org(current_user)
    service = SubventionClaimService(db)
    claim = await service.get(org_id, claim_id)
    return SubventionClaimResponse.model_validate(claim)


@router.get(
    "/by-enrollment/{enrollment_id}/eligible-periods",
    response_model=EligibleClaimPeriodResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def list_eligible_periods(
    enrollment_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> EligibleClaimPeriodResponse:
    """List the periods that can still be claimed for an enrollment."""
    org_id = _require_org(current_user)
    service = SubventionClaimService(db)
    return await service.eligible_periods(org_id, enrollment_id)


# ---------------------------------------------------------------------------
# Lifecycle (mutations — Idempotency-Key required)
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=SubventionClaimResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def create_claim(
    data: SubventionClaimCreate,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> SubventionClaimResponse:
    _require_idempotency_key(idempotency_key)
    org_id = _require_org(current_user)
    service = SubventionClaimService(db)
    claim = await service.create_claim(
        org_id,
        data.enrollment_id,
        data.period_start,
        data.period_end,
        data.documents,
        current_user,
    )
    await db.commit()
    return SubventionClaimResponse.model_validate(claim)


@router.put(
    "/{claim_id}",
    response_model=SubventionClaimResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def update_claim(
    claim_id: UUID,
    data: SubventionClaimUpdate,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> SubventionClaimResponse:
    _require_idempotency_key(idempotency_key)
    org_id = _require_org(current_user)
    service = SubventionClaimService(db)
    if data.documents is not None:
        claim = await service.update_documents(org_id, claim_id, data.documents, current_user)
        await db.commit()
    else:
        claim = await service.get(org_id, claim_id)
    return SubventionClaimResponse.model_validate(claim)


@router.post(
    "/{claim_id}/submit",
    response_model=SubventionClaimResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def submit_claim(
    claim_id: UUID,
    data: SubventionClaimSubmitRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> SubventionClaimResponse:
    _require_idempotency_key(idempotency_key)
    org_id = _require_org(current_user)
    service = SubventionClaimService(db)
    claim = await service.submit_claim(org_id, claim_id, data.declaration_signed_at, current_user)
    await db.commit()
    return SubventionClaimResponse.model_validate(claim)


@router.post(
    "/{claim_id}/verify",
    response_model=SubventionClaimResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def verify_claim(
    claim_id: UUID,
    data: SubventionClaimVerifyRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> SubventionClaimResponse:
    _require_idempotency_key(idempotency_key)
    org_id = _require_org(current_user)
    service = SubventionClaimService(db)
    claim = await service.verify_claim(org_id, claim_id, data.decision, data.reason, current_user)
    await db.commit()
    return SubventionClaimResponse.model_validate(claim)


@router.post(
    "/{claim_id}/initiate-release",
    response_model=SubventionClaimResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def initiate_claim_release(
    claim_id: UUID,
    data: SubventionClaimInitiateReleaseRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> SubventionClaimResponse:
    _require_idempotency_key(idempotency_key)
    org_id = _require_org(current_user)
    service = SubventionClaimService(db)
    claim = await service.initiate_release(
        org_id,
        claim_id,
        data.release_instruction_reference,
        data.release_initiated_date,
        data.release_instruction_notes,
        current_user,
    )
    await db.commit()
    return SubventionClaimResponse.model_validate(claim)


@router.post(
    "/{claim_id}/mark-released",
    response_model=SubventionClaimResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def mark_claim_released(
    claim_id: UUID,
    data: SubventionClaimMarkReleasedRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> SubventionClaimResponse:
    _require_idempotency_key(idempotency_key)
    org_id = _require_org(current_user)
    service = SubventionClaimService(db)
    claim = await service.mark_released(
        org_id,
        claim_id,
        data.release_reference,
        data.released_date,
        current_user,
    )
    await db.commit()
    return SubventionClaimResponse.model_validate(claim)


@router.post(
    "/{claim_id}/cancel",
    response_model=SubventionClaimResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def cancel_claim(
    claim_id: UUID,
    data: SubventionClaimCancelRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> SubventionClaimResponse:
    _require_idempotency_key(idempotency_key)
    org_id = _require_org(current_user)
    service = SubventionClaimService(db)
    claim = await service.cancel_claim(org_id, claim_id, data.reason, current_user)
    await db.commit()
    return SubventionClaimResponse.model_validate(claim)


@router.post(
    "/{claim_id}/certificate/generate",
    response_model=GeneratedDocumentResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_WRITE"))],
)
async def generate_claim_certificate(
    claim_id: UUID,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> GeneratedDocumentResponse:
    _require_idempotency_key(idempotency_key)
    org_id = _require_org(current_user)
    service = SubventionClaimService(db)
    generated = await service.generate_claim_certificate(org_id, claim_id, current_user)
    await db.commit()
    return GeneratedDocumentResponse.model_validate(generated)


@router.get(
    "/{claim_id}/certificate.pdf",
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def download_claim_certificate(
    claim_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    org_id = _require_org(current_user)
    service = SubventionClaimService(db)
    generated = await service.latest_claim_certificate(org_id, claim_id)
    dms = DocumentService(db)
    result = await dms.download_document(generated.dms_document_id, user_id=current_user.id)
    if result is None:
        raise BadRequestException(
            "Generated certificate file is not available",
            error_code="IIF_CLAIM_CERTIFICATE_FILE_NOT_FOUND",
        )
    storage_path, file_name, mime_type = result
    full_path = os.path.join(dms.upload_path, storage_path)
    if not os.path.exists(full_path):
        raise BadRequestException(
            "Generated certificate file is not available",
            error_code="IIF_CLAIM_CERTIFICATE_FILE_NOT_FOUND",
        )
    return FileResponse(path=full_path, filename=file_name, media_type=mime_type)


# ---------------------------------------------------------------------------
# Claim report — JSON + CSV stream
# ---------------------------------------------------------------------------


@router.get(
    "/{claim_id}/report",
    response_model=ClaimReportResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def get_claim_report(
    claim_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> ClaimReportResponse:
    """Structured report payload (JSON)."""
    org_id = _require_org(current_user)
    service = SubventionClaimService(db)
    return await service.generate_claim_report(org_id, claim_id)


def _report_to_csv(payload: ClaimReportResponse) -> str:
    """Render a flat, multi-section CSV from the structured report."""
    buf = io.StringIO()
    w = csv.writer(buf)

    def header_row(*cols: str) -> None:
        w.writerow(list(cols))

    def kv(key: str, value: Any) -> None:
        w.writerow([key, "" if value is None else str(value)])

    header_row("Section", "Subvention claim report")
    w.writerow([])

    # Header block
    h = payload.header
    header_row("Header")
    kv("Scheme code", h.scheme_code)
    kv("Scheme name", h.scheme_name)
    kv("Implementing agency", h.implementing_agency)
    kv("Administering ministry", h.administering_ministry)
    kv("Borrower entity", h.borrower_entity_name)
    kv("Loan account number", h.loan_account_number)
    kv("Sanction date", h.sanction_date)
    kv("Tenure (months)", h.tenure_months)
    kv("Period start", h.period_start)
    kv("Period end", h.period_end)
    kv("Claim frequency", h.claim_frequency)
    w.writerow([])

    # Interest calculation
    header_row("Interest calculation (per tranche)")
    header_row(
        "Tranche #",
        "Disbursement ref",
        "Disbursed amount",
        "Disbursement date",
        "Opening balance",
        "Interest rate (%)",
        "Interest for period",
        "Eligible subvention",
    )
    for line in payload.interest_calculation:
        w.writerow(
            [
                line.tranche_number,
                line.disbursement_reference or "",
                line.disbursed_amount,
                line.disbursement_date or "",
                line.opening_balance,
                line.interest_rate,
                line.interest_for_period,
                line.eligible_subvention,
            ]
        )
    w.writerow([])

    # Repayment record
    header_row("Repayment record (per EMI/EPI allocation)")
    header_row(
        "Installment #",
        "Due date",
        "Installment status",
        "EMI/EPI due",
        "Principal due",
        "Interest due",
        "Penal due",
        "Receipt #",
        "Value date",
        "Instrument / UTR",
        "Receipt amount",
        "Interest",
        "Principal",
        "Penal",
        "Charges",
    )
    for r in payload.repayment_record:
        w.writerow(
            [
                r.installment_number or "",
                r.due_date or "",
                r.installment_status or "",
                r.emi_amount or "",
                r.principal_due or "",
                r.interest_due or "",
                r.penal_due or "",
                r.receipt_number,
                r.value_date,
                r.instrument_number or "",
                r.receipt_amount,
                r.allocated_to_interest,
                r.allocated_to_principal,
                r.allocated_to_penal,
                r.allocated_to_charges,
            ]
        )
    w.writerow([])

    # Account status
    header_row("Account status")
    kv("Asset classification", payload.account_status.asset_classification)
    kv("Days past due", payload.account_status.days_past_due)
    kv("Last EMI status", payload.account_status.last_emi_status)
    w.writerow([])

    # Declaration
    header_row("Declaration")
    kv("Text", payload.declaration_text)
    kv("Signed by (user id)", payload.declaration_signed_by)
    kv("Signed at", payload.declaration_signed_at)
    w.writerow([])

    # Summary
    header_row("Summary")
    for k, v in payload.summary.items():
        kv(k, v)
    w.writerow([])

    # Footer
    header_row("Footer")
    kv("Claim reference", payload.footer.claim_reference)
    kv("Generated at", payload.footer.generated_at)
    kv("Report version", payload.footer.version)
    return buf.getvalue()


def _report_rows(payload: ClaimReportResponse) -> list[list[str]]:
    """Return report rows shared by CSV, XLSX, and PDF renderers."""
    return list(csv.reader(io.StringIO(_report_to_csv(payload))))


def _report_to_xlsx(payload: ClaimReportResponse) -> bytes:
    """Render the claim report as a native XLSX workbook."""
    return build_xlsx(_report_rows(payload), sheet_name="Claim Report")


def _report_to_pdf(payload: ClaimReportResponse) -> bytes:
    """Render the claim report as a simple text PDF."""
    lines = [" | ".join(row) for row in _report_rows(payload)]
    title = f"Interest Subvention Claim Report - {payload.footer.claim_reference}"
    return build_text_pdf(title, lines)


@router.get(
    "/{claim_id}/report.csv",
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def get_claim_report_csv(
    claim_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Render the report as a CSV file stream."""
    org_id = _require_org(current_user)
    service = SubventionClaimService(db)
    payload = await service.generate_claim_report(org_id, claim_id)
    csv_text = _report_to_csv(payload)
    filename = f"{payload.footer.claim_reference.replace('/', '_')}.csv"
    return StreamingResponse(
        iter([csv_text]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/{claim_id}/report.xlsx",
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def get_claim_report_xlsx(
    claim_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Render the report as a native XLSX file stream."""
    org_id = _require_org(current_user)
    service = SubventionClaimService(db)
    payload = await service.generate_claim_report(org_id, claim_id)
    filename = f"{payload.footer.claim_reference.replace('/', '_')}.xlsx"
    return StreamingResponse(
        iter([_report_to_xlsx(payload)]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/{claim_id}/report.pdf",
    dependencies=[Depends(RequirePermissions("TREASURY_READ"))],
)
async def get_claim_report_pdf(
    claim_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Render the report as a PDF file stream."""
    org_id = _require_org(current_user)
    service = SubventionClaimService(db)
    payload = await service.generate_claim_report(org_id, claim_id)
    filename = f"{payload.footer.claim_reference.replace('/', '_')}.pdf"
    return StreamingResponse(
        iter([_report_to_pdf(payload)]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
