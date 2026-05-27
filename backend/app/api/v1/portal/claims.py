"""Borrower-portal claim lifecycle endpoints."""

from __future__ import annotations

import os
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Header, Query, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.lending.iif.claims import _report_to_csv, _report_to_pdf, _report_to_xlsx
from app.api.v1.portal.auth import get_portal_db_with_tenant, get_portal_user
from app.core.exceptions import BadRequestException
from app.core.upload_validation import DOCUMENT_MIME_TYPES, validate_upload
from app.models.lending.masters import LendingOption
from app.schemas.base import CamelSchema
from app.schemas.portal.claim import (
    BorrowerClaimCreateRequest,
    BorrowerClaimDocument,
    BorrowerClaimEnrollmentListResponse,
    BorrowerClaimItem,
    BorrowerClaimListResponse,
    BorrowerClaimSubmitRequest,
    BorrowerClaimsWorkbenchResponse,
    BorrowerEligibleClaimPeriodsResponse,
)
from app.services.dms.document_service import DocumentService
from app.services.lending.iif.subvention_claim_service import (
    SubventionClaimService,
)
from app.services.portal.claim_service import PortalClaimService

router = APIRouter(prefix="/claims", tags=["Borrower Portal · Claims"])


class PortalClaimDocumentTypeOption(CamelSchema):
    code: str
    label: str


def _require_idempotency_key(key: str | None) -> None:
    if not key:
        raise BadRequestException(
            "Idempotency-Key header is required for this operation",
            error_code="IDEMPOTENCY_KEY_REQUIRED",
        )


@router.get(
    "/workbench",
    response_model=BorrowerClaimsWorkbenchResponse,
    response_model_by_alias=True,
    summary="Get borrower claim center data",
)
async def claim_workbench(
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
) -> BorrowerClaimsWorkbenchResponse:
    service = PortalClaimService(db)
    return await service.get_workbench(user)


@router.get(
    "/document-types",
    response_model=list[PortalClaimDocumentTypeOption],
    response_model_by_alias=True,
    summary="List configured claim document types",
)
async def list_claim_document_types(
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
) -> list[PortalClaimDocumentTypeOption]:
    stmt = (
        select(LendingOption)
        .where(
            LendingOption.organization_id == user.organization_id,
            LendingOption.option_group == "IIF_CLAIM_DOCUMENT_TYPE",
            LendingOption.is_active.is_(True),
        )
        .order_by(LendingOption.sort_order.asc(), LendingOption.label.asc())
    )
    rows = list((await db.execute(stmt)).scalars().all())
    return [PortalClaimDocumentTypeOption(code=row.code, label=row.label) for row in rows]


@router.get(
    "/enrollments",
    response_model=BorrowerClaimEnrollmentListResponse,
    response_model_by_alias=True,
    summary="List accessible claim enrollments",
)
async def list_enrollments(
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
) -> BorrowerClaimEnrollmentListResponse:
    service = PortalClaimService(db)
    return await service.list_enrollments(user)


@router.get(
    "/enrollments/{enrollment_id}/eligible-periods",
    response_model=BorrowerEligibleClaimPeriodsResponse,
    response_model_by_alias=True,
    summary="List eligible claim periods for one enrollment",
)
async def list_eligible_periods(
    enrollment_id: UUID,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
) -> BorrowerEligibleClaimPeriodsResponse:
    service = PortalClaimService(db)
    return await service.eligible_periods(user, enrollment_id)


@router.get(
    "",
    response_model=BorrowerClaimListResponse,
    response_model_by_alias=True,
    summary="List borrower-visible claims",
)
async def list_claims(
    loan_account_id: UUID | None = Query(None, alias="loanAccountId"),
    status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200, alias="pageSize"),
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
) -> BorrowerClaimListResponse:
    service = PortalClaimService(db)
    return await service.list_claims(
        user,
        loan_account_id=loan_account_id,
        status=status,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{claim_id}",
    response_model=BorrowerClaimItem,
    response_model_by_alias=True,
    summary="Get one borrower claim",
)
async def get_claim(
    claim_id: UUID,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
) -> BorrowerClaimItem:
    service = PortalClaimService(db)
    return await service.get_claim(user, claim_id)


@router.post(
    "",
    response_model=BorrowerClaimItem,
    response_model_by_alias=True,
    summary="Create a borrower claim draft",
)
async def create_claim(
    payload: BorrowerClaimCreateRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
) -> BorrowerClaimItem:
    _require_idempotency_key(idempotency_key)
    service = PortalClaimService(db)
    result = await service.create_claim(user, payload)
    await db.commit()
    return result


@router.post(
    "/{claim_id}/documents/upload",
    response_model=BorrowerClaimItem,
    response_model_by_alias=True,
    summary="Upload one supporting document to a draft borrower claim",
)
async def upload_claim_document(
    claim_id: UUID,
    file: UploadFile = File(...),
    document_name: str | None = Form(default=None, alias="documentName"),
    document_category: str = Form(
        default="BORROWER_CLAIM_SUPPORTING_DOCUMENT", alias="documentCategory"
    ),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
) -> BorrowerClaimItem:
    _require_idempotency_key(idempotency_key)
    raw = await file.read()
    validation = validate_upload(
        filename=file.filename or "upload",
        content_type=file.content_type or "application/octet-stream",
        body=raw,
        allowed_mime_types=DOCUMENT_MIME_TYPES,
    )
    service = PortalClaimService(db)
    result = await service.upload_claim_document(
        user,
        claim_id,
        file_bytes=raw,
        file_name=validation.safe_filename,
        file_size_bytes=validation.size_bytes,
        file_mime_type=validation.content_type,
        document_name=document_name,
        document_category=document_category,
    )
    await db.commit()
    return result


@router.post(
    "/{claim_id}/submit",
    response_model=BorrowerClaimItem,
    response_model_by_alias=True,
    summary="Submit a borrower claim draft",
)
async def submit_claim(
    claim_id: UUID,
    payload: BorrowerClaimSubmitRequest | None = None,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
) -> BorrowerClaimItem:
    _require_idempotency_key(idempotency_key)
    service = PortalClaimService(db)
    result = await service.submit_claim(user, claim_id, payload)
    await db.commit()
    return result


@router.get(
    "/{claim_id}/report.csv",
    summary="Download the borrower claim report as CSV",
)
async def claim_report_csv(
    claim_id: UUID,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
) -> StreamingResponse:
    portal_service = PortalClaimService(db)
    claim = await portal_service.get_claim_record(user, claim_id)

    service = SubventionClaimService(db)
    payload = await service.generate_claim_report(
        claim.organization_id,
        claim.id,
    )
    csv_text = _report_to_csv(payload)
    filename = f"IIF-{claim.claim_reference.replace('/', '_')}.csv"
    return StreamingResponse(
        iter([csv_text]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/{claim_id}/report.xlsx",
    summary="Download the borrower claim report as XLSX",
)
async def claim_report_xlsx(
    claim_id: UUID,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
) -> StreamingResponse:
    portal_service = PortalClaimService(db)
    claim = await portal_service.get_claim_record(user, claim_id)

    service = SubventionClaimService(db)
    payload = await service.generate_claim_report(claim.organization_id, claim.id)
    filename = f"IIF-{claim.claim_reference.replace('/', '_')}.xlsx"
    return StreamingResponse(
        iter([_report_to_xlsx(payload)]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/{claim_id}/report.pdf",
    summary="Download the borrower claim report as PDF",
)
async def claim_report_pdf(
    claim_id: UUID,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
) -> StreamingResponse:
    portal_service = PortalClaimService(db)
    claim = await portal_service.get_claim_record(user, claim_id)

    service = SubventionClaimService(db)
    payload = await service.generate_claim_report(claim.organization_id, claim.id)
    filename = f"IIF-{claim.claim_reference.replace('/', '_')}.pdf"
    return StreamingResponse(
        iter([_report_to_pdf(payload)]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/{claim_id}/certificate.pdf",
    summary="Download the generated SFC IIF claim certificate",
)
async def claim_certificate_pdf(
    claim_id: UUID,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
) -> FileResponse:
    portal_service = PortalClaimService(db)
    claim = await portal_service.get_claim_record(user, claim_id)

    service = SubventionClaimService(db)
    generated = await service.latest_claim_certificate(
        claim.organization_id,
        claim.id,
        portal_visible_only=True,
    )
    dms_service = DocumentService(db)
    result = await dms_service.download_document(
        generated.dms_document_id,
        user_id=user.id,
    )
    if result is None:
        raise BadRequestException(
            "Generated certificate file is not available",
            error_code="IIF_CLAIM_CERTIFICATE_FILE_NOT_FOUND",
        )
    storage_path, file_name, mime_type = result
    full_path = os.path.join(dms_service.upload_path, storage_path)
    if not os.path.exists(full_path):
        raise BadRequestException(
            "Generated certificate file is not available",
            error_code="IIF_CLAIM_CERTIFICATE_FILE_NOT_FOUND",
        )

    return FileResponse(path=full_path, filename=file_name, media_type=mime_type)


@router.get(
    "/{claim_id}/documents/{document_id}/download",
    summary="Download one borrower claim document",
)
async def download_claim_document(
    claim_id: UUID,
    document_id: UUID,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
) -> FileResponse:
    service = PortalClaimService(db)
    claim = await service.get_claim_record(user, claim_id)
    doc_meta = next(
        (
            BorrowerClaimDocument.model_validate(doc)
            for doc in (claim.documents or [])
            if isinstance(doc, dict) and str(doc.get("document_id") or "") == str(document_id)
        ),
        None,
    )
    if doc_meta is None or doc_meta.document_id is None:
        raise BadRequestException(
            "Document not found",
            error_code="DOCUMENT_NOT_FOUND",
        )

    dms_service = DocumentService(db)
    result = await dms_service.download_document(
        doc_meta.document_id,
        user_id=user.id,
    )
    if result is None:
        raise BadRequestException(
            "Document file is not available",
            error_code="DOCUMENT_FILE_NOT_FOUND",
        )
    storage_path, file_name, mime_type = result
    full_path = os.path.join(dms_service.upload_path, storage_path)
    if not os.path.exists(full_path):
        raise BadRequestException(
            "Document file is not available",
            error_code="DOCUMENT_FILE_NOT_FOUND",
        )

    return FileResponse(
        path=full_path,
        filename=file_name,
        media_type=mime_type,
    )
