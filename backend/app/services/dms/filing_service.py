"""Standard DMS filing engine."""

from __future__ import annotations

import re
from io import BytesIO
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException
from app.models.dms import DMSDocument, DMSFolder, DocumentAccessLevel, DocumentFilingRule
from app.services.dms.document_service import DocumentService

_TOKEN_RE = re.compile(r"{{\s*([a-zA-Z0-9_.-]+)\s*}}")
_UNSAFE_PATH_CHARS_RE = re.compile(r"[^A-Za-z0-9 ._&()/-]+")
_UNSAFE_PATH_VALUE_CHARS_RE = re.compile(r"[^A-Za-z0-9 ._&()-]+")

ENTITY_APPLICATION_GENERATED_PATH = (
    "/Entities/{{ entity.entityCode }}/Applications/"
    "{{ application.applicationNumber }}/Generated Letters"
)
ENTITY_LOAN_SANCTION_PATH = (
    "/Entities/{{ entity.entityCode }}/Loans/{{ loanAccount.accountNumber }}/Sanction & Agreements"
)
ENTITY_LOAN_STATEMENTS_PATH = (
    "/Entities/{{ entity.entityCode }}/Loans/"
    "{{ loanAccount.accountNumber }}/Statements & Certificates"
)
ENTITY_LOAN_CLOSURE_PATH = (
    "/Entities/{{ entity.entityCode }}/Loans/{{ loanAccount.accountNumber }}/Closure & Release"
)
ENTITY_LOAN_LEGAL_PATH = (
    "/Entities/{{ entity.entityCode }}/Loans/{{ loanAccount.accountNumber }}/Collections & Legal"
)
ENTITY_LOAN_IIF_PATH = (
    "/Entities/{{ entity.entityCode }}/Loans/{{ loanAccount.accountNumber }}/Interest Subvention"
)
LENDER_FACILITY_PATH = "/Lenders/{{ lender.lenderCode }}/Facility Documents"
LENDER_DRAWDOWN_PATH = "/Lenders/{{ lender.lenderCode }}/Drawdowns & Repayments"
EMPLOYEE_LETTERS_PATH = "/Employees/{{ employee.employeeCode }}/Letters"
EMPLOYEE_PAYROLL_PATH = "/Employees/{{ employee.employeeCode }}/Payroll"
VENDOR_COMPLIANCE_PATH = "/Vendors/{{ vendor.vendorCode }}/Contracts & Compliance"
FINANCE_CONFIRMATION_PATH = "/Finance/{{ finance.financialYear }}/Confirmations"
LEGAL_NOTICES_PATH = "/Legal/{{ legal.caseNumber }}/Notices & Orders"


def _rule(
    module: str,
    document_type: str,
    entity_type: str,
    path_template: str,
    tags: list[str],
    *,
    portal_visible: bool = False,
    access_level: str | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "module": module,
        "document_type": document_type,
        "entity_type": entity_type,
        "path_template": path_template,
        "default_tags": tags,
        "portal_visible": portal_visible,
    }
    if access_level:
        row["access_level"] = access_level
    return row


DEFAULT_FILING_RULES: list[dict[str, Any]] = [
    {
        "module": "LENDING",
        "document_type": "KYC",
        "entity_type": "entity",
        "path_template": "/Entities/{{ entity.entityCode }}/KYC",
        "default_tags": ["entity", "kyc"],
    },
    _rule(
        "LENDING",
        "SANCTION_LETTER",
        "sanction",
        ENTITY_LOAN_SANCTION_PATH,
        ["lending", "sanction"],
        portal_visible=True,
    ),
    _rule(
        "LENDING",
        "APPROVAL_LETTER",
        "application",
        ENTITY_APPLICATION_GENERATED_PATH,
        ["lending", "approval"],
        portal_visible=True,
    ),
    _rule(
        "LENDING",
        "KFS",
        "application",
        ENTITY_APPLICATION_GENERATED_PATH,
        ["lending", "kfs"],
        portal_visible=True,
    ),
    _rule(
        "LENDING",
        "DISBURSEMENT_ADVICE",
        "loan_account",
        ENTITY_LOAN_SANCTION_PATH,
        ["lending", "disbursement"],
        portal_visible=True,
    ),
    _rule(
        "LENDING",
        "NDC",
        "loan_account",
        ENTITY_LOAN_CLOSURE_PATH,
        ["lending", "closure"],
        portal_visible=True,
    ),
    _rule(
        "LENDING",
        "FORECLOSURE_LETTER",
        "loan_account",
        ENTITY_LOAN_CLOSURE_PATH,
        ["lending", "closure"],
        portal_visible=True,
    ),
    _rule(
        "LENDING",
        "PRE_CLOSURE_QUOTE",
        "loan_account",
        ENTITY_LOAN_CLOSURE_PATH,
        ["lending", "closure"],
        portal_visible=True,
    ),
    _rule(
        "LENDING",
        "CHARGE_RELEASE_LETTER",
        "loan_account",
        ENTITY_LOAN_CLOSURE_PATH,
        ["lending", "release"],
        portal_visible=True,
    ),
    _rule(
        "LENDING",
        "DEMAND_NOTICE",
        "loan_account",
        ENTITY_LOAN_LEGAL_PATH,
        ["lending", "collections"],
        portal_visible=True,
    ),
    _rule(
        "LENDING",
        "OTS_LETTER",
        "loan_account",
        ENTITY_LOAN_LEGAL_PATH,
        ["lending", "ots"],
        portal_visible=True,
    ),
    _rule(
        "LENDING",
        "RESTRUCTURE_ADDENDUM",
        "loan_account",
        ENTITY_LOAN_LEGAL_PATH,
        ["lending", "restructure"],
        portal_visible=True,
    ),
    _rule(
        "LENDING",
        "RATE_REVISION_INTIMATION",
        "loan_account",
        ENTITY_LOAN_STATEMENTS_PATH,
        ["lending", "rate"],
        portal_visible=True,
    ),
    _rule(
        "LENDING",
        "INTEREST_CERT",
        "loan_account",
        ENTITY_LOAN_STATEMENTS_PATH,
        ["lending", "certificate"],
        portal_visible=True,
    ),
    _rule(
        "LENDING",
        "STATEMENT_OF_ACCOUNT",
        "loan_account",
        ENTITY_LOAN_STATEMENTS_PATH,
        ["lending", "statement"],
        portal_visible=True,
    ),
    _rule(
        "LENDING",
        "IIF_CLAIM_CERTIFICATE",
        "subvention_claim",
        ENTITY_LOAN_IIF_PATH,
        ["lending", "iif", "claim-certificate"],
        portal_visible=True,
    ),
    _rule(
        "TREASURY", "LENDER_FACILITY_LETTER", "lender", LENDER_FACILITY_PATH, ["treasury", "lender"]
    ),
    _rule("TREASURY", "DRAWDOWN_REQUEST", "lender", LENDER_DRAWDOWN_PATH, ["treasury", "drawdown"]),
    _rule(
        "TREASURY", "REPAYMENT_ADVICE", "lender", LENDER_DRAWDOWN_PATH, ["treasury", "repayment"]
    ),
    _rule(
        "TREASURY",
        "COVENANT_COMPLIANCE_CERTIFICATE",
        "lender",
        LENDER_FACILITY_PATH,
        ["treasury", "covenant"],
    ),
    _rule("HRIS", "OFFER_LETTER", "employee", EMPLOYEE_LETTERS_PATH, ["hris", "offer"]),
    _rule("HRIS", "APPOINTMENT_LETTER", "employee", EMPLOYEE_LETTERS_PATH, ["hris", "appointment"]),
    _rule("HRIS", "EMPLOYEE_LETTER", "employee", EMPLOYEE_LETTERS_PATH, ["hris", "employee"]),
    _rule("HRIS", "EXPERIENCE_LETTER", "employee", EMPLOYEE_LETTERS_PATH, ["hris", "experience"]),
    _rule("HRIS", "RELIEVING_LETTER", "employee", EMPLOYEE_LETTERS_PATH, ["hris", "separation"]),
    _rule("HRIS", "TRAINING_CERTIFICATE", "employee", EMPLOYEE_LETTERS_PATH, ["hris", "training"]),
    _rule(
        "PAYROLL",
        "PAYSLIP",
        "employee",
        EMPLOYEE_PAYROLL_PATH,
        ["payroll", "employee"],
        portal_visible=True,
    ),
    _rule(
        "PAYROLL",
        "SALARY_REVISION_LETTER",
        "employee",
        EMPLOYEE_LETTERS_PATH,
        ["payroll", "revision"],
    ),
    _rule(
        "PAYROLL",
        "BONUS_LETTER",
        "employee",
        EMPLOYEE_PAYROLL_PATH,
        ["payroll", "bonus"],
        portal_visible=True,
    ),
    _rule(
        "PAYROLL",
        "FNF_STATEMENT",
        "employee",
        EMPLOYEE_PAYROLL_PATH,
        ["payroll", "fnf"],
        portal_visible=True,
    ),
    _rule(
        "AP_AR", "VENDOR_CERTIFICATE", "vendor", VENDOR_COMPLIANCE_PATH, ["vendor", "compliance"]
    ),
    _rule("AP_AR", "PAYMENT_ADVICE", "vendor", VENDOR_COMPLIANCE_PATH, ["vendor", "payment"]),
    _rule(
        "FINANCE",
        "BALANCE_CONFIRMATION",
        "financial_year",
        FINANCE_CONFIRMATION_PATH,
        ["finance", "confirmation"],
    ),
    _rule(
        "FINANCE",
        "AUDIT_CONFIRMATION",
        "financial_year",
        FINANCE_CONFIRMATION_PATH,
        ["finance", "audit"],
    ),
    _rule("LEGAL", "LEGAL_NOTICE", "legal_case", LEGAL_NOTICES_PATH, ["legal", "notice"]),
    _rule("LEGAL", "SARFAESI_13_2_NOTICE", "legal_case", LEGAL_NOTICES_PATH, ["legal", "sarfaesi"]),
    _rule(
        "LEGAL", "ARBITRATION_NOTICE", "legal_case", LEGAL_NOTICES_PATH, ["legal", "arbitration"]
    ),
    _rule(
        "VENDOR_PORTAL",
        "VENDOR_REGISTRATION_APPROVAL",
        "vendor",
        VENDOR_COMPLIANCE_PATH,
        ["vendor", "portal"],
    ),
    _rule(
        "BORROWER_PORTAL",
        "SERVICE_REQUEST_ACK",
        "portal_request",
        ENTITY_APPLICATION_GENERATED_PATH,
        ["portal", "request"],
        portal_visible=True,
    ),
    _rule(
        "ESS",
        "LEAVE_APPROVAL",
        "employee",
        EMPLOYEE_LETTERS_PATH,
        ["ess", "leave"],
        portal_visible=True,
    ),
    _rule(
        "ESS",
        "REIMBURSEMENT_APPROVAL",
        "employee",
        EMPLOYEE_PAYROLL_PATH,
        ["ess", "reimbursement"],
        portal_visible=True,
    ),
]


def _lookup(context: dict[str, Any], dotted_key: str) -> Any:
    value: Any = context
    for part in dotted_key.split("."):
        if isinstance(value, dict):
            value = value.get(part)
        else:
            value = getattr(value, part, None)
        if value in (None, ""):
            return None
    return value


def _fallback_label(entity_type: str, entity_id: UUID | None) -> str:
    short_id = str(entity_id)[:8] if entity_id else "unlinked"
    return f"{entity_type}-{short_id}"


def _safe_path_value(value: Any, *, entity_type: str, entity_id: UUID | None) -> str:
    text = str(value or _fallback_label(entity_type, entity_id))
    text = _UNSAFE_PATH_VALUE_CHARS_RE.sub("-", text)
    text = text.replace("/", "-").replace("\\", "-").replace("..", ".")
    text = text.strip(" .")
    return text or _fallback_label(entity_type, entity_id)


def render_path_template(
    path_template: str,
    context: dict[str, Any],
    *,
    entity_type: str,
    entity_id: UUID | None,
) -> str:
    """Render and sanitize a governed DMS folder path template."""

    def replace(match: re.Match[str]) -> str:
        raw = _lookup(context, match.group(1))
        return _safe_path_value(raw, entity_type=entity_type, entity_id=entity_id)

    rendered = _TOKEN_RE.sub(replace, path_template).strip()
    rendered = _UNSAFE_PATH_CHARS_RE.sub("-", rendered)
    parts = [
        part.strip(" .")
        for part in rendered.split("/")
        if part.strip(" .") and part.strip(" .") not in {".", ".."}
    ]
    if not parts:
        raise BadRequestException(
            detail="Filing path template resolved to an empty path",
            error_code="DMS_FILING_EMPTY_PATH",
        )
    return "/" + "/".join(parts)


class DocumentFilingService:
    """Resolve governed folders and file documents into DMS."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.documents = DocumentService(db)

    async def list_rules(
        self,
        *,
        organization_id: UUID,
        module: str | None = None,
        document_type: str | None = None,
    ) -> list[DocumentFilingRule]:
        stmt = select(DocumentFilingRule).where(
            DocumentFilingRule.organization_id == organization_id,
            DocumentFilingRule.is_active.is_(True),
        )
        if module:
            stmt = stmt.where(DocumentFilingRule.module == module)
        if document_type:
            stmt = stmt.where(DocumentFilingRule.document_type == document_type)
        result = await self.db.execute(
            stmt.order_by(DocumentFilingRule.priority, DocumentFilingRule.module)
        )
        return list(result.scalars().all())

    async def create_rule(
        self,
        *,
        organization_id: UUID,
        data: dict[str, Any],
        created_by: UUID | None,
    ) -> DocumentFilingRule:
        row = DocumentFilingRule(
            organization_id=organization_id,
            module=data["module"],
            document_type=data["document_type"],
            entity_type=data["entity_type"],
            path_template=data["path_template"],
            access_level=data.get("access_level") or DocumentAccessLevel.ORGANIZATION.value,
            retention_policy=data.get("retention_policy"),
            portal_visible=bool(data.get("portal_visible", False)),
            default_tags=data.get("default_tags") or [],
            description=data.get("description"),
            priority=data.get("priority", 100),
            is_system=False,
            created_by=created_by,
        )
        self.db.add(row)
        await self.db.flush()
        await self.db.refresh(row)
        return row

    async def ensure_default_rules(
        self,
        *,
        organization_id: UUID,
        created_by: UUID | None = None,
    ) -> None:
        for rule in DEFAULT_FILING_RULES:
            existing = (
                await self.db.execute(
                    select(DocumentFilingRule).where(
                        DocumentFilingRule.organization_id == organization_id,
                        DocumentFilingRule.module == rule["module"],
                        DocumentFilingRule.document_type == rule["document_type"],
                        DocumentFilingRule.entity_type == rule["entity_type"],
                    )
                )
            ).scalar_one_or_none()
            if existing:
                continue
            self.db.add(
                DocumentFilingRule(
                    organization_id=organization_id,
                    module=rule["module"],
                    document_type=rule["document_type"],
                    entity_type=rule["entity_type"],
                    path_template=rule["path_template"],
                    access_level=rule.get("access_level", DocumentAccessLevel.ORGANIZATION.value),
                    portal_visible=rule.get("portal_visible", False),
                    default_tags=rule.get("default_tags", []),
                    priority=rule.get("priority", 100),
                    is_system=True,
                    created_by=created_by,
                )
            )
        await self.db.flush()

    async def resolve_rule(
        self,
        *,
        organization_id: UUID,
        module: str,
        document_type: str,
        entity_type: str,
    ) -> DocumentFilingRule | None:
        await self.ensure_default_rules(organization_id=organization_id)
        stmt = (
            select(DocumentFilingRule)
            .where(
                DocumentFilingRule.organization_id == organization_id,
                DocumentFilingRule.module == module,
                DocumentFilingRule.document_type == document_type,
                DocumentFilingRule.entity_type == entity_type,
                DocumentFilingRule.is_active.is_(True),
            )
            .order_by(DocumentFilingRule.priority)
            .limit(1)
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def resolve_path(
        self,
        *,
        organization_id: UUID,
        module: str,
        document_type: str,
        entity_type: str,
        entity_id: UUID | None,
        context: dict[str, Any],
    ) -> tuple[str, DocumentFilingRule | None]:
        rule = await self.resolve_rule(
            organization_id=organization_id,
            module=module,
            document_type=document_type,
            entity_type=entity_type,
        )
        if rule:
            return (
                render_path_template(
                    rule.path_template,
                    context,
                    entity_type=entity_type,
                    entity_id=entity_id,
                ),
                rule,
            )
        fallback_label = _fallback_label(entity_type, entity_id)
        fallback_path = f"/Unfiled/{module}/{document_type}/{fallback_label}"
        return (fallback_path, None)

    async def ensure_folder_path(
        self,
        *,
        organization_id: UUID,
        path: str,
        entity_type: str | None = None,
        entity_id: UUID | None = None,
        access_level: str = DocumentAccessLevel.ORGANIZATION.value,
        created_by: UUID | None = None,
    ) -> DMSFolder:
        parent_id: UUID | None = None
        current_path = ""
        current: DMSFolder | None = None
        parts = [p for p in path.split("/") if p]
        for index, part in enumerate(parts):
            is_leaf = index == len(parts) - 1
            current_path = f"{current_path}/{part}"
            current = (
                await self.db.execute(
                    select(DMSFolder).where(
                        DMSFolder.organization_id == organization_id,
                        DMSFolder.path == current_path,
                        DMSFolder.is_active.is_(True),
                    )
                )
            ).scalar_one_or_none()
            if current is None:
                current = DMSFolder(
                    organization_id=organization_id,
                    parent_id=parent_id,
                    name=part,
                    path=current_path,
                    level=index,
                    folder_type="entity" if entity_id and is_leaf else "system",
                    entity_type=entity_type if is_leaf else None,
                    entity_id=entity_id if is_leaf else None,
                    access_level=access_level,
                    created_by=created_by,
                )
                self.db.add(current)
                await self.db.flush()
            parent_id = current.id
        if current is None:
            raise BadRequestException(
                detail="Could not resolve DMS folder path",
                error_code="DMS_FOLDER_RESOLVE_FAILED",
            )
        await self.db.refresh(current)
        return current

    async def resolve_folder(
        self,
        *,
        organization_id: UUID,
        module: str,
        document_type: str,
        entity_type: str,
        entity_id: UUID | None,
        context: dict[str, Any],
        created_by: UUID | None = None,
    ) -> tuple[DMSFolder, str, DocumentFilingRule | None]:
        path, rule = await self.resolve_path(
            organization_id=organization_id,
            module=module,
            document_type=document_type,
            entity_type=entity_type,
            entity_id=entity_id,
            context=context,
        )
        folder = await self.ensure_folder_path(
            organization_id=organization_id,
            path=path,
            entity_type=entity_type,
            entity_id=entity_id,
            access_level=rule.access_level if rule else DocumentAccessLevel.ORGANIZATION.value,
            created_by=created_by,
        )
        return folder, path, rule

    async def file_bytes(
        self,
        *,
        organization_id: UUID,
        content: bytes,
        file_name: str,
        mime_type: str,
        module: str,
        document_type: str,
        document_subtype: str | None,
        entity_type: str,
        entity_id: UUID,
        context: dict[str, Any],
        name: str,
        description: str | None = None,
        keywords: list[str] | None = None,
        created_by: UUID | None = None,
    ) -> tuple[DMSDocument, DMSFolder, DocumentFilingRule | None]:
        folder, _, rule = await self.resolve_folder(
            organization_id=organization_id,
            module=module,
            document_type=document_type,
            entity_type=entity_type,
            entity_id=entity_id,
            context=context,
            created_by=created_by,
        )
        access_level = (
            DocumentAccessLevel(rule.access_level) if rule else DocumentAccessLevel.ORGANIZATION
        )
        doc = await self.documents.upload_document(
            organization_id=organization_id,
            file=BytesIO(content),
            file_name=file_name,
            file_size=len(content),
            mime_type=mime_type,
            folder_id=folder.id,
            name=name,
            description=description,
            document_type=document_type,
            document_subtype=document_subtype,
            entity_type=entity_type,
            entity_id=entity_id,
            access_level=access_level,
            keywords=keywords or (rule.default_tags if rule else None),
            created_by=created_by,
            auto_commit=False,
        )
        return doc, folder, rule

    async def entity_vault(
        self,
        *,
        organization_id: UUID,
        entity_type: str,
        entity_id: UUID,
    ) -> tuple[list[DMSFolder], list[DMSDocument]]:
        folders = list(
            (
                await self.db.execute(
                    select(DMSFolder)
                    .where(
                        DMSFolder.organization_id == organization_id,
                        DMSFolder.entity_type == entity_type,
                        DMSFolder.entity_id == entity_id,
                        DMSFolder.is_active.is_(True),
                    )
                    .order_by(DMSFolder.path)
                )
            )
            .scalars()
            .all()
        )
        documents = list(
            (
                await self.db.execute(
                    select(DMSDocument)
                    .where(
                        DMSDocument.organization_id == organization_id,
                        DMSDocument.entity_type == entity_type,
                        DMSDocument.entity_id == entity_id,
                        DMSDocument.is_active.is_(True),
                    )
                    .order_by(DMSDocument.created_at.desc())
                )
            )
            .scalars()
            .all()
        )
        return folders, documents
