"""Canonical lending, treasury and borrowing master-data SSOT endpoints.

The public API intentionally exposes one route family only:

* ``GET /lending/masters/catalog``
* ``GET /lending/masters/{master_key}/rows``
* ``POST /lending/masters/{master_key}/rows``
* ``PUT /lending/masters/{master_key}/rows/{row_id}``
* ``DELETE /lending/masters/{master_key}/rows/{row_id}``

Every row payload is camelCase. Python/SQLAlchemy internals stay snake_case.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy import func, inspect as sa_inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import RequirePermissions, get_current_user, get_db_with_tenant
from app.core.exceptions import BadRequestException, NotFoundException
from app.models.lending.masters import (
    ApprovalMatrix,
    AssetClass,
    ChargeTriggerRule,
    ChecklistItemCatalog,
    ClassificationOverridePolicy,
    CommunicationTemplate,
    DayCountConvention,
    DocumentTemplate,
    FeeGlMapping,
    FeeType,
    InsuranceType,
    LendingOption,
    LifecycleEventCatalog,
    NachReturnReason,
    NpaBucket,
    PenalChargePolicy,
    ProvisioningRate,
    RateResetBenchmark,
    RecoveryAgent,
    RegistrationAuthority,
    SLAMatrix,
    WilfulDefaulterCommittee,
)
from app.schemas.base import MessageResponse
from app.schemas.lending.approval_checklist import (
    ChecklistTemplateCreate,
    ChecklistTemplateItemCreate,
    ChecklistTemplateItemResponse,
    ChecklistTemplateItemUpdate,
    ChecklistTemplateListResponse,
    ChecklistTemplateResponse,
    ChecklistTemplateUpdate,
)
from app.schemas.lending.masters import (
    MasterCatalogItem,
    MasterCatalogResponse,
    MasterFieldDescriptor,
    MasterRowListResponse,
    MasterRowMutation,
    MasterRowResponse,
)
from app.services.lending.checklist import ChecklistTemplateService

router = APIRouter()

_READ_PERM = "LENDING_MASTER_READ"
_WRITE_PERM = "LENDING_MASTER_WRITE"


@dataclass(frozen=True)
class MasterDefinition:
    key: str
    label: str
    description: str
    group: str
    model: Any
    order_by: str
    source_of_truth: str
    consumer_screens: tuple[str, ...]
    seed_source: str = "backend/app/db/seeds/lending_masters.py"


MASTER_DEFINITIONS: dict[str, MasterDefinition] = {
    "asset-classes": MasterDefinition(
        "asset-classes",
        "Asset Classes",
        "Lending asset classes and collateral behavior.",
        "Lending Setup",
        AssetClass,
        "sort_order",
        "mst_asset_class",
        ("/admin/lending/products", "/admin/lending/applications", "/admin/lending/collaterals"),
    ),
    "checklist-catalog": MasterDefinition(
        "checklist-catalog",
        "Checklist Item Catalog",
        "Reusable checklist/document/control definitions used by products and approval templates.",
        "Checklist SSOT",
        ChecklistItemCatalog,
        "code",
        "mst_checklist_item_catalog",
        (
            "/admin/lending/products",
            "/admin/lending/masters/approval-checklist-templates",
            "/portal/applications/new",
        ),
    ),
    "approval-matrix": MasterDefinition(
        "approval-matrix",
        "Approval Matrix",
        "Amount-band, action and authority role setup.",
        "Workflow Controls",
        ApprovalMatrix,
        "band_min",
        "mst_approval_matrix",
        ("/admin/lending/sanctions", "/admin/lending/disbursements"),
    ),
    "charge-trigger-rules": MasterDefinition(
        "charge-trigger-rules",
        "Charge Trigger Rules",
        "Event-driven charge rules for bounced receipts, statements, rate switches and similar events.",
        "Charges",
        ChargeTriggerRule,
        "trigger_event_code",
        "mst_charge_trigger_rule",
        ("/admin/lending/receipts", "/admin/lending/closure-cockpit"),
    ),
    "classification-override-policies": MasterDefinition(
        "classification-override-policies",
        "Classification Override Policies",
        "Policy-controlled exceptions to asset classification logic.",
        "Risk Controls",
        ClassificationOverridePolicy,
        "code",
        "mst_classification_override_policy",
        ("/admin/lending/collections/npa", "/admin/lending/risk-cockpit"),
    ),
    "communication-templates": MasterDefinition(
        "communication-templates",
        "Communication Templates",
        "Borrower-facing SMS/email template bodies for lifecycle events.",
        "Documents & Communication",
        CommunicationTemplate,
        "event_code",
        "mst_communication_template",
        ("/admin/notifications/templates", "/portal/applications", "/portal/loans"),
    ),
    "day-count-conventions": MasterDefinition(
        "day-count-conventions",
        "Day Count Conventions",
        "Interest day-count bases used in lending and borrowing schedules.",
        "Rate & Schedule Setup",
        DayCountConvention,
        "code",
        "mst_day_count_convention",
        ("/admin/lending/products", "/admin/treasury/borrowings"),
    ),
    "document-templates": MasterDefinition(
        "document-templates",
        "Document Templates",
        "KFS, sanction letters, certificates, notices and statement templates.",
        "Documents & Communication",
        DocumentTemplate,
        "code",
        "mst_document_template",
        ("/admin/lending/sanctions", "/portal/loans", "/portal/claims"),
    ),
    "fee-gl-mappings": MasterDefinition(
        "fee-gl-mappings",
        "Fee GL Mappings",
        "GL mapping for fee income, receivable and GST posting.",
        "Accounting Bridge",
        FeeGlMapping,
        "fee_type_code",
        "mst_fee_gl_mapping",
        ("/admin/lending/receipts", "/admin/finance/vouchers"),
    ),
    "fee-types": MasterDefinition(
        "fee-types",
        "Fee Types",
        "Operator-defined fee and charge categories.",
        "Charges",
        FeeType,
        "code",
        "mst_fee_type",
        ("/admin/lending/products", "/admin/lending/receipts"),
    ),
    "insurance-types": MasterDefinition(
        "insurance-types",
        "Insurance Types",
        "Insurance categories required for collateral and document checks.",
        "Collateral Setup",
        InsuranceType,
        "code",
        "mst_insurance_type",
        ("/admin/lending/collaterals", "/admin/lending/products"),
    ),
    "lending-options": MasterDefinition(
        "lending-options",
        "Lending & Treasury Options",
        "Governed option sets for lender type, borrowing type, frequencies, security types and ratings.",
        "Shared Options",
        LendingOption,
        "option_group",
        "mst_lending_option",
        ("/admin/treasury/lenders", "/admin/treasury/borrowings", "/admin/lending/products"),
    ),
    "lifecycle-event-catalog": MasterDefinition(
        "lifecycle-event-catalog",
        "Lifecycle Event Catalog",
        "Labels and borrower visibility defaults for lifecycle events.",
        "Lifecycle",
        LifecycleEventCatalog,
        "code",
        "mst_lifecycle_event_catalog",
        ("/admin/lending/applications", "/admin/lending/accounts", "/portal/loans"),
    ),
    "nach-return-reasons": MasterDefinition(
        "nach-return-reasons",
        "NACH Return Reasons",
        "NPCI return/bounce reason master.",
        "Collections",
        NachReturnReason,
        "code",
        "mst_nach_return_reason",
        ("/admin/lending/nach", "/admin/lending/receipts"),
    ),
    "npa-buckets": MasterDefinition(
        "npa-buckets",
        "NPA Buckets",
        "DPD ranges and asset-classification buckets.",
        "Risk Controls",
        NpaBucket,
        "min_dpd",
        "mst_npa_bucket",
        ("/admin/lending/collections/npa", "/admin/lending/reports"),
    ),
    "penal-charge-policies": MasterDefinition(
        "penal-charge-policies",
        "Penal Charge Policies",
        "RBI-compliant penal charge policies.",
        "Charges",
        PenalChargePolicy,
        "code",
        "mst_penal_charge_policy",
        ("/admin/lending/receipts", "/admin/lending/collections/followups"),
    ),
    "provisioning-rates": MasterDefinition(
        "provisioning-rates",
        "Provisioning Rates",
        "Provisioning rates by classification, segment and secured/unsecured status.",
        "Risk Controls",
        ProvisioningRate,
        "asset_classification",
        "mst_provisioning_rate",
        ("/admin/lending/collections/npa", "/admin/reports/regulatory"),
    ),
    "rate-reset-benchmarks": MasterDefinition(
        "rate-reset-benchmarks",
        "Rate Reset Benchmarks",
        "Repo, MCLR, T-Bill and internal cost-of-funds benchmarks.",
        "Rate & Schedule Setup",
        RateResetBenchmark,
        "code",
        "mst_rate_reset_benchmark",
        ("/admin/lending/products", "/admin/treasury/borrowings"),
    ),
    "recovery-agents": MasterDefinition(
        "recovery-agents",
        "Recovery Agents",
        "Empanelled recovery agents and compliance controls.",
        "Collections",
        RecoveryAgent,
        "agent_code",
        "mst_recovery_agent",
        ("/admin/lending/collections/followups", "/admin/lending/collections/legal"),
    ),
    "registration-authorities": MasterDefinition(
        "registration-authorities",
        "Registration Authorities",
        "CERSAI, ROC, NeSL, DG Shipping and similar charge/security registries.",
        "Collateral Setup",
        RegistrationAuthority,
        "code",
        "mst_registration_authority",
        ("/admin/lending/collaterals", "/admin/lending/charges"),
    ),
    "sla-matrix": MasterDefinition(
        "sla-matrix",
        "SLA Matrix",
        "Stage/action TATs and escalation setup.",
        "Workflow Controls",
        SLAMatrix,
        "stage",
        "mst_sla_matrix",
        ("/admin/lending/applications", "/admin/workflow/tasks"),
    ),
    "wilful-defaulter-committees": MasterDefinition(
        "wilful-defaulter-committees",
        "Wilful Defaulter Committees",
        "Identification and review committee composition.",
        "Risk Controls",
        WilfulDefaulterCommittee,
        "committee_type",
        "mst_wilful_defaulter_committee",
        ("/admin/lending/collections/legal", "/admin/lending/collections/npa"),
    ),
}

_RESERVED_FIELDS = {
    "id",
    "organization_id",
    "created_at",
    "created_by",
    "updated_at",
    "updated_by",
    "deleted_at",
    "deleted_by",
    "version",
}

_READONLY_FIELDS = _RESERVED_FIELDS | {"is_system"}


def _snake_to_camel(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(part[:1].upper() + part[1:] for part in tail)


def _camel_to_snake(value: str) -> str:
    chars: list[str] = []
    for char in value:
        if char.isupper():
            chars.append("_")
            chars.append(char.lower())
        else:
            chars.append(char)
    return "".join(chars).lstrip("_")


def _definition(master_key: str) -> MasterDefinition:
    definition = MASTER_DEFINITIONS.get(master_key)
    if definition is None:
        raise NotFoundException(
            detail=f"Unknown lending master: {master_key}",
            error_code="LENDING_MASTER_NOT_FOUND",
        )
    return definition


def _require_idempotency_key(key: str | None) -> None:
    if not key:
        raise BadRequestException(
            detail="Idempotency-Key header is required for this operation",
            error_code="IDEMPOTENCY_KEY_REQUIRED",
        )


def _serialize_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if hasattr(value, "value"):
        return value.value
    return value


def _row_to_response(row: Any) -> MasterRowResponse:
    mapper = sa_inspect(row.__class__)
    data = {
        _snake_to_camel(column.name): _serialize_value(getattr(row, column.name))
        for column in mapper.columns
        if column.name != "organization_id"
    }
    return MasterRowResponse(id=row.id, data=data)


def _column_data_type(column: Any) -> str:
    try:
        python_type = column.type.python_type
    except (AttributeError, NotImplementedError):
        python_type = str
    if python_type is bool:
        return "boolean"
    if python_type in {int, float, Decimal}:
        return "number"
    if python_type in {date, datetime}:
        return "date"
    return "text"


def _catalog_item(definition: MasterDefinition) -> MasterCatalogItem:
    mapper = sa_inspect(definition.model)
    fields: list[MasterFieldDescriptor] = []
    for column in mapper.columns:
        if column.name in _RESERVED_FIELDS:
            continue
        fields.append(
            MasterFieldDescriptor(
                key=_snake_to_camel(column.name),
                label=column.name.replace("_", " ").title(),
                data_type=_column_data_type(column),
                required=not column.nullable
                and column.default is None
                and column.server_default is None,
                editable=column.name not in _READONLY_FIELDS,
                system=column.name == "is_system",
            )
        )
    return MasterCatalogItem(
        key=definition.key,
        label=definition.label,
        description=definition.description,
        group=definition.group,
        source_table=definition.model.__tablename__,
        source_of_truth=definition.source_of_truth,
        consumer_screens=list(definition.consumer_screens),
        seed_source=definition.seed_source,
        fields=fields,
    )


def _approval_template_catalog_item() -> MasterCatalogItem:
    return MasterCatalogItem(
        key="approval-checklist-templates",
        label="Approval Checklist Templates",
        description=(
            "Reusable sanction/appraisal gating templates. Items must be sourced "
            "from the Checklist Item Catalog SSOT."
        ),
        group="Checklist SSOT",
        source_table="mst_approval_checklist_template",
        source_of_truth="mst_approval_checklist_template + mst_approval_checklist_item",
        consumer_screens=[
            "/admin/lending/applications",
            "/admin/lending/sanctions",
            "/admin/lending/masters/approval-checklist-templates",
        ],
        seed_source="backend/scripts/seed_data.py",
        fields=[
            MasterFieldDescriptor(key="code", label="Code", data_type="text", required=True),
            MasterFieldDescriptor(key="name", label="Name", data_type="text", required=True),
            MasterFieldDescriptor(
                key="appliesTo", label="Applies To", data_type="text", required=True
            ),
            MasterFieldDescriptor(key="isDefault", label="Default", data_type="boolean"),
        ],
    )


def _writable_fields(model: Any) -> set[str]:
    mapper = sa_inspect(model)
    return {column.name for column in mapper.columns if column.name not in _READONLY_FIELDS}


def _payload_to_model_data(model: Any, payload: dict[str, Any]) -> dict[str, Any]:
    writable = _writable_fields(model)
    result: dict[str, Any] = {}
    unknown: list[str] = []
    for key, value in payload.items():
        snake_key = _camel_to_snake(key)
        if snake_key not in writable:
            unknown.append(key)
            continue
        result[snake_key] = value
    if unknown:
        raise BadRequestException(
            detail=f"Unknown or read-only fields: {', '.join(sorted(unknown))}",
            error_code="LENDING_MASTER_UNKNOWN_FIELDS",
        )
    return result


@router.get(
    "/catalog",
    response_model=MasterCatalogResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions(_READ_PERM))],
)
async def list_master_catalog() -> MasterCatalogResponse:
    items = [_catalog_item(defn) for defn in MASTER_DEFINITIONS.values()]
    items.append(_approval_template_catalog_item())
    return MasterCatalogResponse(items=sorted(items, key=lambda item: (item.group, item.label)))


@router.get(
    "/approval-checklist-templates/rows",
    response_model=ChecklistTemplateListResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions(_READ_PERM))],
)
async def list_approval_checklist_templates(
    applies_to: str | None = Query(None, alias="appliesTo"),
    include_inactive: bool = Query(False, alias="includeInactive"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> ChecklistTemplateListResponse:
    service = ChecklistTemplateService(db)
    rows = await service.list_templates(
        organization_id=current_user.organization_id,
        applies_to=applies_to,
        include_inactive=include_inactive,
    )
    return ChecklistTemplateListResponse(
        items=[ChecklistTemplateResponse.model_validate(row) for row in rows],
    )


@router.get(
    "/approval-checklist-templates/rows/{template_id}",
    response_model=ChecklistTemplateResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions(_READ_PERM))],
)
async def get_approval_checklist_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> ChecklistTemplateResponse:
    service = ChecklistTemplateService(db)
    template = await service.get_template_with_items(current_user.organization_id, template_id)
    return ChecklistTemplateResponse.model_validate(template)


@router.post(
    "/approval-checklist-templates/rows",
    response_model=ChecklistTemplateResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermissions(_WRITE_PERM))],
)
async def create_approval_checklist_template(
    data: ChecklistTemplateCreate,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> ChecklistTemplateResponse:
    _require_idempotency_key(idempotency_key)
    async with db.begin():
        service = ChecklistTemplateService(db)
        template = await service.create_template(data, current_user)
    await db.refresh(template, attribute_names=["items"])
    return ChecklistTemplateResponse.model_validate(template)


@router.put(
    "/approval-checklist-templates/rows/{template_id}",
    response_model=ChecklistTemplateResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions(_WRITE_PERM))],
)
async def update_approval_checklist_template(
    template_id: UUID,
    data: ChecklistTemplateUpdate,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> ChecklistTemplateResponse:
    _require_idempotency_key(idempotency_key)
    async with db.begin():
        service = ChecklistTemplateService(db)
        template = await service.update_template(
            current_user.organization_id,
            template_id,
            data,
            current_user,
        )
    await db.refresh(template, attribute_names=["items"])
    return ChecklistTemplateResponse.model_validate(template)


@router.delete(
    "/approval-checklist-templates/rows/{template_id}",
    response_model=MessageResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions(_WRITE_PERM))],
)
async def delete_approval_checklist_template(
    template_id: UUID,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> MessageResponse:
    _require_idempotency_key(idempotency_key)
    async with db.begin():
        service = ChecklistTemplateService(db)
        await service.delete_template(current_user.organization_id, template_id, current_user)
    return MessageResponse(message="Template deleted")


@router.post(
    "/approval-checklist-templates/rows/{template_id}/items",
    response_model=ChecklistTemplateItemResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequirePermissions(_WRITE_PERM))],
)
async def add_approval_checklist_template_item(
    template_id: UUID,
    data: ChecklistTemplateItemCreate,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> ChecklistTemplateItemResponse:
    _require_idempotency_key(idempotency_key)
    async with db.begin():
        service = ChecklistTemplateService(db)
        item = await service.add_item(
            current_user.organization_id,
            template_id,
            data,
            current_user,
        )
    await db.refresh(item)
    return ChecklistTemplateItemResponse.model_validate(item)


@router.put(
    "/approval-checklist-templates/rows/{template_id}/items/{item_id}",
    response_model=ChecklistTemplateItemResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions(_WRITE_PERM))],
)
async def update_approval_checklist_template_item(
    template_id: UUID,
    item_id: UUID,
    data: ChecklistTemplateItemUpdate,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> ChecklistTemplateItemResponse:
    _require_idempotency_key(idempotency_key)
    async with db.begin():
        service = ChecklistTemplateService(db)
        item = await service.update_item(
            current_user.organization_id,
            template_id,
            item_id,
            data,
            current_user,
        )
    await db.refresh(item)
    return ChecklistTemplateItemResponse.model_validate(item)


@router.delete(
    "/approval-checklist-templates/rows/{template_id}/items/{item_id}",
    response_model=MessageResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions(_WRITE_PERM))],
)
async def delete_approval_checklist_template_item(
    template_id: UUID,
    item_id: UUID,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> MessageResponse:
    _require_idempotency_key(idempotency_key)
    async with db.begin():
        service = ChecklistTemplateService(db)
        await service.delete_item(
            current_user.organization_id,
            template_id,
            item_id,
            current_user,
        )
    return MessageResponse(message="Template item deleted")


@router.post(
    "/approval-checklist-templates/rows/{template_id}/set-default",
    response_model=ChecklistTemplateResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions(_WRITE_PERM))],
)
async def set_default_approval_checklist_template(
    template_id: UUID,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> ChecklistTemplateResponse:
    _require_idempotency_key(idempotency_key)
    async with db.begin():
        service = ChecklistTemplateService(db)
        template = await service.set_default_template(
            current_user.organization_id,
            template_id,
            current_user,
        )
    await db.refresh(template, attribute_names=["items"])
    return ChecklistTemplateResponse.model_validate(template)


@router.get(
    "/{master_key}/rows",
    response_model=MasterRowListResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions(_READ_PERM))],
)
async def list_master_rows(
    master_key: str,
    option_group: str | None = Query(None, alias="optionGroup"),
    page: int = Query(1, ge=1),
    page_size: int = Query(200, ge=1, le=500),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> MasterRowListResponse:
    definition = _definition(master_key)
    model = definition.model
    stmt = select(model).where(model.organization_id == current_user.organization_id)
    if hasattr(model, "deleted_at"):
        stmt = stmt.where(model.deleted_at.is_(None))
    if option_group and model is LendingOption:
        stmt = stmt.where(LendingOption.option_group == option_group)
    order_attr = getattr(model, definition.order_by)
    skip = (page - 1) * page_size
    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    rows = list(
        (await db.execute(stmt.order_by(order_attr).offset(skip).limit(page_size))).scalars().all()
    )
    return MasterRowListResponse(
        key=master_key,
        items=[_row_to_response(row) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/{master_key}/rows",
    response_model=MasterRowResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions(_WRITE_PERM))],
)
async def create_master_row(
    master_key: str,
    payload: MasterRowMutation,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> MasterRowResponse:
    _require_idempotency_key(idempotency_key)
    definition = _definition(master_key)
    data = _payload_to_model_data(definition.model, payload.data)
    row = definition.model(
        organization_id=current_user.organization_id,
        **data,
    )
    if hasattr(row, "is_system"):
        row.is_system = False
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return _row_to_response(row)


@router.put(
    "/{master_key}/rows/{row_id}",
    response_model=MasterRowResponse,
    response_model_by_alias=True,
    dependencies=[Depends(RequirePermissions(_WRITE_PERM))],
)
async def update_master_row(
    master_key: str,
    row_id: UUID,
    payload: MasterRowMutation,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> MasterRowResponse:
    _require_idempotency_key(idempotency_key)
    definition = _definition(master_key)
    row = await db.get(definition.model, row_id)
    if row is None or row.organization_id != current_user.organization_id:
        raise NotFoundException("Master row not found", error_code="LENDING_MASTER_ROW_NOT_FOUND")
    data = _payload_to_model_data(definition.model, payload.data)
    for key, value in data.items():
        setattr(row, key, value)
    await db.flush()
    await db.refresh(row)
    return _row_to_response(row)


@router.delete(
    "/{master_key}/rows/{row_id}",
    status_code=204,
    dependencies=[Depends(RequirePermissions(_WRITE_PERM))],
)
async def delete_master_row(
    master_key: str,
    row_id: UUID,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_with_tenant),
    current_user=Depends(get_current_user),
) -> None:
    _require_idempotency_key(idempotency_key)
    definition = _definition(master_key)
    row = await db.get(definition.model, row_id)
    if row is None or row.organization_id != current_user.organization_id:
        raise NotFoundException("Master row not found", error_code="LENDING_MASTER_ROW_NOT_FOUND")
    if getattr(row, "is_system", False):
        raise BadRequestException(
            detail="System rows cannot be deleted. Add an operator row or deactivate through an allowed workflow.",
            error_code="LENDING_MASTER_SYSTEM_ROW_LOCKED",
        )
    if hasattr(row, "soft_delete"):
        row.soft_delete(current_user.id)
    else:
        row.is_active = False
    await db.flush()
