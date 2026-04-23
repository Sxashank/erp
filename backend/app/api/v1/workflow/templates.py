"""Notification template API endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import RequirePermissions
from app.models.auth.user import User
from app.models.workflow import NotificationTemplate, WorkflowEntityType
from app.schemas.workflow.notification_template import (
    NotificationTemplateCreate,
    NotificationTemplateUpdate,
    NotificationTemplateResponse,
    TemplatePreviewRequest,
    TemplatePreviewResponse,
)
from app.schemas.base import PaginatedResponse, MessageResponse

router = APIRouter()


@router.get("", response_model=PaginatedResponse[NotificationTemplateResponse])
async def list_notification_templates(
    organization_id: UUID = Query(...),
    entity_type: Optional[WorkflowEntityType] = Query(None),
    code: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(RequirePermissions("WORKFLOW_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated list of notification templates."""
    base_conditions = [
        NotificationTemplate.organization_id == organization_id,
        NotificationTemplate.is_active == True,
    ]

    if entity_type:
        base_conditions.append(NotificationTemplate.entity_type == entity_type)

    if code:
        base_conditions.append(NotificationTemplate.code.ilike(f"%{code}%"))

    # Count total
    count_query = select(NotificationTemplate.id).where(and_(*base_conditions))
    count_result = await db.execute(count_query)
    total = len(count_result.fetchall())

    # Get paginated results
    query = (
        select(NotificationTemplate)
        .where(and_(*base_conditions))
        .order_by(NotificationTemplate.code)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.execute(query)
    templates = result.scalars().all()

    items = [_template_to_response(t) for t in templates]

    return PaginatedResponse.create(items, total, page, page_size)


@router.post("", response_model=NotificationTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_notification_template(
    data: NotificationTemplateCreate,
    current_user: User = Depends(RequirePermissions("WORKFLOW_CREATE")),
    db: AsyncSession = Depends(get_db),
):
    """Create a new notification template."""
    # Check for duplicate code
    existing = await db.execute(
        select(NotificationTemplate).where(
            and_(
                NotificationTemplate.organization_id == data.organization_id,
                NotificationTemplate.code == data.code,
                NotificationTemplate.is_active == True,
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Notification template with code '{data.code}' already exists",
        )

    template = NotificationTemplate(
        organization_id=data.organization_id,
        code=data.code,
        name=data.name,
        entity_type=data.entity_type,
        email_subject=data.email_subject,
        email_body=data.email_body,
        notification_title=data.notification_title,
        notification_body=data.notification_body,
        available_variables=data.available_variables,
        created_by=current_user.id,
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)

    return _template_to_response(template)


@router.get("/{template_id}", response_model=NotificationTemplateResponse)
async def get_notification_template(
    template_id: UUID,
    current_user: User = Depends(RequirePermissions("WORKFLOW_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get a notification template by ID."""
    query = select(NotificationTemplate).where(
        and_(
            NotificationTemplate.id == template_id,
            NotificationTemplate.is_active == True,
        )
    )
    result = await db.execute(query)
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification template not found",
        )

    return _template_to_response(template)


@router.get("/by-code/{code}", response_model=NotificationTemplateResponse)
async def get_notification_template_by_code(
    code: str,
    organization_id: UUID = Query(...),
    entity_type: Optional[WorkflowEntityType] = Query(None),
    current_user: User = Depends(RequirePermissions("WORKFLOW_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get a notification template by code.

    If entity_type is provided, tries to find entity-specific template first,
    falls back to generic template if not found.
    """
    conditions = [
        NotificationTemplate.organization_id == organization_id,
        NotificationTemplate.code == code,
        NotificationTemplate.is_active == True,
    ]

    # First try entity-specific template
    if entity_type:
        query = select(NotificationTemplate).where(
            and_(*conditions, NotificationTemplate.entity_type == entity_type)
        )
        result = await db.execute(query)
        template = result.scalar_one_or_none()
        if template:
            return _template_to_response(template)

    # Fall back to generic template
    query = select(NotificationTemplate).where(
        and_(*conditions, NotificationTemplate.entity_type.is_(None))
    )
    result = await db.execute(query)
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification template with code '{code}' not found",
        )

    return _template_to_response(template)


@router.put("/{template_id}", response_model=NotificationTemplateResponse)
async def update_notification_template(
    template_id: UUID,
    data: NotificationTemplateUpdate,
    current_user: User = Depends(RequirePermissions("WORKFLOW_UPDATE")),
    db: AsyncSession = Depends(get_db),
):
    """Update a notification template."""
    query = select(NotificationTemplate).where(
        and_(
            NotificationTemplate.id == template_id,
            NotificationTemplate.is_active == True,
        )
    )
    result = await db.execute(query)
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification template not found",
        )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)

    template.updated_by = current_user.id
    await db.commit()
    await db.refresh(template)

    return _template_to_response(template)


@router.delete("/{template_id}", response_model=MessageResponse)
async def delete_notification_template(
    template_id: UUID,
    current_user: User = Depends(RequirePermissions("WORKFLOW_DELETE")),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a notification template."""
    query = select(NotificationTemplate).where(
        and_(
            NotificationTemplate.id == template_id,
            NotificationTemplate.is_active == True,
        )
    )
    result = await db.execute(query)
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification template not found",
        )

    template.soft_delete(current_user.id)
    await db.commit()

    return MessageResponse(message="Notification template deleted successfully")


@router.post("/{template_id}/preview", response_model=TemplatePreviewResponse)
async def preview_notification_template(
    template_id: UUID,
    data: TemplatePreviewRequest,
    current_user: User = Depends(RequirePermissions("WORKFLOW_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Preview a notification template with sample context data.

    Renders the template with the provided context variables to show
    what the final email will look like.
    """
    query = select(NotificationTemplate).where(
        and_(
            NotificationTemplate.id == template_id,
            NotificationTemplate.is_active == True,
        )
    )
    result = await db.execute(query)
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification template not found",
        )

    # Render template with context
    subject = _render_template(template.email_subject, data.context)
    body = _render_template(template.email_body, data.context)

    return TemplatePreviewResponse(subject=subject, body=body)


@router.get("/{template_id}/variables", response_model=list[str])
async def get_template_variables(
    template_id: UUID,
    current_user: User = Depends(RequirePermissions("WORKFLOW_VIEW")),
    db: AsyncSession = Depends(get_db),
):
    """Get the list of available variables for a notification template."""
    query = select(NotificationTemplate).where(
        and_(
            NotificationTemplate.id == template_id,
            NotificationTemplate.is_active == True,
        )
    )
    result = await db.execute(query)
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification template not found",
        )

    return template.available_variables or []


def _template_to_response(template: NotificationTemplate) -> NotificationTemplateResponse:
    """Convert template model to response."""
    return NotificationTemplateResponse(
        id=template.id,
        organization_id=template.organization_id,
        code=template.code,
        name=template.name,
        entity_type=template.entity_type,
        email_subject=template.email_subject,
        email_body=template.email_body,
        notification_title=template.notification_title,
        notification_body=template.notification_body,
        available_variables=template.available_variables,
        created_at=template.created_at,
        updated_at=template.updated_at,
        is_active=template.is_active,
    )


def _render_template(template: str, context: dict) -> str:
    """Render template string with context variables.

    Uses simple {variable_name} placeholder substitution.
    Missing variables are left as placeholders.
    """
    result = template
    for key, value in context.items():
        placeholder = f"{{{key}}}"
        result = result.replace(placeholder, str(value) if value is not None else "")
    return result
