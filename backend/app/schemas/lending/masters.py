"""Schemas for the 21 lending master tables — camelCase wire."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import CamelSchema

# ---------------------------------------------------------------------------
# Reusable base for list responses
# ---------------------------------------------------------------------------


class _ListResponse(CamelSchema):
    total: int
    items: list[Any]


# ---------------------------------------------------------------------------
# Asset class
# ---------------------------------------------------------------------------


class AssetClassResponse(CamelSchema):
    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    details_schema: dict[str, Any] = Field(default_factory=dict)
    valuation_required: bool
    valuation_frequency_months: int
    insurance_required: bool
    mandatory_insurance_types: list[str] = Field(default_factory=list)
    registration_authority_code: Optional[str] = None
    default_provisioning_band: Optional[str] = None
    is_system: bool
    sort_order: int


class AssetClassCreate(CamelSchema):
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    details_schema: dict[str, Any] = Field(default_factory=dict)
    valuation_required: bool = True
    valuation_frequency_months: int = 12
    insurance_required: bool = True
    mandatory_insurance_types: list[str] = Field(default_factory=list)
    registration_authority_code: Optional[str] = None
    default_provisioning_band: Optional[str] = None
    sort_order: int = 0


class AssetClassUpdate(CamelSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    details_schema: Optional[dict[str, Any]] = None
    valuation_required: Optional[bool] = None
    valuation_frequency_months: Optional[int] = None
    insurance_required: Optional[bool] = None
    mandatory_insurance_types: Optional[list[str]] = None
    registration_authority_code: Optional[str] = None
    default_provisioning_band: Optional[str] = None
    sort_order: Optional[int] = None


class AssetClassListResponse(_ListResponse):
    items: list[AssetClassResponse]


# ---------------------------------------------------------------------------
# Lifecycle event catalog
# ---------------------------------------------------------------------------


class LifecycleEventCatalogResponse(CamelSchema):
    id: UUID
    code: str
    label: str
    description: Optional[str] = None
    phase: Optional[str] = None
    icon: Optional[str] = None
    is_borrower_visible_default: bool
    regulatory_tags: list[str]
    is_system: bool


class LifecycleEventCatalogListResponse(_ListResponse):
    items: list[LifecycleEventCatalogResponse]


# ---------------------------------------------------------------------------
# NPA bucket
# ---------------------------------------------------------------------------


class NpaBucketResponse(CamelSchema):
    id: UUID
    code: str
    label: str
    asset_classification: str
    min_dpd: int
    max_dpd: Optional[int] = None
    sort_order: int
    effective_from: date
    effective_to: Optional[date] = None
    loan_segment: Optional[str] = None
    is_system: bool


class NpaBucketCreate(CamelSchema):
    code: str
    label: str
    asset_classification: str
    min_dpd: int = Field(..., ge=0)
    max_dpd: Optional[int] = Field(default=None, ge=0)
    sort_order: int = 0
    effective_from: date
    effective_to: Optional[date] = None
    loan_segment: Optional[str] = None


class NpaBucketUpdate(CamelSchema):
    label: Optional[str] = None
    asset_classification: Optional[str] = None
    min_dpd: Optional[int] = None
    max_dpd: Optional[int] = None
    sort_order: Optional[int] = None
    effective_to: Optional[date] = None


class NpaBucketListResponse(_ListResponse):
    items: list[NpaBucketResponse]


# ---------------------------------------------------------------------------
# Provisioning rate
# ---------------------------------------------------------------------------


class ProvisioningRateResponse(CamelSchema):
    id: UUID
    asset_classification: str
    secured_unsecured: str
    loan_segment: str
    rate_percent: Decimal
    nbfc_layer: Optional[str] = None
    effective_from: date
    effective_to: Optional[date] = None
    is_system: bool
    notes: Optional[str] = None


class ProvisioningRateCreate(CamelSchema):
    asset_classification: str
    secured_unsecured: str
    loan_segment: str = "DEFAULT"
    rate_percent: Decimal = Field(..., ge=0, le=100)
    nbfc_layer: Optional[str] = None
    effective_from: date
    effective_to: Optional[date] = None
    notes: Optional[str] = None


class ProvisioningRateUpdate(CamelSchema):
    rate_percent: Optional[Decimal] = None
    effective_to: Optional[date] = None
    notes: Optional[str] = None


class ProvisioningRateListResponse(_ListResponse):
    items: list[ProvisioningRateResponse]


# ---------------------------------------------------------------------------
# Fee type
# ---------------------------------------------------------------------------


class FeeTypeResponse(CamelSchema):
    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    is_gst_applicable: bool
    gst_rate_percent: Decimal
    is_refundable: bool
    is_charged_to_borrower: bool
    collection_stage: Optional[str] = None
    is_system: bool


class FeeTypeCreate(CamelSchema):
    code: str
    name: str
    description: Optional[str] = None
    is_gst_applicable: bool = False
    gst_rate_percent: Decimal = Decimal("18")
    is_refundable: bool = False
    is_charged_to_borrower: bool = True
    collection_stage: Optional[str] = None


class FeeTypeUpdate(CamelSchema):
    name: Optional[str] = None
    description: Optional[str] = None
    is_gst_applicable: Optional[bool] = None
    gst_rate_percent: Optional[Decimal] = None
    is_refundable: Optional[bool] = None
    is_charged_to_borrower: Optional[bool] = None
    collection_stage: Optional[str] = None


class FeeTypeListResponse(_ListResponse):
    items: list[FeeTypeResponse]


# ---------------------------------------------------------------------------
# Document template
# ---------------------------------------------------------------------------


class DocumentTemplateResponse(CamelSchema):
    id: UUID
    code: str
    name: str
    body: str
    body_format: str
    merge_fields_schema: dict[str, Any] = Field(default_factory=dict)
    locale: str
    template_version: int
    is_current: bool
    is_system: bool


class DocumentTemplateCreate(CamelSchema):
    code: str
    name: str
    body: str
    body_format: str = "MARKDOWN"
    merge_fields_schema: dict[str, Any] = Field(default_factory=dict)
    locale: str = "en"


class DocumentTemplateUpdate(CamelSchema):
    name: Optional[str] = None
    body: Optional[str] = None
    body_format: Optional[str] = None
    merge_fields_schema: Optional[dict[str, Any]] = None


class DocumentTemplateListResponse(_ListResponse):
    items: list[DocumentTemplateResponse]


# ---------------------------------------------------------------------------
# Communication template
# ---------------------------------------------------------------------------


class CommunicationTemplateResponse(CamelSchema):
    id: UUID
    event_code: str
    channel: str
    locale: str
    template_version: int
    is_current: bool
    subject: Optional[str] = None
    body: str
    requires_opt_in: bool
    is_system: bool


class CommunicationTemplateCreate(CamelSchema):
    event_code: str
    channel: str
    locale: str = "en"
    subject: Optional[str] = None
    body: str
    requires_opt_in: bool = False


class CommunicationTemplateUpdate(CamelSchema):
    subject: Optional[str] = None
    body: Optional[str] = None
    requires_opt_in: Optional[bool] = None


class CommunicationTemplateListResponse(_ListResponse):
    items: list[CommunicationTemplateResponse]


# ---------------------------------------------------------------------------
# Checklist item catalog
# ---------------------------------------------------------------------------


class ChecklistItemResponse(CamelSchema):
    id: UUID
    code: str
    label: str
    description: Optional[str] = None
    category: str
    stage: str
    is_mandatory_default: bool
    expiry_days: Optional[int] = None
    is_system: bool


class ChecklistItemCreate(CamelSchema):
    code: str
    label: str
    description: Optional[str] = None
    category: str
    stage: str = "APPLICATION"
    is_mandatory_default: bool = True
    expiry_days: Optional[int] = None


class ChecklistItemUpdate(CamelSchema):
    label: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    stage: Optional[str] = None
    is_mandatory_default: Optional[bool] = None
    expiry_days: Optional[int] = None


class ChecklistItemListResponse(_ListResponse):
    items: list[ChecklistItemResponse]


# ---------------------------------------------------------------------------
# Canonical SSOT master API
# ---------------------------------------------------------------------------


class MasterFieldDescriptor(CamelSchema):
    key: str
    label: str
    data_type: str
    required: bool = False
    editable: bool = True
    system: bool = False


class MasterCatalogItem(CamelSchema):
    key: str
    label: str
    description: str
    group: str
    source_table: str
    source_of_truth: str
    consumer_screens: list[str] = Field(default_factory=list)
    seed_source: str
    fields: list[MasterFieldDescriptor] = Field(default_factory=list)


class MasterCatalogResponse(CamelSchema):
    items: list[MasterCatalogItem]


class MasterRowResponse(CamelSchema):
    id: UUID
    data: dict[str, Any]


class MasterRowListResponse(CamelSchema):
    key: str
    items: list[MasterRowResponse]
    total: int
    page: int
    page_size: int


class MasterRowMutation(CamelSchema):
    data: dict[str, Any]


class LendingOptionResponse(CamelSchema):
    id: UUID
    option_group: str
    code: str
    label: str
    description: Optional[str] = None
    sort_order: int
    is_system: bool


class LendingOptionListResponse(CamelSchema):
    items: list[LendingOptionResponse]
    total: int
