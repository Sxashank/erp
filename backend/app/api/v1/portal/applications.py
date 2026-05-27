"""Borrower-portal: loan applications endpoints.

Every endpoint authenticates the borrower via
:func:`app.api.v1.portal.auth.get_portal_user` and intersects URL/body
entity-ids with the user's accessible set
(:mod:`app.services.portal.entity_access`).
"""

from __future__ import annotations

import hashlib
import os
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    Header,
    Query,
    UploadFile,
)
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.portal.auth import get_portal_db_with_tenant, get_portal_user
from app.core.exceptions import BadRequestException
from app.core.upload_validation import DOCUMENT_MIME_TYPES, validate_upload
from app.schemas.lending.lifecycle import (
    ApplicationQueryListResponse,
    ApplicationQueryResponse,
    RespondToQueryRequest,
)
from app.schemas.portal.application import (
    ApplicationDetailResponse,
    ApplicationDocumentResponse,
    ApplicationListResponse,
    ApplicationWithdrawRequest,
    CreateApplicationRequest,
    UpdateApplicationRequest,
    UploadDocumentResponse,
)
from app.services.dms.document_service import DocumentService
from app.services.lending.application_query_service import ApplicationQueryService
from app.services.portal.application_service import PortalApplicationService
from app.services.portal.entity_access import assert_application_access

router = APIRouter(prefix="/applications", tags=["Borrower Portal · Applications"])


def _require_idempotency_key(key: str | None) -> None:
    if not key:
        raise BadRequestException(
            "Idempotency-Key header is required for this operation",
            error_code="IDEMPOTENCY_KEY_REQUIRED",
        )


@router.get(
    "",
    response_model=ApplicationListResponse,
    response_model_by_alias=True,
    summary="List borrower's loan applications",
)
async def list_applications(
    status: str | None = Query(None),
    entity_id: UUID | None = Query(None, alias="entityId"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200, alias="pageSize"),
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
) -> ApplicationListResponse:
    service = PortalApplicationService(db)
    return await service.list_applications(
        portal_user=user,
        page=page,
        page_size=page_size,
        status=status,
        entity_id=entity_id,
    )


@router.get(
    "/{application_id}",
    response_model=ApplicationDetailResponse,
    response_model_by_alias=True,
    summary="Get one application with utilization, documents and status timeline",
)
async def get_application(
    application_id: UUID,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
) -> ApplicationDetailResponse:
    service = PortalApplicationService(db)
    return await service.get_application(portal_user=user, application_id=application_id)


@router.post(
    "",
    response_model=ApplicationDetailResponse,
    response_model_by_alias=True,
    summary="Create a draft SFC loan application",
)
async def create_application(
    payload: CreateApplicationRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
) -> ApplicationDetailResponse:
    _require_idempotency_key(idempotency_key)
    service = PortalApplicationService(db)
    result = await service.create_application(portal_user=user, payload=payload)
    await db.commit()
    return result


@router.patch(
    "/{application_id}",
    response_model=ApplicationDetailResponse,
    response_model_by_alias=True,
    summary="Update a draft SFC loan application",
)
async def update_application(
    application_id: UUID,
    payload: UpdateApplicationRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
) -> ApplicationDetailResponse:
    _require_idempotency_key(idempotency_key)
    service = PortalApplicationService(db)
    result = await service.update_application(
        portal_user=user,
        application_id=application_id,
        payload=payload,
    )
    await db.commit()
    return result


@router.post(
    "/{application_id}/submit",
    response_model=ApplicationDetailResponse,
    response_model_by_alias=True,
    summary="Submit a draft SFC loan application for review",
)
async def submit_application(
    application_id: UUID,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
) -> ApplicationDetailResponse:
    _require_idempotency_key(idempotency_key)
    service = PortalApplicationService(db)
    result = await service.submit_application(
        portal_user=user,
        application_id=application_id,
    )
    await db.commit()
    return result


@router.post(
    "/{application_id}/resubmit",
    response_model=ApplicationDetailResponse,
    response_model_by_alias=True,
    summary="Resubmit a queried SFC loan application",
)
async def resubmit_application(
    application_id: UUID,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
) -> ApplicationDetailResponse:
    _require_idempotency_key(idempotency_key)
    service = PortalApplicationService(db)
    result = await service.resubmit_application(
        portal_user=user,
        application_id=application_id,
    )
    await db.commit()
    return result


@router.post(
    "/{application_id}/withdraw",
    response_model=ApplicationDetailResponse,
    response_model_by_alias=True,
    summary="Withdraw a borrower application before sanction",
)
async def withdraw_application(
    application_id: UUID,
    payload: ApplicationWithdrawRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
) -> ApplicationDetailResponse:
    _require_idempotency_key(idempotency_key)
    service = PortalApplicationService(db)
    result = await service.withdraw_application(
        portal_user=user,
        application_id=application_id,
        reason=payload.reason,
    )
    await db.commit()
    return result


@router.get(
    "/{application_id}/queries",
    response_model=ApplicationQueryListResponse,
    response_model_by_alias=True,
    summary="List borrower-visible application queries",
)
async def list_application_queries(
    application_id: UUID,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
) -> ApplicationQueryListResponse:
    application = await assert_application_access(user, application_id, db)
    service = ApplicationQueryService(db)
    rows = await service.list_for_application(
        organization_id=application.organization_id,
        application_id=application_id,
    )
    items = [ApplicationQueryResponse.model_validate(row) for row in rows]
    return ApplicationQueryListResponse(items=items, total=len(items))


@router.post(
    "/{application_id}/queries/{query_id}/respond",
    response_model=ApplicationQueryResponse,
    response_model_by_alias=True,
    summary="Respond to a borrower application query",
)
async def respond_to_application_query(
    application_id: UUID,
    query_id: UUID,
    payload: RespondToQueryRequest,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
) -> ApplicationQueryResponse:
    _require_idempotency_key(idempotency_key)
    application = await assert_application_access(user, application_id, db)
    service = ApplicationQueryService(db)
    query = await service.get(organization_id=application.organization_id, query_id=query_id)
    if query.application_id != application_id:
        raise BadRequestException(
            "Application query was not found for this application",
            error_code="APPLICATION_QUERY_NOT_FOUND",
        )
    result = await service.respond_to_query(
        organization_id=application.organization_id,
        query_id=query_id,
        portal_user_id=user.id,
        response_text=payload.response_text,
        response_attachments=payload.response_attachments,
    )
    await db.commit()
    await db.refresh(result)
    return ApplicationQueryResponse.model_validate(result)


@router.post(
    "/{application_id}/documents/upload",
    response_model=UploadDocumentResponse,
    response_model_by_alias=True,
    summary="Upload a supporting document for an application",
)
async def upload_application_document(
    application_id: UUID,
    file: UploadFile = File(...),
    document_code: str = Form(default="BORROWER_UPLOAD", alias="documentCode"),
    document_name: str | None = Form(default=None, alias="documentName"),
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
) -> UploadDocumentResponse:
    """Upload an application supporting document through the main DMS."""
    _require_idempotency_key(idempotency_key)

    raw = await file.read()
    validation = validate_upload(
        filename=file.filename or "upload",
        content_type=file.content_type or "application/octet-stream",
        body=raw,
        allowed_mime_types=DOCUMENT_MIME_TYPES,
    )

    file_hash = hashlib.sha256(raw).hexdigest()

    service = PortalApplicationService(db)
    doc = await service.upload_document(
        portal_user=user,
        application_id=application_id,
        file_bytes=raw,
        file_name=validation.safe_filename,
        file_size_bytes=validation.size_bytes,
        file_mime_type=validation.content_type,
        document_name=document_name,
        document_code=document_code,
        file_hash=file_hash,
    )
    await db.commit()

    return UploadDocumentResponse(
        id=doc.id,
        application_id=doc.application_id,
        document_code=doc.document_code,
        document_name=doc.document_name,
        file_name=doc.file_name,
        file_size_bytes=doc.file_size_bytes,
        status=doc.status,
        upload_date=doc.upload_date,
    )


@router.get(
    "/{application_id}/documents",
    response_model=list[ApplicationDocumentResponse],
    response_model_by_alias=True,
    summary="List documents on an application",
)
async def list_application_documents(
    application_id: UUID,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
) -> list[ApplicationDocumentResponse]:
    service = PortalApplicationService(db)
    return await service.list_documents(portal_user=user, application_id=application_id)


@router.get(
    "/{application_id}/documents/{document_id}/download",
    summary="Download one application document",
)
async def download_application_document(
    application_id: UUID,
    document_id: UUID,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
) -> FileResponse:
    service = PortalApplicationService(db)
    document = await service.get_document_record(
        portal_user=user,
        application_id=application_id,
        document_id=document_id,
    )

    if document.dms_document_id:
        dms_service = DocumentService(db)
        result = await dms_service.download_document(
            document.dms_document_id,
            user_id=user.id,
        )
        if result is None:
            raise BadRequestException(
                "Document file is not available",
                error_code="DOCUMENT_FILE_NOT_FOUND",
            )
        storage_path, file_name, mime_type = result
        full_path = os.path.join(dms_service.upload_path, storage_path)
    else:
        full_path = document.file_path
        file_name = document.file_name
        mime_type = document.file_mime_type or "application/octet-stream"

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
