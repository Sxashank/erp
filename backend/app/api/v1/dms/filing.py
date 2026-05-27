"""DMS filing rule and entity vault endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_current_user, get_db_with_tenant
from app.models.auth.user import User
from app.schemas.dms.filing import (
    EntityVaultResponse,
    FilingRuleCreate,
    FilingRuleResponse,
    ResolveFolderRequest,
    ResolveFolderResponse,
)
from app.services.dms.filing_service import DocumentFilingService

router = APIRouter(tags=["DMS Filing"])


@router.get(
    "/filing-rules",
    response_model=list[FilingRuleResponse],
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("DMS_FOLDER_VIEW"))],
)
async def list_filing_rules(
    module: str | None = Query(None),
    document_type: str | None = Query(None, alias="documentType"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> list[FilingRuleResponse]:
    service = DocumentFilingService(db)
    await service.ensure_default_rules(
        organization_id=current_user.organization_id,
        created_by=current_user.id,
    )
    rows = await service.list_rules(
        organization_id=current_user.organization_id,
        module=module,
        document_type=document_type,
    )
    return [FilingRuleResponse.model_validate(row) for row in rows]


@router.post(
    "/filing-rules",
    response_model=FilingRuleResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermissions("DMS_FOLDER_CREATE"))],
)
async def create_filing_rule(
    data: FilingRuleCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> FilingRuleResponse:
    service = DocumentFilingService(db)
    row = await service.create_rule(
        organization_id=current_user.organization_id,
        data=data.model_dump(),
        created_by=current_user.id,
    )
    return FilingRuleResponse.model_validate(row)


@router.post(
    "/resolve-folder",
    response_model=ResolveFolderResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("DMS_FOLDER_CREATE"))],
)
async def resolve_folder(
    data: ResolveFolderRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> ResolveFolderResponse:
    service = DocumentFilingService(db)
    folder, path, rule = await service.resolve_folder(
        organization_id=current_user.organization_id,
        module=data.module,
        document_type=data.document_type,
        entity_type=data.entity_type,
        entity_id=data.entity_id,
        context=data.context,
        created_by=current_user.id,
    )
    return ResolveFolderResponse(
        folder=folder,
        path=path,
        rule=FilingRuleResponse.model_validate(rule) if rule else None,
    )


@router.get(
    "/entity-vault/{entity_type}/{entity_id}",
    response_model=EntityVaultResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("DMS_DOCUMENT_VIEW"))],
)
async def get_entity_vault(
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
