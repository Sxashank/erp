"""Cross-module document retrieval endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_current_user, get_db_with_tenant
from app.models.auth.user import User
from app.schemas.dms.filing import EntityVaultResponse
from app.schemas.document_studio import (
    DocumentPackageAddItem,
    DocumentPackageCreate,
    DocumentPackageDetailResponse,
    DocumentPackageFinalize,
    DocumentPackageItemResponse,
    DocumentPackageListResponse,
    DocumentPackageResponse,
)
from app.services.dms.filing_service import DocumentFilingService
from app.services.document_studio_service import DocumentStudioService

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get(
    "/entity/{entity_type}/{entity_id}",
    response_model=EntityVaultResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("DMS_DOCUMENT_VIEW"))],
)
async def get_documents_for_entity(
    entity_type: str,
    entity_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> EntityVaultResponse:
    service = DocumentFilingService(db)
    folders, documents = await service.entity_vault(
        organization_id=current_user.organization_id,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    return EntityVaultResponse(
        entity_type=entity_type,
        entity_id=entity_id,
        folders=folders,
        documents=documents,
    )


@router.get(
    "/packages",
    response_model=DocumentPackageListResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("DMS_DOCUMENT_VIEW"))],
)
async def list_document_packages(
    entity_type: str | None = Query(None, alias="entityType"),
    entity_id: UUID | None = Query(None, alias="entityId"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> DocumentPackageListResponse:
    service = DocumentStudioService(db)
    rows = await service.list_packages(
        organization_id=current_user.organization_id,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    return DocumentPackageListResponse(
        items=[DocumentPackageResponse.model_validate(row) for row in rows],
        total=len(rows),
    )


@router.post(
    "/packages",
    response_model=DocumentPackageResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermissions("DMS_DOCUMENT_UPLOAD"))],
)
async def create_document_package(
    data: DocumentPackageCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> DocumentPackageResponse:
    service = DocumentStudioService(db)
    row = await service.create_package(
        organization_id=current_user.organization_id,
        data=data.model_dump(),
        created_by=current_user.id,
    )
    return DocumentPackageResponse.model_validate(row)


@router.post(
    "/packages/{package_id}/items",
    response_model=DocumentPackageItemResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermissions("DMS_DOCUMENT_UPLOAD"))],
)
async def add_document_package_item(
    package_id: UUID,
    data: DocumentPackageAddItem,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> DocumentPackageItemResponse:
    service = DocumentStudioService(db)
    row = await service.add_package_item(
        organization_id=current_user.organization_id,
        package_id=package_id,
        data=data.model_dump(),
        created_by=current_user.id,
    )
    return DocumentPackageItemResponse.model_validate(row)


@router.post(
    "/packages/{package_id}/finalize",
    response_model=DocumentPackageDetailResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("DMS_DOCUMENT_UPDATE"))],
)
async def finalize_document_package(
    package_id: UUID,
    data: DocumentPackageFinalize,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> DocumentPackageDetailResponse:
    service = DocumentStudioService(db)
    row, items = await service.finalize_package(
        organization_id=current_user.organization_id,
        package_id=package_id,
        manifest=data.manifest,
        user_id=current_user.id,
    )
    return DocumentPackageDetailResponse(
        **DocumentPackageResponse.model_validate(row).model_dump(),
        items=[DocumentPackageItemResponse.model_validate(item) for item in items],
    )


@router.get(
    "/packages/{package_id}",
    response_model=DocumentPackageDetailResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("DMS_DOCUMENT_VIEW"))],
)
async def get_document_package(
    package_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> DocumentPackageDetailResponse:
    service = DocumentStudioService(db)
    row, items = await service.get_package(
        organization_id=current_user.organization_id,
        package_id=package_id,
    )
    return DocumentPackageDetailResponse(
        **DocumentPackageResponse.model_validate(row).model_dump(),
        items=[DocumentPackageItemResponse.model_validate(item) for item in items],
    )
