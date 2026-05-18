"""Approval-checklist template service.

CRUD over ``mst_approval_checklist_template`` + child
``mst_approval_checklist_item`` rows.

Tenant rule (same as ``SubventionSchemeService``):
- Reads return platform rows (organization_id IS NULL) AND the caller's
  tenant-owned rows.
- Writes only target the caller's own tenant — platform-default rows
  are read-only at runtime (managed via migrations).
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from app.models.auth.user import User
from app.models.lending.checklist.template import (
    ApprovalChecklistTemplate,
    ApprovalChecklistTemplateItem,
)
from app.models.lending.enums import (
    ChecklistAppliesTo,
    ChecklistItemCategory,
)
from app.schemas.lending.approval_checklist import (
    ChecklistTemplateCreate,
    ChecklistTemplateItemCreate,
    ChecklistTemplateItemUpdate,
    ChecklistTemplateUpdate,
)

_VALID_APPLIES_TO = {e.value for e in ChecklistAppliesTo}
_VALID_CATEGORIES = {e.value for e in ChecklistItemCategory}


class ChecklistTemplateService:
    """Service for checklist-template + template-item CRUD."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # =========================================================================
    # Templates — CRUD
    # =========================================================================

    async def create_template(
        self,
        data: ChecklistTemplateCreate,
        current_user: User,
    ) -> ApprovalChecklistTemplate:
        if current_user.organization_id is None:
            raise BadRequestException(
                "Current user has no organization context",
                error_code="MISSING_ORG_CONTEXT",
            )
        if data.applies_to not in _VALID_APPLIES_TO:
            raise BadRequestException(
                f"applies_to must be one of {sorted(_VALID_APPLIES_TO)}",
                error_code="INVALID_APPLIES_TO",
            )

        # Per-org uniqueness on (code, organization_id).
        existing = await self.session.execute(
            select(ApprovalChecklistTemplate).where(
                ApprovalChecklistTemplate.organization_id == current_user.organization_id,
                ApprovalChecklistTemplate.code == data.code,
                ApprovalChecklistTemplate.deleted_at.is_(None),
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise ConflictException(
                f"Template with code '{data.code}' already exists",
                error_code="TEMPLATE_CODE_EXISTS",
            )

        for item in data.items:
            if item.category not in _VALID_CATEGORIES:
                raise BadRequestException(
                    f"Item '{item.code}': category must be one of " f"{sorted(_VALID_CATEGORIES)}",
                    error_code="INVALID_ITEM_CATEGORY",
                )

        template = ApprovalChecklistTemplate(
            organization_id=current_user.organization_id,
            code=data.code,
            name=data.name,
            description=data.description,
            applies_to=data.applies_to,
            is_default=data.is_default,
            created_by=current_user.id,
        )
        self.session.add(template)
        await self.session.flush()

        # Enforce "at most one default per org" at write time.
        if data.is_default:
            await self._unset_other_defaults(current_user.organization_id, template.id)

        for item_data in data.items:
            item = ApprovalChecklistTemplateItem(
                template_id=template.id,
                code=item_data.code,
                label=item_data.label,
                description=item_data.description,
                category=item_data.category,
                is_mandatory=item_data.is_mandatory,
                sort_order=item_data.sort_order,
                default_due_offset_days=item_data.default_due_offset_days,
                requires_evidence=item_data.requires_evidence,
                created_by=current_user.id,
            )
            self.session.add(item)

        await self.session.flush()
        await self.session.refresh(template, attribute_names=["items"])
        return template

    async def update_template(
        self,
        organization_id: UUID,
        template_id: UUID,
        data: ChecklistTemplateUpdate,
        current_user: User,
    ) -> ApprovalChecklistTemplate:
        template = await self.get_template_with_items(organization_id, template_id)
        if template.organization_id is None:
            raise BadRequestException(
                "Platform-default templates are read-only",
                error_code="READONLY_PLATFORM_TEMPLATE",
            )
        if data.applies_to is not None and data.applies_to not in _VALID_APPLIES_TO:
            raise BadRequestException(
                f"applies_to must be one of {sorted(_VALID_APPLIES_TO)}",
                error_code="INVALID_APPLIES_TO",
            )

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(template, field, value)
        template.updated_by = current_user.id
        template.version = (template.version or 1) + 1

        await self.session.flush()
        if data.is_default is True:
            await self._unset_other_defaults(organization_id, template.id)
        await self.session.refresh(template, attribute_names=["items"])
        return template

    async def delete_template(
        self,
        organization_id: UUID,
        template_id: UUID,
        current_user: User,
    ) -> None:
        template = await self.get_template_with_items(organization_id, template_id)
        if template.organization_id is None:
            raise BadRequestException(
                "Platform-default templates cannot be deleted",
                error_code="READONLY_PLATFORM_TEMPLATE",
            )
        template.soft_delete(deleted_by=current_user.id)
        await self.session.flush()

    async def list_templates(
        self,
        organization_id: UUID,
        applies_to: str | None = None,
        include_inactive: bool = False,
    ) -> list[ApprovalChecklistTemplate]:
        where = [
            or_(
                ApprovalChecklistTemplate.organization_id.is_(None),
                ApprovalChecklistTemplate.organization_id == organization_id,
            ),
            ApprovalChecklistTemplate.deleted_at.is_(None),
        ]
        if not include_inactive:
            where.append(ApprovalChecklistTemplate.is_active.is_(True))
        if applies_to is not None:
            where.append(ApprovalChecklistTemplate.applies_to == applies_to)

        stmt = (
            select(ApprovalChecklistTemplate)
            .options(
                selectinload(ApprovalChecklistTemplate.items),
            )
            .where(*where)
            .order_by(
                # Tenant rows before platform rows; then by code.
                ApprovalChecklistTemplate.organization_id.is_(None).asc(),
                ApprovalChecklistTemplate.code.asc(),
            )
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def get_template_with_items(
        self,
        organization_id: UUID,
        template_id: UUID,
    ) -> ApprovalChecklistTemplate:
        stmt = (
            select(ApprovalChecklistTemplate)
            .options(selectinload(ApprovalChecklistTemplate.items))
            .where(ApprovalChecklistTemplate.id == template_id)
        )
        template = (await self.session.execute(stmt)).scalar_one_or_none()
        if template is None or template.deleted_at is not None:
            raise NotFoundException(
                "Checklist template not found",
                error_code="CHECKLIST_TEMPLATE_NOT_FOUND",
            )
        if template.organization_id is not None and template.organization_id != organization_id:
            raise NotFoundException(
                "Checklist template not found",
                error_code="CHECKLIST_TEMPLATE_NOT_FOUND",
            )
        return template

    async def get_default_template(
        self,
        organization_id: UUID,
        applies_to: str = ChecklistAppliesTo.LOAN_APPLICATION.value,
    ) -> ApprovalChecklistTemplate | None:
        """Return the default template — tenant override beats platform."""
        stmt = (
            select(ApprovalChecklistTemplate)
            .options(selectinload(ApprovalChecklistTemplate.items))
            .where(
                ApprovalChecklistTemplate.deleted_at.is_(None),
                ApprovalChecklistTemplate.is_active.is_(True),
                ApprovalChecklistTemplate.is_default.is_(True),
                ApprovalChecklistTemplate.applies_to == applies_to,
                or_(
                    ApprovalChecklistTemplate.organization_id.is_(None),
                    ApprovalChecklistTemplate.organization_id == organization_id,
                ),
            )
            .order_by(
                ApprovalChecklistTemplate.organization_id.is_(None).asc(),
            )
            .limit(1)
        )
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def set_default_template(
        self,
        organization_id: UUID,
        template_id: UUID,
        current_user: User,
    ) -> ApprovalChecklistTemplate:
        template = await self.get_template_with_items(organization_id, template_id)
        if template.organization_id is None:
            raise BadRequestException(
                "Cannot toggle is_default on a platform template",
                error_code="READONLY_PLATFORM_TEMPLATE",
            )
        template.is_default = True
        template.updated_by = current_user.id
        template.version = (template.version or 1) + 1
        await self.session.flush()
        await self._unset_other_defaults(organization_id, template.id)
        await self.session.refresh(template, attribute_names=["items"])
        return template

    # =========================================================================
    # Items — CRUD
    # =========================================================================

    async def add_item(
        self,
        organization_id: UUID,
        template_id: UUID,
        data: ChecklistTemplateItemCreate,
        current_user: User,
    ) -> ApprovalChecklistTemplateItem:
        template = await self.get_template_with_items(organization_id, template_id)
        if template.organization_id is None:
            raise BadRequestException(
                "Cannot add items to a platform template",
                error_code="READONLY_PLATFORM_TEMPLATE",
            )
        if data.category not in _VALID_CATEGORIES:
            raise BadRequestException(
                f"category must be one of {sorted(_VALID_CATEGORIES)}",
                error_code="INVALID_ITEM_CATEGORY",
            )
        # Code uniqueness within the template.
        for existing in template.items:
            if existing.deleted_at is None and existing.code == data.code:
                raise ConflictException(
                    f"Item with code '{data.code}' already exists",
                    error_code="TEMPLATE_ITEM_CODE_EXISTS",
                )

        item = ApprovalChecklistTemplateItem(
            template_id=template_id,
            code=data.code,
            label=data.label,
            description=data.description,
            category=data.category,
            is_mandatory=data.is_mandatory,
            sort_order=data.sort_order,
            default_due_offset_days=data.default_due_offset_days,
            requires_evidence=data.requires_evidence,
            created_by=current_user.id,
        )
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(item)
        return item

    async def update_item(
        self,
        organization_id: UUID,
        template_id: UUID,
        item_id: UUID,
        data: ChecklistTemplateItemUpdate,
        current_user: User,
    ) -> ApprovalChecklistTemplateItem:
        item = await self._get_template_item(organization_id, template_id, item_id)
        if data.category is not None and data.category not in _VALID_CATEGORIES:
            raise BadRequestException(
                f"category must be one of {sorted(_VALID_CATEGORIES)}",
                error_code="INVALID_ITEM_CATEGORY",
            )
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        item.updated_by = current_user.id
        item.version = (item.version or 1) + 1
        await self.session.flush()
        await self.session.refresh(item)
        return item

    async def delete_item(
        self,
        organization_id: UUID,
        template_id: UUID,
        item_id: UUID,
        current_user: User,
    ) -> None:
        item = await self._get_template_item(organization_id, template_id, item_id)
        item.soft_delete(deleted_by=current_user.id)
        await self.session.flush()

    # =========================================================================
    # Helpers
    # =========================================================================

    async def _get_template_item(
        self,
        organization_id: UUID,
        template_id: UUID,
        item_id: UUID,
    ) -> ApprovalChecklistTemplateItem:
        template = await self.get_template_with_items(organization_id, template_id)
        if template.organization_id is None:
            raise BadRequestException(
                "Cannot modify items on a platform template",
                error_code="READONLY_PLATFORM_TEMPLATE",
            )
        item = await self.session.get(ApprovalChecklistTemplateItem, item_id)
        if item is None or item.deleted_at is not None or item.template_id != template_id:
            raise NotFoundException(
                "Template item not found",
                error_code="TEMPLATE_ITEM_NOT_FOUND",
            )
        return item

    async def _unset_other_defaults(
        self,
        organization_id: UUID,
        keep_id: UUID,
    ) -> None:
        """Within one org, only one template per applies_to is default."""
        stmt = (
            update(ApprovalChecklistTemplate)
            .where(
                ApprovalChecklistTemplate.organization_id == organization_id,
                ApprovalChecklistTemplate.id != keep_id,
                ApprovalChecklistTemplate.is_default.is_(True),
                ApprovalChecklistTemplate.deleted_at.is_(None),
            )
            .values(is_default=False)
        )
        await self.session.execute(stmt)
