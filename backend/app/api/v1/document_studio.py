"""Platform Document Studio endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_current_user, get_db_with_tenant
from app.models.auth.user import User
from app.models.document_studio import DocumentModule
from app.schemas.document_studio import (
    GeneratedDocumentResponse,
    GenerateDocumentRequest,
    PreviewRequest,
    PreviewResponse,
    TemplateCreate,
    TemplateDetail,
    TemplateListResponse,
    TemplateSummary,
    TemplateVersionCreate,
    TemplateVersionResponse,
    VariableDefinition,
    VariableListResponse,
)
from app.services.document_studio_service import DocumentStudioService

router = APIRouter(prefix="/document-studio", tags=["Document Studio"])


@router.get(
    "/templates",
    response_model=TemplateListResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("DMS_DOCUMENT_VIEW"))],
)
async def list_templates(
    module: DocumentModule | None = Query(None),
    document_type: str | None = Query(None, alias="documentType"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> TemplateListResponse:
    service = DocumentStudioService(db)
    rows = await service.list_templates(
        organization_id=current_user.organization_id,
        module=module,
        document_type=document_type,
    )
    return TemplateListResponse(
        items=[TemplateSummary.model_validate(row) for row in rows],
        total=len(rows),
    )


@router.get(
    "/templates/{template_id}",
    response_model=TemplateDetail,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("DMS_DOCUMENT_VIEW"))],
)
async def get_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> TemplateDetail:
    service = DocumentStudioService(db)
    row = await service.get_template(
        organization_id=current_user.organization_id,
        template_id=template_id,
    )
    return TemplateDetail.model_validate(row)


@router.post(
    "/templates",
    response_model=TemplateDetail,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermissions("DMS_DOCUMENT_UPLOAD"))],
)
async def create_template(
    data: TemplateCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> TemplateDetail:
    service = DocumentStudioService(db)
    row = await service.create_template(
        organization_id=current_user.organization_id,
        data=data.model_dump(),
        created_by=current_user.id,
    )
    await db.refresh(row, attribute_names=["versions"])
    return TemplateDetail.model_validate(row)


@router.post(
    "/templates/{template_id}/versions",
    response_model=TemplateVersionResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermissions("DMS_DOCUMENT_UPLOAD"))],
)
async def create_template_version(
    template_id: UUID,
    data: TemplateVersionCreate,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> TemplateVersionResponse:
    service = DocumentStudioService(db)
    row = await service.create_version(
        organization_id=current_user.organization_id,
        template_id=template_id,
        data=data.model_dump(),
        created_by=current_user.id,
    )
    return TemplateVersionResponse.model_validate(row)


@router.post(
    "/templates/{version_id}/submit-review",
    response_model=TemplateVersionResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("DMS_DOCUMENT_UPDATE"))],
)
async def submit_template_version_for_review(
    version_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> TemplateVersionResponse:
    service = DocumentStudioService(db)
    row = await service.transition_version(
        organization_id=current_user.organization_id,
        version_id=version_id,
        action="submit-review",
        user_id=current_user.id,
    )
    return TemplateVersionResponse.model_validate(row)


@router.post(
    "/templates/{version_id}/approve",
    response_model=TemplateVersionResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("DMS_DOCUMENT_UPDATE"))],
)
async def approve_template_version(
    version_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> TemplateVersionResponse:
    service = DocumentStudioService(db)
    row = await service.transition_version(
        organization_id=current_user.organization_id,
        version_id=version_id,
        action="approve",
        user_id=current_user.id,
    )
    return TemplateVersionResponse.model_validate(row)


@router.post(
    "/templates/{version_id}/publish",
    response_model=TemplateVersionResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("DMS_DOCUMENT_UPDATE"))],
)
async def publish_template_version(
    version_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> TemplateVersionResponse:
    service = DocumentStudioService(db)
    row = await service.transition_version(
        organization_id=current_user.organization_id,
        version_id=version_id,
        action="publish",
        user_id=current_user.id,
    )
    return TemplateVersionResponse.model_validate(row)


@router.get(
    "/variables",
    response_model=VariableListResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("DMS_DOCUMENT_VIEW"))],
)
async def list_variables(
    module: DocumentModule,
    document_type: str | None = Query(None, alias="documentType"),
    db: AsyncSession = Depends(get_db_with_tenant),
) -> VariableListResponse:
    service = DocumentStudioService(db)
    items = await service.variables(module=module, document_type=document_type)
    return VariableListResponse(
        module=module,
        document_type=document_type,
        items=[VariableDefinition.model_validate(item) for item in items],
    )


@router.post(
    "/preview",
    response_model=PreviewResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("DMS_DOCUMENT_VIEW"))],
)
async def preview_document(
    data: PreviewRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> PreviewResponse:
    service = DocumentStudioService(db)
    rendered_html, missing = await service.preview(
        organization_id=current_user.organization_id,
        template_version_id=data.template_version_id,
        body=data.body,
        header=data.header,
        footer=data.footer,
        context=data.context,
    )
    return PreviewResponse(rendered_html=rendered_html, missing_variables=missing)


@router.post(
    "/generate",
    response_model=GeneratedDocumentResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions("DMS_DOCUMENT_UPLOAD"))],
)
async def generate_document(
    data: GenerateDocumentRequest,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user: User = Depends(get_current_user),
) -> GeneratedDocumentResponse:
    service = DocumentStudioService(db)
    row = await service.generate(
        organization_id=current_user.organization_id,
        data=data.model_dump(),
        user_id=current_user.id,
    )
    return GeneratedDocumentResponse.model_validate(row)
