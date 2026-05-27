"""Approval-checklist schemas.

Wire format is camelCase per ``CamelSchema`` (CLAUDE.md §5.4). Routes
serving these models MUST set ``response_model_by_alias=True``.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import Field, model_validator

from app.schemas.base import CamelSchema

# =============================================================================
# Template Master
# =============================================================================


class ChecklistTemplateItemCreate(CamelSchema):
    """Payload for creating a new template item."""

    catalog_item_id: UUID
    is_mandatory: bool = False
    sort_order: int = 0
    default_due_offset_days: int | None = Field(None, ge=0)
    requires_evidence: bool = False


class ChecklistTemplateItemUpdate(CamelSchema):
    """Partial update for a template item."""

    catalog_item_id: UUID | None = None
    is_mandatory: bool | None = None
    sort_order: int | None = None
    default_due_offset_days: int | None = Field(None, ge=0)
    requires_evidence: bool | None = None
    is_active: bool | None = None


class ChecklistTemplateItemResponse(CamelSchema):
    """Response for one template item."""

    id: UUID
    template_id: UUID
    catalog_item_id: UUID
    code: str
    label: str
    description: str | None = None
    category: str
    is_mandatory: bool
    sort_order: int
    default_due_offset_days: int | None = None
    requires_evidence: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None
    version: int


class ChecklistTemplateCreate(CamelSchema):
    """Payload for creating a new checklist template."""

    code: str = Field(..., max_length=50, min_length=1)
    name: str = Field(..., max_length=200, min_length=1)
    description: str | None = Field(None, max_length=500)
    applies_to: str = Field(default="LOAN_APPLICATION", max_length=50)
    is_default: bool = False
    items: list[ChecklistTemplateItemCreate] = Field(default_factory=list)


class ChecklistTemplateUpdate(CamelSchema):
    """Partial update for a template (does not touch items)."""

    name: str | None = Field(None, max_length=200, min_length=1)
    description: str | None = Field(None, max_length=500)
    applies_to: str | None = Field(None, max_length=50)
    is_default: bool | None = None
    is_active: bool | None = None


class ChecklistTemplateResponse(CamelSchema):
    """Detail / list response for a template (includes items)."""

    id: UUID
    organization_id: UUID | None = None
    code: str
    name: str
    description: str | None = None
    applies_to: str
    is_default: bool
    items: list[ChecklistTemplateItemResponse] = Field(default_factory=list)
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None
    version: int

    @model_validator(mode="before")
    @classmethod
    def _from_orm(cls, obj: Any) -> Any:
        if isinstance(obj, dict):
            return obj
        items = getattr(obj, "items", None) or []
        live_items = [i for i in items if getattr(i, "deleted_at", None) is None]
        return {
            "id": obj.id,
            "organization_id": obj.organization_id,
            "code": obj.code,
            "name": obj.name,
            "description": obj.description,
            "applies_to": obj.applies_to,
            "is_default": obj.is_default,
            "items": [ChecklistTemplateItemResponse.model_validate(i) for i in live_items],
            "is_active": obj.is_active,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
            "version": obj.version,
        }


class ChecklistTemplateListResponse(CamelSchema):
    """List wrapper (templates rarely paginate — return all)."""

    items: list[ChecklistTemplateResponse]


# =============================================================================
# Loan Checklist (per-application live state)
# =============================================================================


class LoanChecklistItemUpdate(CamelSchema):
    """Partial update for a loan-checklist item.

    Status transitions: PENDING → IN_PROGRESS → MET / WAIVED /
    NOT_APPLICABLE. Service-layer validates evidence + waiver-reason
    requirements; this schema is intentionally permissive.
    """

    status: str | None = Field(None, max_length=20)
    notes: str | None = Field(None, max_length=1000)
    due_date: date | None = None
    evidence_document_path: str | None = Field(None, max_length=1000)
    waiver_reason: str | None = Field(None, max_length=500)


class LoanChecklistItemResponse(CamelSchema):
    """Response for one loan-checklist item."""

    id: UUID
    checklist_id: UUID
    template_item_id: UUID | None = None
    catalog_item_id: UUID | None = None
    code: str
    label: str
    description: str | None = None
    category: str
    is_mandatory: bool
    sort_order: int
    requires_evidence: bool
    status: str
    met_at: datetime | None = None
    met_by: UUID | None = None
    waived_at: datetime | None = None
    waived_by: UUID | None = None
    waiver_reason: str | None = None
    evidence_document_path: str | None = None
    evidence_uploaded_at: datetime | None = None
    due_date: date | None = None
    notes: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None
    version: int


class LoanChecklistResponse(CamelSchema):
    """Full checklist response for an application.

    Includes an aggregate ``mandatoryPending`` (count of mandatory items
    still in PENDING / IN_PROGRESS) so the UI gate decision is one read.
    """

    id: UUID
    organization_id: UUID
    application_id: UUID
    template_id: UUID | None = None
    name: str
    items: list[LoanChecklistItemResponse] = Field(default_factory=list)
    mandatory_pending: int = 0
    is_active: bool
    created_at: datetime
    updated_at: datetime | None = None
    version: int

    @model_validator(mode="before")
    @classmethod
    def _from_orm(cls, obj: Any) -> Any:
        if isinstance(obj, dict):
            return obj
        raw_items = getattr(obj, "items", None) or []
        live_items = [i for i in raw_items if getattr(i, "deleted_at", None) is None]
        pending_states = {"PENDING", "IN_PROGRESS"}
        mandatory_pending = sum(
            1 for i in live_items if i.is_mandatory and i.status in pending_states
        )
        return {
            "id": obj.id,
            "organization_id": obj.organization_id,
            "application_id": obj.application_id,
            "template_id": obj.template_id,
            "name": obj.name,
            "items": [LoanChecklistItemResponse.model_validate(i) for i in live_items],
            "mandatory_pending": mandatory_pending,
            "is_active": obj.is_active,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
            "version": obj.version,
        }


# =============================================================================
# Action payloads
# =============================================================================


class ApplyTemplateRequest(CamelSchema):
    """Payload for applying / replacing a template on a loan application."""

    template_id: UUID
    # Anchor against which default_due_offset_days is resolved. If not
    # provided, the service uses today (UTC).
    due_date_anchor: date | None = None


class MarkMetRequest(CamelSchema):
    """Payload for marking a checklist item as MET."""

    evidence_document_path: str | None = Field(None, max_length=1000)
    notes: str | None = Field(None, max_length=1000)


class WaiveRequest(CamelSchema):
    """Payload for waiving a checklist item — reason is required."""

    waiver_reason: str = Field(..., max_length=500, min_length=5)


class MarkNotApplicableRequest(CamelSchema):
    """Payload for marking a checklist item as NOT_APPLICABLE."""

    notes: str | None = Field(None, max_length=1000)
