"""Notification template API endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.security import get_current_user
from app.models.auth.user import User
from app.models.notification import (
    SysNotificationTemplate,
    NotificationTemplateVariable,
    NotificationCategory,
    NotificationTemplateType,
)
from app.schemas.notification import (
    NotificationTemplateCreate,
    NotificationTemplateUpdate,
    NotificationTemplateResponse,
    NotificationTemplateListResponse,
    TemplateVariableCreate,
    TemplateVariableResponse,
    TemplatePreviewRequest,
    TemplatePreviewResponse,
)

router = APIRouter()


@router.get("", response_model=NotificationTemplateListResponse)
async def list_templates(
    category: Optional[NotificationCategory] = None,
    template_type: Optional[NotificationTemplateType] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List notification templates with filters."""
    conditions = [
        SysNotificationTemplate.is_active == True,
        (
            (SysNotificationTemplate.organization_id == current_user.organization_id) |
            (SysNotificationTemplate.organization_id.is_(None))
        ),
    ]

    if category:
        conditions.append(SysNotificationTemplate.category == category)
    if template_type:
        conditions.append(SysNotificationTemplate.template_type == template_type)
    if is_active is not None:
        conditions.append(SysNotificationTemplate.is_active == is_active)
    if search:
        conditions.append(
            (SysNotificationTemplate.name.ilike(f"%{search}%")) |
            (SysNotificationTemplate.code.ilike(f"%{search}%"))
        )

    # Count query
    count_result = await db.execute(
        select(func.count()).select_from(SysNotificationTemplate).where(and_(*conditions))
    )
    total = count_result.scalar()

    # Data query
    skip = (page - 1) * page_size
    result = await db.execute(
        select(SysNotificationTemplate)
        .where(and_(*conditions))
        .order_by(SysNotificationTemplate.name)
        .offset(skip)
        .limit(page_size)
    )
    templates = list(result.scalars().all())

    return NotificationTemplateListResponse(
        items=[NotificationTemplateResponse.model_validate(t) for t in templates],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{template_id}", response_model=NotificationTemplateResponse)
async def get_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific notification template."""
    result = await db.execute(
        select(SysNotificationTemplate).where(
            SysNotificationTemplate.id == template_id,
            (
                (SysNotificationTemplate.organization_id == current_user.organization_id) |
                (SysNotificationTemplate.organization_id.is_(None))
            ),
        )
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )

    return NotificationTemplateResponse.model_validate(template)


@router.get("/code/{code}", response_model=NotificationTemplateResponse)
async def get_template_by_code(
    code: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a notification template by code."""
    # First try org-specific template
    result = await db.execute(
        select(SysNotificationTemplate).where(
            SysNotificationTemplate.code == code,
            SysNotificationTemplate.organization_id == current_user.organization_id,
            SysNotificationTemplate.is_active == True,
        )
    )
    template = result.scalar_one_or_none()

    if not template:
        # Fall back to global template
        result = await db.execute(
            select(SysNotificationTemplate).where(
                SysNotificationTemplate.code == code,
                SysNotificationTemplate.organization_id.is_(None),
                SysNotificationTemplate.is_active == True,
            )
        )
        template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )

    return NotificationTemplateResponse.model_validate(template)


@router.post("", response_model=NotificationTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    data: NotificationTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new notification template."""
    # Check for duplicate code
    result = await db.execute(
        select(SysNotificationTemplate).where(
            SysNotificationTemplate.code == data.code,
            SysNotificationTemplate.organization_id == current_user.organization_id,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Template with this code already exists",
        )

    template = SysNotificationTemplate(
        organization_id=current_user.organization_id,
        code=data.code,
        name=data.name,
        description=data.description,
        template_type=data.template_type,
        category=data.category,
        channels=data.channels,
        email_subject=data.email_subject,
        email_body_html=data.email_body_html,
        email_body_text=data.email_body_text,
        sms_body=data.sms_body,
        push_title=data.push_title,
        push_body=data.push_body,
        push_image_url=data.push_image_url,
        in_app_title=data.in_app_title,
        in_app_message=data.in_app_message,
        whatsapp_template_id=data.whatsapp_template_id,
        whatsapp_template_params=data.whatsapp_template_params,
        variables=data.variables,
        default_values=data.default_values,
        trigger_event=data.trigger_event,
        is_active=data.is_active,
        created_by=current_user.id,
    )

    db.add(template)
    await db.flush()

    # Add variable definitions if provided
    if data.variable_definitions:
        for var_data in data.variable_definitions:
            variable = NotificationTemplateVariable(
                template_id=template.id,
                name=var_data.name,
                display_name=var_data.display_name,
                description=var_data.description,
                data_type=var_data.data_type,
                format_pattern=var_data.format_pattern,
                default_value=var_data.default_value,
                is_required=var_data.is_required,
                validation_regex=var_data.validation_regex,
                sample_value=var_data.sample_value,
                display_order=var_data.display_order,
                created_by=current_user.id,
            )
            db.add(variable)

    await db.commit()
    await db.refresh(template)

    return NotificationTemplateResponse.model_validate(template)


@router.put("/{template_id}", response_model=NotificationTemplateResponse)
async def update_template(
    template_id: UUID,
    data: NotificationTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a notification template."""
    result = await db.execute(
        select(SysNotificationTemplate).where(
            SysNotificationTemplate.id == template_id,
            SysNotificationTemplate.organization_id == current_user.organization_id,
        )
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)

    template.updated_by = current_user.id

    await db.commit()
    await db.refresh(template)

    return NotificationTemplateResponse.model_validate(template)


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete (soft) a notification template."""
    result = await db.execute(
        select(SysNotificationTemplate).where(
            SysNotificationTemplate.id == template_id,
            SysNotificationTemplate.organization_id == current_user.organization_id,
        )
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )

    template.soft_delete(current_user.id)
    await db.commit()


@router.post("/preview", response_model=TemplatePreviewResponse)
async def preview_template(
    data: TemplatePreviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Preview a notification template with sample data."""
    template = None

    if data.template_id:
        result = await db.execute(
            select(SysNotificationTemplate).where(
                SysNotificationTemplate.id == data.template_id,
            )
        )
        template = result.scalar_one_or_none()
    elif data.template_code:
        result = await db.execute(
            select(SysNotificationTemplate).where(
                SysNotificationTemplate.code == data.template_code,
                (
                    (SysNotificationTemplate.organization_id == current_user.organization_id) |
                    (SysNotificationTemplate.organization_id.is_(None))
                ),
            )
        )
        template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )

    # Get content based on channel
    channel = data.channel
    title = None
    subject = None
    body = ""
    html_body = None

    if channel == "email":
        subject = template.email_subject
        body = template.email_body_text or ""
        html_body = template.email_body_html
    elif channel == "sms":
        body = template.sms_body or ""
    elif channel == "push":
        title = template.push_title
        body = template.push_body or ""
    elif channel == "in_app":
        title = template.in_app_title
        body = template.in_app_message or ""

    # Find variables used
    variables_used = template.variables or []

    # Render with context
    context = data.context
    missing_variables = []

    for var in variables_used:
        if var not in context:
            missing_variables.append(var)
            # Use sample value if available
            if template.default_values and var in template.default_values:
                context[var] = template.default_values[var]
            else:
                context[var] = f"[{var}]"

    # Simple template rendering
    def render(text: str, ctx: dict) -> str:
        if not text:
            return ""
        result = text
        for key, value in ctx.items():
            placeholder = "{" + key + "}"
            result = result.replace(placeholder, str(value) if value else "")
        return result

    return TemplatePreviewResponse(
        channel=channel,
        title=render(title, context) if title else None,
        subject=render(subject, context) if subject else None,
        body=render(body, context),
        html_body=render(html_body, context) if html_body else None,
        variables_used=variables_used,
        missing_variables=missing_variables,
    )


# Template variables endpoints

@router.get("/{template_id}/variables", response_model=list[TemplateVariableResponse])
async def list_template_variables(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List variables for a template."""
    result = await db.execute(
        select(NotificationTemplateVariable)
        .where(NotificationTemplateVariable.template_id == template_id)
        .order_by(NotificationTemplateVariable.display_order)
    )
    variables = list(result.scalars().all())
    return [TemplateVariableResponse.model_validate(v) for v in variables]


@router.post("/{template_id}/variables", response_model=TemplateVariableResponse)
async def add_template_variable(
    template_id: UUID,
    data: TemplateVariableCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a variable to a template."""
    # Verify template exists and belongs to org
    result = await db.execute(
        select(SysNotificationTemplate).where(
            SysNotificationTemplate.id == template_id,
            SysNotificationTemplate.organization_id == current_user.organization_id,
        )
    )
    template = result.scalar_one_or_none()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found",
        )

    variable = NotificationTemplateVariable(
        template_id=template_id,
        name=data.name,
        display_name=data.display_name,
        description=data.description,
        data_type=data.data_type,
        format_pattern=data.format_pattern,
        default_value=data.default_value,
        is_required=data.is_required,
        validation_regex=data.validation_regex,
        sample_value=data.sample_value,
        display_order=data.display_order,
        created_by=current_user.id,
    )

    db.add(variable)
    await db.commit()
    await db.refresh(variable)

    return TemplateVariableResponse.model_validate(variable)


@router.delete("/{template_id}/variables/{variable_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template_variable(
    template_id: UUID,
    variable_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a template variable."""
    result = await db.execute(
        select(NotificationTemplateVariable).where(
            NotificationTemplateVariable.id == variable_id,
            NotificationTemplateVariable.template_id == template_id,
        )
    )
    variable = result.scalar_one_or_none()

    if not variable:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Variable not found",
        )

    await db.delete(variable)
    await db.commit()
