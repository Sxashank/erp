#!/usr/bin/env python3
"""Seed manual-lending UAT data.

This is intentionally manual-first: it creates no bank/GSTN/NACH/AA/bureau
integration configuration and does not call any external service.
"""

from __future__ import annotations

import argparse
import asyncio
import re
import sys
from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

import app.models  # noqa: F401 - ensure common ORM models are registered
import app.models.lending  # noqa: F401 - ensure lending ORM models are registered
from app.core.constants import ALL_PERMISSIONS, Permissions, UserStatus
from app.core.constants import EntityStatus as OrgStatus
from app.core.iif_rules import DEFAULT_REQUIRED_DOCUMENTS
from app.core.security import get_password_hash
from app.database import async_session_factory
from app.db.seeds.lending_masters import seed_for_organization as seed_lending_master_catalog
from app.models.auth.role import Permission, Role, RolePermission, UserRole
from app.models.auth.user import User
from app.models.finance.account import Account
from app.models.lending import (
    AllocationComponent,
    ApplicationFundingSource,
    ApplicationLenderLoan,
    ApplicationStage,
    ApplicationStatus,
    ApprovalChecklistTemplate,
    ApprovalChecklistTemplateItem,
    AssetClassification,
    ChargeType,
    ChecklistAppliesTo,
    ChecklistItemCategory,
    ContactType,
    DayCountConvention,
    Disbursement,
    DisbursementMode,
    DisbursementStatus,
    DocumentCategory,
    DocumentChecklist,
    DocumentStage,
    Entity,
    EntityContact,
    EntityStatus,
    EntityType,
    FundDeployment,
    FundUtilizationCategory,
    InstallmentStatus,
    InterestType,
    LoanAccount,
    LoanAccountStatus,
    LoanApplication,
    LoanProduct,
    LoanReceipt,
    LoanSanction,
    LoanSecurity,
    LoanSubventionEnrollment,
    ProductCategory,
    ReceiptAllocation,
    ReceiptMode,
    ReceiptStatus,
    ReceiptType,
    RepaymentFrequency,
    RepaymentMode,
    RepaymentSchedule,
    SanctionStatus,
    ScheduleInstallment,
    ScheduleType,
    SecurityCategory,
    SecurityStatus,
    SecurityType,
    SubventionClaim,
    SubventionScheme,
)
from app.models.lending.enums import (
    BorrowingRateType,
    BorrowingSecurityType,
    BorrowingStatus,
    BorrowingType,
    ClaimFrequency,
    CouponFrequency,
    DrawdownStatus,
    IIFLoanType,
    InvestmentCategory,
    InvestmentStatus,
    InvestmentType,
    LenderStatus,
    LenderType,
    SubventionClaimStatus,
    SubventionEnrollmentStatus,
)
from app.models.lending.masters import ChecklistItemCatalog
from app.models.lending.treasury import (
    Borrowing,
    BorrowingSchedule,
    BorrowingTranche,
    Lender,
)
from app.models.lending.treasury_investment import TreasuryInvestment
from app.models.masters.organization import Organization
from app.models.portal.enums import PortalActorRole, PortalRegistrationStatus, PortalUserStatus
from app.models.portal.portal_user import PortalUser
from app.models.portal.portal_user_entity import PortalUserEntity
from app.models.workflow.enums import WorkflowEntityType
from app.models.workflow.workflow_definition import WorkflowDefinition

ROOT = Path(__file__).resolve().parents[1]
ADMIN_USERNAME = "krishna"
ADMIN_PASSWORD = "ChangeMe123!"
PORTAL_EMAIL = "borrower.portal.uat@smfc.com"
PORTAL_PASSWORD = "Portal@123"
PORTAL_ADMIN_EMAIL = "scheme.admin.uat@smfc.com"
PORTAL_ADMIN_PASSWORD = "PortalAdmin@123"

PORTAL_DOC_CATALOG_MAP = {
    "BOARD_RESOLUTION": "KYC_BOARD_RESOLUTION",
    "FINANCIAL_STATEMENT": "FIN_AUDITED_FINANCIALS",
    "PROJECT_PROPOSAL": "PROJECT_DPR",
    "SUPPORTING_DOCUMENT": "SUPPORTING_DOCUMENT",
}

DOCUMENT_CATEGORY_FROM_CATALOG = {
    "KYC": DocumentCategory.KYC,
    "FINANCIAL": DocumentCategory.FINANCIAL,
    "LEGAL": DocumentCategory.LEGAL,
    "INSURANCE": DocumentCategory.INSURANCE,
    "REGULATORY": DocumentCategory.REGULATORY,
    "PROPERTY": DocumentCategory.SECURITY,
    "VESSEL": DocumentCategory.SECURITY,
    "PORT": DocumentCategory.PROJECT,
    "OTHER": DocumentCategory.PROJECT,
}

APPROVAL_CHECKLIST_TEMPLATE_ITEMS = [
    ("KYC_CIN", True, True),
    ("FIN_CASHFLOW_MODEL", True, True),
    ("PROJECT_DPR", True, True),
    ("REG_CERSAI_FILING", True, True),
    ("LEGAL_VETTING", True, True),
    ("KYC_BOARD_RESOLUTION", True, True),
]

APPROVAL_CATEGORY_FROM_CATALOG = {
    "KYC": ChecklistItemCategory.KYC.value,
    "LEGAL": ChecklistItemCategory.LEGAL.value,
    "INSURANCE": ChecklistItemCategory.INSURANCE.value,
    "REGULATORY": ChecklistItemCategory.COMPLIANCE.value,
    "FINANCIAL": ChecklistItemCategory.DOCUMENT.value,
    "PROPERTY": ChecklistItemCategory.DOCUMENT.value,
    "VESSEL": ChecklistItemCategory.DOCUMENT.value,
    "PORT": ChecklistItemCategory.DOCUMENT.value,
    "OTHER": ChecklistItemCategory.OTHER.value,
}


def money(value: str | int | float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


def today() -> date:
    return date.today()


async def get_lending_gl_accounts(session: AsyncSession, org: Organization) -> dict[str, object]:
    """Resolve seeded lending GL mappings by account code."""
    code_map = {
        "loan_asset": "1301",
        "interest_receivable": "1404",
        "interest_income": "4001",
        "penal_interest_income": "4103",
        "charges_income": "4101",
        "receipt_suspense": "2104",
        "source_bank": "1101",
    }
    rows = (
        await session.execute(
            select(Account).where(
                Account.organization_id == org.id,
                Account.code.in_(code_map.values()),
            )
        )
    ).scalars()
    accounts_by_code = {account.code: account.id for account in rows}
    return {key: accounts_by_code.get(code) for key, code in code_map.items()}


def now_utc() -> datetime:
    return datetime.now(UTC)


def now_naive() -> datetime:
    return datetime.now()


def add_months(base: date, months: int) -> date:
    year = base.year + ((base.month - 1 + months) // 12)
    month = ((base.month - 1 + months) % 12) + 1
    day = min(base.day, 28)
    return date(year, month, day)


async def scalar_one_or_none(session: AsyncSession, stmt):
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


def discover_permission_codes() -> set[str]:
    """Parse backend permission dependency usage into seedable permission codes."""
    codes: set[str] = {
        "MASTER_ORG_VIEW",
        "USER_VIEW",
        "ROLE_VIEW",
    }
    for permission_group in ALL_PERMISSIONS.values():
        codes.update(str(code) for code in permission_group)

    pattern = re.compile(r"(?:RequirePermissions|PermissionChecker)\((.*?)\)", re.DOTALL)
    for path in (ROOT / "app" / "api").rglob("*.py"):
        text = path.read_text()
        for match in pattern.finditer(text):
            codes.update(re.findall(r"[\"']([A-Z0-9_]+)[\"']", match.group(1)))
            for permission_name in re.findall(r"Permissions\.([A-Z0-9_]+)", match.group(1)):
                permission_code = getattr(Permissions, permission_name, None)
                if permission_code:
                    codes.add(str(permission_code))
    return codes


async def ensure_permissions(session: AsyncSession, role: Role) -> None:
    existing_codes = {code for (code,) in (await session.execute(select(Permission.code))).all()}
    permissions: list[Permission] = []
    for code in sorted(discover_permission_codes() - existing_codes):
        module = code.split("_", 1)[0]
        permission = Permission(
            code=code,
            name=code.replace("_", " ").title(),
            module=module,
            resource=code.lower(),
            action="READ" if code.endswith("_VIEW") else "MANAGE",
        )
        session.add(permission)
        permissions.append(permission)

    await session.flush()
    all_permissions = (await session.execute(select(Permission))).scalars().all()
    assigned_ids = {
        permission_id
        for (permission_id,) in (
            await session.execute(
                select(RolePermission.permission_id).where(RolePermission.role_id == role.id)
            )
        ).all()
    }
    for permission in all_permissions:
        if permission.id not in assigned_ids:
            session.add(RolePermission(role_id=role.id, permission_id=permission.id))


async def ensure_base_access(
    session: AsyncSession,
    *,
    reset_password: bool,
) -> tuple[Organization, User]:
    org = await scalar_one_or_none(
        session, select(Organization).where(Organization.code == "SMFC_UAT")
    )
    if not org:
        org = Organization(
            code="SMFC_UAT",
            name="Sagarmala Finance Corporation UAT",
            legal_name="Sagarmala Finance Corporation Limited",
            short_name="SMFCL UAT",
            pan="AABCS1234Q",
            tan="MUMS12345A",
            gstin="27AABCS1234Q1Z5",
            rbi_registration="UAT-NBFC-001",
            reg_city="Mumbai",
            reg_state_code="27",
            phone="02240000000",
            email="uat@smfcl.gov.in",
            website="https://sagarmala.gov.in",
            base_currency="INR",
            financial_year_start_month=4,
            status=OrgStatus.ACTIVE.value,
            is_primary=True,
        )
        session.add(org)
        await session.flush()

    role = await scalar_one_or_none(session, select(Role).where(Role.code == "SUPER_ADMIN"))
    if not role:
        role = Role(
            code="SUPER_ADMIN",
            name="Super Administrator",
            description="Full UAT administration access",
            is_system_role=True,
            is_default=False,
        )
        session.add(role)
        await session.flush()
    await ensure_permissions(session, role)

    user = await scalar_one_or_none(session, select(User).where(User.username == ADMIN_USERNAME))
    if not user:
        user = User(
            username=ADMIN_USERNAME,
            email="krishna@supersight.com",
            full_name="Krishna Administrator",
            employee_code="UAT001",
            password_hash=get_password_hash(ADMIN_PASSWORD),
            status=UserStatus.ACTIVE.value,
            organization_id=org.id,
            must_change_password=False,
        )
        session.add(user)
        await session.flush()
    else:
        user.organization_id = org.id
        user.status = UserStatus.ACTIVE.value
        user.locked_until = None
        user.failed_login_attempts = 0
        user.must_change_password = False
        if reset_password:
            user.password_hash = get_password_hash(ADMIN_PASSWORD)

    existing_assignment = await scalar_one_or_none(
        session,
        select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == role.id),
    )
    if not existing_assignment:
        session.add(
            UserRole(
                user_id=user.id,
                role_id=role.id,
                unit_id=None,
                effective_from=datetime.now(UTC) - timedelta(days=1),
            )
        )
    return org, user


async def ensure_product(
    session: AsyncSession,
    org: Organization,
    *,
    code: str,
    name: str,
    category: ProductCategory,
    repayment_mode: RepaymentMode,
) -> LoanProduct:
    product = await scalar_one_or_none(
        session,
        select(LoanProduct).where(
            LoanProduct.organization_id == org.id,
            LoanProduct.code == code,
        ),
    )
    if not product:
        product = LoanProduct(
            organization_id=org.id,
            code=code,
            name=name,
            description=f"UAT product for {name}",
            category=category,
            min_amount=money("1000000"),
            max_amount=money("5000000000"),
            default_amount=money("250000000"),
            min_tenure_months=12,
            max_tenure_months=180,
            default_tenure_months=84,
            allows_moratorium=True,
            max_moratorium_months=24,
            moratorium_type="INTEREST_ONLY",
            interest_type=InterestType.FLOATING,
            min_spread_bps=150,
            max_spread_bps=600,
            default_spread_bps=275,
            min_effective_rate=money("8.00"),
            max_effective_rate=money("18.00"),
            day_count_convention=DayCountConvention.ACT_365,
            allowed_repayment_frequencies=["MONTHLY", "QUARTERLY"],
            default_repayment_frequency=RepaymentFrequency.QUARTERLY,
            allowed_repayment_modes=["EMI", "STRUCTURED", "BULLET"],
            default_repayment_mode=repayment_mode,
            requires_collateral=True,
            min_collateral_coverage=money("125.00"),
            eligible_entity_types=["CORPORATE", "LLP"],
            disbursement_type="TRANCHE_BASED",
            max_tranches=4,
            allows_partial_disbursement=True,
            disbursement_validity_days=365,
            is_active_for_new_loans=True,
            effective_from=date(2026, 4, 1),
        )
        session.add(product)
        await session.flush()
    await ensure_product_document_checklist(session, product)
    return product


async def ensure_product_document_checklist(
    session: AsyncSession,
    product: LoanProduct,
) -> None:
    """Seed borrower-facing application documents for the portal demo.

    These are application-stage documents only. Sanction, schedule, security,
    source-of-funds and lender repayment documents remain in internal admin
    workflows.
    """

    checklist = [
        {
            "code": "BOARD_RESOLUTION",
            "name": "Board resolution / borrowing authority",
            "category": DocumentCategory.LEGAL,
            "mandatory": True,
            "help": "Upload the board or equivalent authorisation approving the proposed SFC borrowing.",
            "order": 10,
        },
        {
            "code": "FINANCIAL_STATEMENT",
            "name": "Audited financial statements",
            "category": DocumentCategory.FINANCIAL,
            "mandatory": True,
            "help": "Upload the latest audited financial statements used for credit appraisal.",
            "order": 20,
        },
        {
            "code": "PROJECT_PROPOSAL",
            "name": "Project proposal / DPR",
            "category": DocumentCategory.PROJECT,
            "mandatory": True,
            "help": "Upload the project proposal, DPR, cost estimates or equivalent project note.",
            "order": 30,
        },
        {
            "code": "SUPPORTING_DOCUMENT",
            "name": "Additional supporting document",
            "category": DocumentCategory.PROJECT,
            "mandatory": False,
            "help": "Use this for any additional borrower-side project or eligibility document requested by SFC.",
            "order": 90,
        },
    ]

    for item in checklist:
        catalog_code = PORTAL_DOC_CATALOG_MAP[item["code"]]
        catalog_item = await scalar_one_or_none(
            session,
            select(ChecklistItemCatalog).where(
                ChecklistItemCatalog.organization_id == product.organization_id,
                ChecklistItemCatalog.code == catalog_code,
                ChecklistItemCatalog.deleted_at.is_(None),
            ),
        )
        if catalog_item is None:
            raise RuntimeError(f"Missing checklist catalog item {catalog_code}")
        category = DOCUMENT_CATEGORY_FROM_CATALOG[catalog_item.category]
        stage = DocumentStage(catalog_item.stage)
        existing = await scalar_one_or_none(
            session,
            select(DocumentChecklist).where(
                DocumentChecklist.product_id == product.id,
                DocumentChecklist.code == catalog_item.code,
            ),
        )
        if existing:
            existing.catalog_item_id = catalog_item.id
            existing.name = catalog_item.label
            existing.description = item["help"]
            existing.category = category
            existing.required_at_stage = stage
            existing.is_mandatory = item["mandatory"]
            existing.applicable_entity_types = ["CORPORATE", "LLP"]
            existing.allowed_file_types = ["pdf", "jpg", "jpeg", "png", "xlsx", "xls"]
            existing.max_file_size_mb = 50
            existing.min_file_count = 1
            existing.max_file_count = 5
            existing.display_order = item["order"]
            existing.help_text = item["help"]
            existing.is_active = True
            continue
        session.add(
            DocumentChecklist(
                product_id=product.id,
                catalog_item_id=catalog_item.id,
                code=catalog_item.code,
                name=catalog_item.label,
                description=item["help"],
                category=category,
                required_at_stage=stage,
                is_mandatory=item["mandatory"],
                is_mandatory_for_disbursement=False,
                applicable_entity_types=["CORPORATE", "LLP"],
                allowed_file_types=["pdf", "jpg", "jpeg", "png", "xlsx", "xls"],
                max_file_size_mb=50,
                min_file_count=1,
                max_file_count=5,
                requires_verification=True,
                display_order=item["order"],
                help_text=item["help"],
            )
        )


async def ensure_active_products_have_application_checklist(
    session: AsyncSession,
    org: Organization,
) -> None:
    """Backfill borrower-facing requirements for all active demo products.

    Focused E2E seed chains can add products that are still visible in the
    borrower portal. Demo-visible products must not appear without
    product-driven application document requirements.
    """

    products = (
        (
            await session.execute(
                select(LoanProduct).where(
                    LoanProduct.organization_id == org.id,
                    LoanProduct.is_active_for_new_loans.is_(True),
                )
            )
        )
        .scalars()
        .all()
    )
    for product in products:
        await ensure_product_document_checklist(session, product)


async def ensure_approval_checklist_template(
    session: AsyncSession,
    org: Organization,
) -> None:
    template = await scalar_one_or_none(
        session,
        select(ApprovalChecklistTemplate).where(
            ApprovalChecklistTemplate.organization_id == org.id,
            ApprovalChecklistTemplate.code == "UAT_CORP_LOAN_APPROVAL",
            ApprovalChecklistTemplate.deleted_at.is_(None),
        ),
    )
    if template is None:
        template = ApprovalChecklistTemplate(
            organization_id=org.id,
            code="UAT_CORP_LOAN_APPROVAL",
            name="UAT Corporate Loan Approval Checklist",
            description="Default appraisal and sanction gating checklist for the UAT loan demo.",
            applies_to=ChecklistAppliesTo.LOAN_APPLICATION.value,
            is_default=True,
        )
        session.add(template)
        await session.flush()
    else:
        template.name = "UAT Corporate Loan Approval Checklist"
        template.description = (
            "Default appraisal and sanction gating checklist for the UAT loan demo."
        )
        template.applies_to = ChecklistAppliesTo.LOAN_APPLICATION.value
        template.is_default = True

    for sort_order, (catalog_code, mandatory, evidence) in enumerate(
        APPROVAL_CHECKLIST_TEMPLATE_ITEMS,
        start=1,
    ):
        catalog_item = await scalar_one_or_none(
            session,
            select(ChecklistItemCatalog).where(
                ChecklistItemCatalog.organization_id == org.id,
                ChecklistItemCatalog.code == catalog_code,
                ChecklistItemCatalog.deleted_at.is_(None),
            ),
        )
        if catalog_item is None:
            raise RuntimeError(f"Missing approval checklist catalog item {catalog_code}")

        item = await scalar_one_or_none(
            session,
            select(ApprovalChecklistTemplateItem).where(
                ApprovalChecklistTemplateItem.template_id == template.id,
                ApprovalChecklistTemplateItem.code == catalog_item.code,
                ApprovalChecklistTemplateItem.deleted_at.is_(None),
            ),
        )
        category = APPROVAL_CATEGORY_FROM_CATALOG.get(
            catalog_item.category,
            ChecklistItemCategory.OTHER.value,
        )
        if item is None:
            session.add(
                ApprovalChecklistTemplateItem(
                    template_id=template.id,
                    catalog_item_id=catalog_item.id,
                    code=catalog_item.code,
                    label=catalog_item.label,
                    description=catalog_item.description,
                    category=category,
                    is_mandatory=mandatory,
                    sort_order=sort_order,
                    default_due_offset_days=7,
                    requires_evidence=evidence,
                )
            )
            continue

        item.catalog_item_id = catalog_item.id
        item.label = catalog_item.label
        item.description = catalog_item.description
        item.category = category
        item.is_mandatory = mandatory
        item.sort_order = sort_order
        item.default_due_offset_days = 7
        item.requires_evidence = evidence


async def ensure_entity(
    session: AsyncSession,
    org: Organization,
    *,
    code: str,
    pan: str,
    legal_name: str,
    rating: str,
) -> Entity:
    entity = await scalar_one_or_none(
        session,
        select(Entity).where(Entity.organization_id == org.id, Entity.entity_code == code),
    )
    if not entity:
        entity = Entity(
            organization_id=org.id,
            entity_code=code,
            entity_type=EntityType.CORPORATE,
            legal_name=legal_name,
            trade_name=legal_name.replace(" Private Limited", ""),
            pan=pan,
            gstin=f"27{pan}1Z5",
            kyc_verified=True,
            kyc_verified_date=today() - timedelta(days=45),
            date_of_incorporation=date(2016, 7, 1),
            place_of_incorporation="Mumbai",
            country_of_incorporation="IND",
            internal_rating=rating,
            external_rating="A-",
            external_rating_agency="ICRA",
            authorized_capital=money("1000000000"),
            paid_up_capital=money("350000000"),
            net_worth=money("725000000"),
            turnover=money("2850000000"),
            employee_count=460,
            primary_email=f"{code.lower()}@example.com",
            primary_phone="9876543210",
            region="West",
            status=EntityStatus.ACTIVE,
            onboarding_date=today() - timedelta(days=120),
            remarks="UAT corporate borrower seeded for manual lending certification.",
        )
        session.add(entity)
        await session.flush()
    return entity


async def ensure_entity_contact(
    session: AsyncSession,
    entity: Entity,
    *,
    contact_type: ContactType,
    first_name: str,
    last_name: str,
    designation: str,
    email: str,
    mobile: str,
    pan: str | None = None,
    din: str | None = None,
    is_primary: bool = False,
    is_authorized_signatory: bool = False,
    shareholding_percentage: Decimal | None = None,
) -> EntityContact:
    contact = await scalar_one_or_none(
        session,
        select(EntityContact).where(
            EntityContact.entity_id == entity.id,
            EntityContact.email == email,
            EntityContact.deleted_at.is_(None),
        ),
    )
    if not contact:
        contact = EntityContact(
            entity_id=entity.id,
            contact_type=contact_type,
            first_name=first_name,
            last_name=last_name,
            designation=designation,
            email=email,
            mobile=mobile,
            pan=pan,
            din=din,
            is_primary=is_primary,
            is_authorized_signatory=is_authorized_signatory,
            shareholding_percentage=shareholding_percentage,
            kyc_verified=True,
            remarks="Seeded UAT borrower contact for manual lending certification.",
        )
        session.add(contact)
        await session.flush()
    else:
        contact.contact_type = contact_type
        contact.first_name = first_name
        contact.last_name = last_name
        contact.designation = designation
        contact.mobile = mobile
        contact.pan = pan
        contact.din = din
        contact.is_primary = is_primary
        contact.is_authorized_signatory = is_authorized_signatory
        contact.shareholding_percentage = shareholding_percentage
        contact.kyc_verified = True
        contact.is_active = True
    return contact


async def ensure_borrower_contacts(
    session: AsyncSession,
    *,
    active_entity: Entity,
    overdue_entity: Entity,
    closure_entity: Entity,
) -> None:
    await ensure_entity_contact(
        session,
        active_entity,
        contact_type=ContactType.AUTHORIZED_SIGNATORY,
        first_name="UAT",
        last_name="Borrower",
        designation="Chief Financial Officer",
        email=PORTAL_EMAIL,
        mobile="9876501234",
        pan="AAIPB0001A",
        din="10000001",
        is_primary=True,
        is_authorized_signatory=True,
        shareholding_percentage=money("12.50"),
    )
    await ensure_entity_contact(
        session,
        active_entity,
        contact_type=ContactType.DIRECTOR,
        first_name="Anita",
        last_name="Deshmukh",
        designation="Managing Director",
        email="anita.deshmukh@uatcoastal.example.com",
        mobile="9876501235",
        pan="AAIPD0002B",
        din="10000002",
        is_primary=False,
        is_authorized_signatory=True,
        shareholding_percentage=money("26.00"),
    )
    await ensure_entity_contact(
        session,
        overdue_entity,
        contact_type=ContactType.AUTHORIZED_SIGNATORY,
        first_name="Rohit",
        last_name="Menon",
        designation="Finance Controller",
        email="rohit.menon@uatinland.example.com",
        mobile="9876502234",
        pan="AAIPM0003C",
        din="10000003",
        is_primary=True,
        is_authorized_signatory=True,
        shareholding_percentage=money("8.00"),
    )
    await ensure_entity_contact(
        session,
        closure_entity,
        contact_type=ContactType.AUTHORIZED_SIGNATORY,
        first_name="Meera",
        last_name="Nair",
        designation="Company Secretary",
        email="meera.nair@uatshipyard.example.com",
        mobile="9876503234",
        pan="AAIPN0004D",
        din="10000004",
        is_primary=True,
        is_authorized_signatory=True,
        shareholding_percentage=money("5.00"),
    )


async def ensure_application(
    session: AsyncSession,
    org: Organization,
    entity: Entity,
    product: LoanProduct,
    *,
    number: str,
    amount: Decimal,
    stage: ApplicationStage,
    status: ApplicationStatus,
    project_name: str,
) -> LoanApplication:
    app = await scalar_one_or_none(
        session,
        select(LoanApplication).where(
            LoanApplication.organization_id == org.id,
            LoanApplication.application_number == number,
        ),
    )
    if not app:
        project_cost = (amount * Decimal("1.35")).quantize(Decimal("0.01"))
        app = LoanApplication(
            organization_id=org.id,
            application_number=number,
            entity_id=entity.id,
            product_id=product.id,
            requested_amount=amount,
            requested_tenure_months=84,
            purpose=f"Project finance for {project_name}",
            detailed_purpose="Manual UAT lifecycle coverage: appraisal, sanction, tranche disbursement, schedule, receipt, overdue and closure.",
            is_project_finance=True,
            project_name=project_name,
            project_cost=project_cost,
            promoter_contribution=(amount * Decimal("0.25")).quantize(Decimal("0.01")),
            promoter_contribution_pct=money("25.00"),
            bank_finance=amount,
            project_location="Maharashtra",
            project_start_date=today() - timedelta(days=180),
            project_completion_date=add_months(today(), 18),
            preferred_interest_type=InterestType.FLOATING,
            preferred_repayment_frequency=RepaymentFrequency.QUARTERLY,
            preferred_repayment_mode=product.default_repayment_mode,
            requested_moratorium_months=6,
            stage=stage,
            status=status,
            application_date=today() - timedelta(days=75),
            submission_date=today() - timedelta(days=70),
            expected_decision_date=today() - timedelta(days=35),
            decision_date=(
                today() - timedelta(days=25) if status == ApplicationStatus.SANCTIONED else None
            ),
            entity_rating_at_application=entity.internal_rating,
            source_channel="DIRECT",
            remarks="Seeded by manual-lending UAT script.",
            extra_data={
                "scheme_status": (
                    "LENDER_REVIEW" if status == ApplicationStatus.SUBMITTED else "SANCTION_ISSUED"
                )
            },
        )
        session.add(app)
        await session.flush()
    await ensure_application_iif_details(session, org, app, amount)
    return app


async def ensure_application_iif_details(
    session: AsyncSession,
    org: Organization,
    app: LoanApplication,
    amount: Decimal,
) -> None:
    await session.execute(
        delete(ApplicationFundingSource).where(
            ApplicationFundingSource.organization_id == org.id,
            ApplicationFundingSource.application_id == app.id,
        )
    )
    project_cost = app.project_cost or (amount * Decimal("1.35")).quantize(Decimal("0.01"))
    funding_rows = [
        ("EQUITY_SHARE_CAPITAL", "Equity share capital", money("30000000")),
        ("PROMOTER_CONTRIBUTION", "Promoter contribution", money("20000000")),
        ("BANK_TERM_LOAN", "Bank / FI term loan", amount),
        ("INTERNAL_ACCRUALS", "Internal accruals", project_cost - amount - money("50000000")),
    ]
    for source_code, source_label, source_amount in funding_rows:
        session.add(
            ApplicationFundingSource(
                organization_id=org.id,
                application_id=app.id,
                source_code=source_code,
                source_label=source_label,
                amount=source_amount,
                remarks="Seeded for IIF project funding composition demo.",
            )
        )

    await session.execute(
        delete(ApplicationLenderLoan).where(
            ApplicationLenderLoan.organization_id == org.id,
            ApplicationLenderLoan.application_id == app.id,
        )
    )
    session.add(
        ApplicationLenderLoan(
            organization_id=org.id,
            application_id=app.id,
            loan_type="Term Loan",
            loan_amount=amount,
            lender_name="UAT National Bank",
            lender_category="Bank",
            lender_contact="Credit Desk",
            lender_email="creditdesk@uatnationalbank.example.com",
            lender_address="Mumbai Corporate Banking Branch",
            lender_state="Maharashtra",
            lender_district="Mumbai",
            lender_pincode="400001",
            sanction_reference=f"{app.application_number}/SANCTION",
            sanction_date=today() - timedelta(days=30),
            interest_rate_percent=money("10.75"),
            emi_periodicity="Quarterly",
            interest_debiting_periodicity="Monthly",
            loan_account_number="UATBNKTL0001",
            ifsc_code="UTNB0000001",
            security_type="First charge on project assets",
            disbursement_call_type="Tranche based",
            emi_amount=money("18500000"),
            emi_due_date=add_months(today(), 3),
            lender_validation_status="VALIDATED",
            lender_validation_remarks="Seeded lender validation for client demo.",
            lender_validated_at=datetime.now(UTC) - timedelta(days=20),
        )
    )
    await session.flush()


async def ensure_sanction(
    session: AsyncSession,
    org: Organization,
    app: LoanApplication,
    entity: Entity,
    product: LoanProduct,
    *,
    number: str,
    amount: Decimal,
    status: SanctionStatus,
    max_tranches: int,
) -> LoanSanction:
    sanction = await scalar_one_or_none(
        session,
        select(LoanSanction).where(
            LoanSanction.organization_id == org.id,
            LoanSanction.sanction_number == number,
        ),
    )
    if not sanction:
        sanction = LoanSanction(
            organization_id=org.id,
            application_id=app.id,
            entity_id=entity.id,
            product_id=product.id,
            sanction_number=number,
            sanction_letter_number=f"{number}/SL",
            sanction_date=today() - timedelta(days=25),
            validity_date=today() + timedelta(days=180),
            first_disbursement_deadline=today() + timedelta(days=90),
            sanctioned_amount=amount,
            requested_amount=app.requested_amount,
            approved_project_cost=app.project_cost,
            tenure_months=84,
            moratorium_months=6,
            moratorium_type="INTEREST_ONLY",
            interest_type=InterestType.FLOATING,
            base_rate_at_sanction=money("8.25"),
            spread_bps=275,
            effective_rate=money("11.00"),
            penal_interest_rate=money("2.00"),
            repayment_frequency=RepaymentFrequency.QUARTERLY,
            repayment_mode=product.default_repayment_mode,
            repayment_start_date=add_months(today(), 3),
            day_count_convention=DayCountConvention.ACT_365,
            allows_prepayment=True,
            prepayment_lock_in_months=12,
            prepayment_penalty_rate=money("1.00"),
            allows_foreclosure=True,
            foreclosure_penalty_rate=money("1.00"),
            disbursement_type="TRANCHE_BASED",
            max_tranches=max_tranches,
            status=status,
            approval_authority="UAT Credit Committee",
            approval_reference=f"UAT/CC/{today().year}/001",
            acceptance_required=True,
            acceptance_deadline=today() + timedelta(days=30),
            accepted_at=(
                datetime.now(UTC) - timedelta(days=20)
                if status in {SanctionStatus.ACCEPTED, SanctionStatus.ACTIVE}
                else None
            ),
            entity_rating=entity.internal_rating,
            special_terms="Manual recording of disbursements and receipts; no external integrations.",
            remarks="Seeded by manual-lending UAT script.",
        )
        session.add(sanction)
        await session.flush()

    security = await scalar_one_or_none(
        session,
        select(LoanSecurity).where(
            LoanSecurity.sanction_id == sanction.id,
            LoanSecurity.security_number == 1,
        ),
    )
    if not security:
        session.add(
            LoanSecurity(
                sanction_id=sanction.id,
                security_number=1,
                security_code=f"SEC-{number[-3:]}",
                security_category=SecurityCategory.PRIMARY,
                security_type=SecurityType.IMMOVABLE_PROPERTY,
                charge_type=ChargeType.FIRST,
                description="Mortgage over project land and terminal assets",
                property_address="UAT project site, Maharashtra",
                owner_name=entity.legal_name,
                declared_value=(amount * Decimal("1.50")).quantize(Decimal("0.01")),
                market_value=(amount * Decimal("1.45")).quantize(Decimal("0.01")),
                acceptable_value=(amount * Decimal("1.25")).quantize(Decimal("0.01")),
                margin_percentage=money("20.00"),
                net_value=amount,
                valuation_date=today() - timedelta(days=30),
                valuer_name="UAT Valuers LLP",
                status=SecurityStatus.REGISTERED,
                cersai_id=f"MANUAL-CERSAI-{number[-3:]}",
                cersai_registration_date=today() - timedelta(days=18),
            )
        )
    return sanction


async def ensure_account(
    session: AsyncSession,
    org: Organization,
    sanction: LoanSanction,
    entity: Entity,
    product: LoanProduct,
    *,
    number: str,
    status: LoanAccountStatus,
    disbursed: Decimal,
    principal_outstanding: Decimal,
    interest_overdue: Decimal = money("0"),
    principal_overdue: Decimal = money("0"),
    dpd: int = 0,
    asset_classification: AssetClassification = AssetClassification.STANDARD,
    closure_date: date | None = None,
) -> LoanAccount:
    gl_accounts = await get_lending_gl_accounts(session, org)
    account = await scalar_one_or_none(
        session,
        select(LoanAccount).where(LoanAccount.loan_account_number == number),
    )
    if not account:
        account = LoanAccount(
            organization_id=org.id,
            sanction_id=sanction.id,
            entity_id=entity.id,
            product_id=product.id,
            loan_account_number=number,
            loan_reference_number=f"REF-{number[-3:]}",
            account_open_date=today() - timedelta(days=20),
            first_disbursement_date=today() - timedelta(days=15) if disbursed else None,
            last_disbursement_date=today() - timedelta(days=10) if disbursed else None,
            repayment_start_date=add_months(today(), -2),
            maturity_date=add_months(today(), 82),
            sanctioned_amount=sanction.sanctioned_amount,
            tenure_months=sanction.tenure_months,
            moratorium_months=sanction.moratorium_months,
            moratorium_end_date=add_months(today() - timedelta(days=20), 6),
            interest_type=sanction.interest_type,
            current_base_rate=sanction.base_rate_at_sanction,
            spread_bps=sanction.spread_bps,
            current_interest_rate=sanction.effective_rate,
            penal_interest_rate=sanction.penal_interest_rate,
            repayment_frequency=sanction.repayment_frequency,
            repayment_mode=sanction.repayment_mode,
            day_count_convention=sanction.day_count_convention,
            installment_day=5,
            current_emi_amount=money("8750000"),
            total_disbursed_amount=disbursed,
            undisbursed_amount=sanction.sanctioned_amount - disbursed,
            principal_outstanding=principal_outstanding,
            interest_outstanding=money("0"),
            interest_overdue=interest_overdue,
            principal_overdue=principal_overdue,
            penal_interest_outstanding=money("250000") if dpd else money("0"),
            charges_outstanding=money("0"),
            total_outstanding=principal_outstanding + interest_overdue + principal_overdue,
            total_principal_received=(
                disbursed - principal_outstanding
                if disbursed > principal_outstanding
                else money("0")
            ),
            total_interest_received=(
                money("18500000") if status != LoanAccountStatus.CREATED else money("0")
            ),
            days_past_due=dpd,
            oldest_due_date=today() - timedelta(days=dpd) if dpd else None,
            asset_classification=asset_classification,
            npa_date=today() - timedelta(days=dpd - 90) if dpd > 90 else None,
            npa_amount=principal_outstanding if dpd > 90 else money("0"),
            provision_percentage=money("15.00") if dpd > 90 else money("0.40"),
            provision_amount=(
                principal_outstanding * (Decimal("0.15") if dpd > 90 else Decimal("0.004"))
            ).quantize(Decimal("0.01")),
            provision_held=(
                principal_outstanding * (Decimal("0.12") if dpd > 90 else Decimal("0.004"))
            ).quantize(Decimal("0.01")),
            accrual_suspended=dpd > 90,
            accrual_suspension_date=today() - timedelta(days=dpd - 90) if dpd > 90 else None,
            closure_date=closure_date,
            status=status,
            loan_asset_account_id=gl_accounts.get("loan_asset"),
            interest_receivable_account_id=gl_accounts.get("interest_receivable"),
            interest_income_account_id=gl_accounts.get("interest_income"),
            penal_interest_income_account_id=gl_accounts.get("penal_interest_income"),
            charges_income_account_id=gl_accounts.get("charges_income"),
            receipt_suspense_account_id=gl_accounts.get("receipt_suspense"),
            remarks="Seeded by manual-lending UAT script.",
        )
        session.add(account)
        await session.flush()
    else:
        account.loan_asset_account_id = gl_accounts.get("loan_asset")
        account.interest_receivable_account_id = gl_accounts.get("interest_receivable")
        account.interest_income_account_id = gl_accounts.get("interest_income")
        account.penal_interest_income_account_id = gl_accounts.get("penal_interest_income")
        account.charges_income_account_id = gl_accounts.get("charges_income")
        account.receipt_suspense_account_id = gl_accounts.get("receipt_suspense")
    return account


async def ensure_disbursement(
    session: AsyncSession,
    account: LoanAccount,
    *,
    sequence: int,
    amount: Decimal,
    status: DisbursementStatus,
) -> Disbursement:
    gl_accounts = await get_lending_gl_accounts(session, account.organization)
    disbursement = await scalar_one_or_none(
        session,
        select(Disbursement).where(
            Disbursement.loan_account_id == account.id,
            Disbursement.disbursement_number == sequence,
        ),
    )
    if not disbursement:
        disbursement = Disbursement(
            loan_account_id=account.id,
            disbursement_number=sequence,
            disbursement_reference=f"UAT-DISB-{account.loan_account_number[-3:]}-{sequence}",
            requested_amount=amount,
            approved_amount=amount if status != DisbursementStatus.PENDING else None,
            disbursed_amount=amount if status == DisbursementStatus.PROCESSED else None,
            disbursement_charges=money("0"),
            net_disbursement=amount if status == DisbursementStatus.PROCESSED else None,
            request_date=today() - timedelta(days=18),
            approval_date=(
                today() - timedelta(days=16) if status != DisbursementStatus.PENDING else None
            ),
            scheduled_date=(
                today() + timedelta(days=5)
                if status == DisbursementStatus.PENDING
                else today() - timedelta(days=14)
            ),
            disbursement_date=(
                today() - timedelta(days=14) if status == DisbursementStatus.PROCESSED else None
            ),
            value_date=(
                today() - timedelta(days=14) if status == DisbursementStatus.PROCESSED else None
            ),
            disbursement_mode=DisbursementMode.RTGS,
            source_account_id=(
                gl_accounts.get("source_bank") if status == DisbursementStatus.PROCESSED else None
            ),
            beneficiary_name=account.entity.legal_name if account.entity else "UAT Borrower",
            beneficiary_account_number="1234567890123456",
            beneficiary_ifsc="SBIN0001234",
            beneficiary_bank="State Bank of India",
            utr_number=(
                f"UTRUAT{account.loan_account_number[-3:]}{sequence}"
                if status == DisbursementStatus.PROCESSED
                else None
            ),
            purpose="Manual tranche disbursement UAT",
            conditions_verified=status != DisbursementStatus.PENDING,
            conditions_verified_at=(
                datetime.now(UTC) - timedelta(days=16)
                if status != DisbursementStatus.PENDING
                else None
            ),
            status=status,
            approved_at=(
                datetime.now(UTC) - timedelta(days=16)
                if status != DisbursementStatus.PENDING
                else None
            ),
            processed_at=(
                datetime.now(UTC) - timedelta(days=14)
                if status == DisbursementStatus.PROCESSED
                else None
            ),
            remarks="Manual UAT disbursement; no bank integration.",
        )
        session.add(disbursement)
        await session.flush()
    elif status == DisbursementStatus.PROCESSED:
        disbursement.source_account_id = gl_accounts.get("source_bank")
    return disbursement


async def ensure_schedule_and_receipt(
    session: AsyncSession,
    org: Organization,
    account: LoanAccount,
    *,
    overdue: bool,
) -> None:
    schedule = await scalar_one_or_none(
        session,
        select(RepaymentSchedule).where(
            RepaymentSchedule.loan_account_id == account.id,
            RepaymentSchedule.schedule_number == 1,
        ),
    )
    if not schedule:
        schedule = RepaymentSchedule(
            loan_account_id=account.id,
            schedule_number=1,
            schedule_type=ScheduleType.ORIGINAL,
            principal_amount=account.total_disbursed_amount or account.sanctioned_amount,
            interest_rate=account.current_interest_rate,
            tenure_months=account.tenure_months,
            emi_amount=account.current_emi_amount,
            effective_date=account.account_open_date,
            first_installment_date=add_months(account.account_open_date, 1),
            last_installment_date=add_months(account.account_open_date, 12),
            total_installments=12,
            total_principal=account.total_disbursed_amount or account.sanctioned_amount,
            total_interest=money("48000000"),
            is_current=True,
            remarks="UAT schedule for manual installment validation.",
        )
        session.add(schedule)
        await session.flush()

    existing_installments = (
        (
            await session.execute(
                select(ScheduleInstallment).where(ScheduleInstallment.schedule_id == schedule.id)
            )
        )
        .scalars()
        .all()
    )
    if not existing_installments:
        opening = account.total_disbursed_amount or account.sanctioned_amount
        principal = (opening / Decimal("12")).quantize(Decimal("0.01"))
        interest = money("1200000")
        for idx in range(1, 5):
            due_date = add_months(today(), idx - 3)
            is_past = due_date < today()
            paid = is_past and not overdue
            status = (
                InstallmentStatus.PAID
                if paid
                else InstallmentStatus.OVERDUE if is_past and overdue else InstallmentStatus.DUE
            )
            session.add(
                ScheduleInstallment(
                    schedule_id=schedule.id,
                    installment_number=idx,
                    due_date=due_date,
                    principal_amount=principal,
                    interest_amount=interest,
                    emi_amount=principal + interest,
                    opening_balance=opening - (principal * (idx - 1)),
                    closing_balance=opening - (principal * idx),
                    principal_paid=principal if paid else money("0"),
                    interest_paid=interest if paid else money("0"),
                    principal_overdue=(
                        principal if status == InstallmentStatus.OVERDUE else money("0")
                    ),
                    interest_overdue=(
                        interest if status == InstallmentStatus.OVERDUE else money("0")
                    ),
                    status=status,
                    paid_date=due_date + timedelta(days=2) if paid else None,
                )
            )
        await session.flush()

    first_installment = await scalar_one_or_none(
        session,
        select(ScheduleInstallment)
        .where(ScheduleInstallment.schedule_id == schedule.id)
        .order_by(ScheduleInstallment.installment_number.asc())
        .limit(1),
    )

    receipt = await scalar_one_or_none(
        session,
        select(LoanReceipt).where(
            LoanReceipt.organization_id == org.id,
            LoanReceipt.receipt_number == f"UAT-RCPT-{account.loan_account_number[-3:]}-001",
        ),
    )
    if not receipt and account.status != LoanAccountStatus.CREATED:
        amount = money("9950000")
        gl_accounts = await get_lending_gl_accounts(session, org)
        receipt = LoanReceipt(
            organization_id=org.id,
            loan_account_id=account.id,
            receipt_number=f"UAT-RCPT-{account.loan_account_number[-3:]}-001",
            receipt_date=today() - timedelta(days=7),
            value_date=today() - timedelta(days=7),
            receipt_amount=amount,
            receipt_type=ReceiptType.REGULAR,
            receipt_mode=ReceiptMode.NEFT,
            instrument_number=f"UTRRCPT{account.loan_account_number[-3:]}001",
            instrument_date=today() - timedelta(days=7),
            instrument_bank="HDFC Bank",
            receipt_account_id=gl_accounts.get("source_bank"),
            receipt_suspense_account_id=account.receipt_suspense_account_id,
            allocated_amount=amount - money("250000") if overdue else amount,
            unallocated_amount=money("250000") if overdue else money("0"),
            principal_allocated=money("7600000"),
            interest_allocated=money("2100000") if overdue else money("2350000"),
            penal_interest_allocated=money("250000") if overdue else money("0"),
            status=ReceiptStatus.ALLOCATED,
            processed_at=datetime.now(UTC) - timedelta(days=7),
            remarks="Manual UAT receipt recorded without bank-statement integration.",
        )
        session.add(receipt)
        await session.flush()
        session.add(
            ReceiptAllocation(
                receipt_id=receipt.id,
                installment_id=first_installment.id if first_installment else None,
                allocation_component=AllocationComponent.PRINCIPAL,
                allocated_amount=receipt.principal_allocated,
                allocation_sequence=1,
                remarks="UAT principal allocation",
            )
        )
        session.add(
            ReceiptAllocation(
                receipt_id=receipt.id,
                installment_id=first_installment.id if first_installment else None,
                allocation_component=AllocationComponent.INTEREST,
                allocated_amount=receipt.interest_allocated,
                allocation_sequence=2,
                remarks="UAT interest allocation",
            )
        )
    elif receipt and first_installment:
        allocations = list(
            (
                await session.execute(
                    select(ReceiptAllocation).where(ReceiptAllocation.receipt_id == receipt.id)
                )
            )
            .scalars()
            .all()
        )
        for allocation in allocations:
            allocation.installment_id = allocation.installment_id or first_installment.id


async def ensure_treasury(session: AsyncSession, org: Organization, account: LoanAccount) -> None:
    lender = await scalar_one_or_none(
        session,
        select(Lender).where(Lender.organization_id == org.id, Lender.lender_code == "UAT_SBI"),
    )
    if not lender:
        lender = Lender(
            organization_id=org.id,
            lender_code="UAT_SBI",
            lender_name="State Bank of India - UAT Funding Line",
            lender_type=LenderType.BANK.value,
            status=LenderStatus.ACTIVE.value,
            contact_person="Treasury Relationship Manager",
            contact_email="uat.treasury@sbi.example",
            contact_phone="02240001000",
            total_sanction_limit=money("1500000000"),
            available_limit=money("850000000"),
            external_rating="AAA",
            rating_agency="CRISIL",
            rating_date=today() - timedelta(days=60),
            remarks="Manual source lender for UAT treasury spread visibility.",
            updated_at=datetime.now(UTC),
        )
        session.add(lender)
        await session.flush()

    borrowing = await scalar_one_or_none(
        session,
        select(Borrowing).where(
            Borrowing.organization_id == org.id,
            Borrowing.borrowing_number == "UAT-BORR-SBI-001",
        ),
    )
    if not borrowing:
        borrowing = Borrowing(
            organization_id=org.id,
            lender_id=lender.id,
            borrowing_number="UAT-BORR-SBI-001",
            borrowing_type=BorrowingType.TERM_LOAN.value,
            sanctioned_amount=money("650000000"),
            drawn_amount=money("450000000"),
            principal_outstanding=money("425000000"),
            available_amount=money("200000000"),
            sanction_date=today() - timedelta(days=120),
            maturity_date=add_months(today(), 54),
            tenure_months=60,
            rate_type=BorrowingRateType.FLOATING.value,
            base_rate_name="REPO",
            base_rate_value=money("7.25"),
            spread_bps=125,
            effective_rate=money("8.50"),
            interest_payment_frequency=RepaymentFrequency.QUARTERLY.value,
            principal_payment_frequency=RepaymentFrequency.QUARTERLY.value,
            first_interest_date=add_months(today() - timedelta(days=90), 3),
            first_principal_date=add_months(today() - timedelta(days=90), 6),
            security_type=BorrowingSecurityType.HYPOTHECATION.value,
            security_description="Hypothecation of eligible book debts",
            status=BorrowingStatus.ACTIVE.value,
            remarks="Manual source-of-funds record; no lender portal integration.",
            updated_at=datetime.now(UTC),
        )
        session.add(borrowing)
        await session.flush()

    tranche = await scalar_one_or_none(
        session,
        select(BorrowingTranche).where(
            BorrowingTranche.borrowing_id == borrowing.id,
            BorrowingTranche.tranche_number == 1,
        ),
    )
    if not tranche:
        tranche = BorrowingTranche(
            borrowing_id=borrowing.id,
            tranche_number=1,
            request_date=today() - timedelta(days=95),
            requested_amount=money("450000000"),
            purpose="UAT lending deployment",
            disbursement_date=today() - timedelta(days=90),
            disbursed_amount=money("450000000"),
            principal_outstanding=money("425000000"),
            effective_rate=money("8.50"),
            utr_number="UTRUATBORR001",
            status=DrawdownStatus.DISBURSED.value,
            remarks="Manual borrowing drawdown used for UAT spread calculations.",
            updated_at=datetime.now(UTC),
        )
        session.add(tranche)
        await session.flush()

    schedule = await scalar_one_or_none(
        session,
        select(BorrowingSchedule).where(
            BorrowingSchedule.borrowing_id == borrowing.id,
            BorrowingSchedule.installment_number == 1,
        ),
    )
    if not schedule:
        session.add(
            BorrowingSchedule(
                borrowing_id=borrowing.id,
                tranche_id=tranche.id,
                installment_number=1,
                due_date=add_months(today(), 1),
                principal_due=money("0"),
                interest_due=money("9562500"),
                total_due=money("9562500"),
                opening_balance=money("425000000"),
                closing_balance=money("425000000"),
                status="DUE",
                updated_at=datetime.now(UTC),
            )
        )

    deployment = await scalar_one_or_none(
        session,
        select(FundDeployment).where(
            FundDeployment.borrowing_id == borrowing.id,
            FundDeployment.loan_account_id == account.id,
        ),
    )
    if not deployment:
        session.add(
            FundDeployment(
                organization_id=org.id,
                borrowing_id=borrowing.id,
                borrowing_tranche_id=tranche.id,
                loan_account_id=account.id,
                deployment_reference="UAT-FD-001",
                allocation_date=today() - timedelta(days=15),
                allocated_amount=money("250000000"),
                cost_rate=money("8.50"),
                lending_rate=account.current_interest_rate,
                spread_bps=money("250"),
                allocation_basis={"mode": "manual", "notes": "UAT source-of-funds linkage"},
                status="ACTIVE",
                remarks="Manual mapping between borrowing drawdown and lending asset.",
                updated_at=datetime.now(UTC),
            )
        )

    investment = await scalar_one_or_none(
        session,
        select(TreasuryInvestment).where(
            TreasuryInvestment.organization_id == org.id,
            TreasuryInvestment.investment_number == "UAT-INV-GSEC-001",
        ),
    )
    if not investment:
        session.add(
            TreasuryInvestment(
                organization_id=org.id,
                investment_number="UAT-INV-GSEC-001",
                type=InvestmentType.GSEC.value,
                category=InvestmentCategory.HTM.value,
                issuer="Government of India",
                description="UAT 10-year G-Sec liquidity buffer",
                isin="IN000UAT0010",
                face_value=money("1000000"),
                purchase_price=money("995000"),
                units=Decimal("100.0000"),
                coupon_rate=money("7.10"),
                ytm=money("7.25"),
                coupon_frequency=CouponFrequency.SEMI_ANNUAL.value,
                purchase_date=today() - timedelta(days=75),
                maturity_date=add_months(today(), 120),
                broker="Manual Treasury Desk",
                remarks="Manual UAT treasury investment; no market-data integration.",
                status=InvestmentStatus.ACTIVE.value,
                current_value=money("100250000"),
                accrued_interest=money("1450000"),
                updated_at=datetime.now(UTC),
            )
        )


async def ensure_iif_basics(
    session: AsyncSession,
    org: Organization,
    account: LoanAccount,
) -> None:
    category = await scalar_one_or_none(
        session,
        select(FundUtilizationCategory).where(
            FundUtilizationCategory.organization_id == org.id,
            FundUtilizationCategory.code == "UAT_PORT_INFRA",
        ),
    )
    if not category:
        category = FundUtilizationCategory(
            organization_id=org.id,
            code="UAT_PORT_INFRA",
            label="UAT Port Infrastructure",
            description="UAT utilization bucket for maritime infrastructure lending.",
            sort_order=1,
        )
        session.add(category)
        await session.flush()

    scheme = await scalar_one_or_none(
        session,
        select(SubventionScheme).where(
            SubventionScheme.organization_id == org.id,
            SubventionScheme.scheme_code == "UAT_IIF_2026",
        ),
    )
    if not scheme:
        scheme = SubventionScheme(
            organization_id=org.id,
            scheme_code="UAT_IIF_2026",
            scheme_name="UAT Interest Incentivization Fund 2026",
            administering_ministry="Ministry of Ports, Shipping and Waterways",
            implementing_agency="Sagarmala Finance Corporation Limited",
            description="Manual UAT scheme data; no ministry portal integration.",
            subvention_rate_percent=money("3.00"),
            max_subvention_per_beneficiary=money("10000000000"),
            scheme_corpus=money("50000000000"),
            eligible_loan_types=[IIFLoanType.TERM_LOAN_CAPEX.value],
            max_tenure_term_loan_months=120,
            max_tenure_working_capital_months=36,
            scheme_start_date=date(2026, 4, 1),
            scheme_end_date=date(2027, 3, 31),
            eligibility_window_months=36,
            claim_frequency=ClaimFrequency.QUARTERLY.value,
            npa_disqualification_dpd_days=30,
        )
        session.add(scheme)
        await session.flush()

    enrollment = await scalar_one_or_none(
        session,
        select(LoanSubventionEnrollment).where(
            LoanSubventionEnrollment.organization_id == org.id,
            LoanSubventionEnrollment.loan_account_id == account.id,
            LoanSubventionEnrollment.scheme_id == scheme.id,
        ),
    )
    if not enrollment:
        enrollment = LoanSubventionEnrollment(
            organization_id=org.id,
            loan_account_id=account.id,
            scheme_id=scheme.id,
            enrolled_date=date(2026, 4, 1),
            status=SubventionEnrollmentStatus.ENROLLED.value,
            total_claimed_to_date=money("5625000"),
            total_paid_to_date=money("0"),
            notes="Seeded manual UAT IIF enrollment for detail-screen coverage.",
        )
        session.add(enrollment)
        await session.flush()

    claim_documents = [
        {
            "name": str(doc.get("label") or doc.get("code")),
            "file_name": f"{str(doc.get('code')).lower()}.pdf",
            "document_category": str(doc.get("code")),
            "path": f"/manual-uat/iif/{str(doc.get('code')).lower()}.pdf",
            "uploaded_at": now_utc().isoformat(),
        }
        for doc in DEFAULT_REQUIRED_DOCUMENTS
        if str(doc.get("stage", "")).upper() == "CLAIM_SUBMISSION"
    ]
    claim = await scalar_one_or_none(
        session,
        select(SubventionClaim).where(
            SubventionClaim.organization_id == org.id,
            SubventionClaim.claim_reference == "UAT/IIF/2026Q1/00001",
        ),
    )
    if not claim:
        session.add(
            SubventionClaim(
                organization_id=org.id,
                enrollment_id=enrollment.id,
                claim_reference="UAT/IIF/2026Q1/00001",
                period_start=date(2026, 4, 1),
                period_end=date(2026, 6, 30),
                claim_frequency=ClaimFrequency.QUARTERLY.value,
                interest_paid_in_period=money("187500000"),
                applicable_subvention_amount=money("5625000"),
                status=SubventionClaimStatus.DRAFT.value,
                documents=claim_documents,
            )
        )
    else:
        claim.documents = claim_documents
        if claim.status == SubventionClaimStatus.REJECTED.value:
            claim.status = SubventionClaimStatus.DRAFT.value
            claim.rejection_reason = None


async def ensure_workflow_definitions(session: AsyncSession, org: Organization) -> None:
    workflow = await scalar_one_or_none(
        session,
        select(WorkflowDefinition).where(
            WorkflowDefinition.organization_id == org.id,
            WorkflowDefinition.code == "UAT_LOAN_SANCTION_APPROVAL",
        ),
    )
    if not workflow:
        session.add(
            WorkflowDefinition(
                organization_id=org.id,
                name="UAT Loan Sanction Approval",
                code="UAT_LOAN_SANCTION_APPROVAL",
                description="Manual maker-checker workflow for UAT loan sanctions.",
                entity_type=WorkflowEntityType.LOAN_SANCTION,
                is_default=True,
                priority=100,
                activation_conditions={"mode": "manual", "minAmount": "0"},
                allow_parallel_branches=False,
                require_comments_on_reject=True,
                notify_initiator_on_complete=True,
                allow_withdrawal=True,
                version=1,
                updated_at=datetime.now(UTC),
            )
        )


async def ensure_portal_user(
    session: AsyncSession,
    org: Organization,
    borrower_entity: Entity,
    *,
    reset_password: bool,
) -> PortalUser:
    user = await scalar_one_or_none(
        session,
        select(PortalUser).where(
            PortalUser.organization_id == org.id,
            PortalUser.email == PORTAL_EMAIL,
        ),
    )
    if not user:
        user = PortalUser(
            organization_id=org.id,
            mobile="9876501234",
            mobile_verified=True,
            mobile_verified_at=now_naive(),
            email=PORTAL_EMAIL,
            email_verified=True,
            email_verified_at=now_naive(),
            status=PortalUserStatus.ACTIVE,
            registration_status=PortalRegistrationStatus.ACTIVE,
            actor_role=PortalActorRole.SCHEME_BORROWER,
            registration_requested_pan=borrower_entity.pan,
            registration_authorized_signatory_name="UAT Borrower Portal User",
            registered_at=now_utc() - timedelta(days=30),
            approved_at=now_utc() - timedelta(days=20),
            registration_reference="REG/UAT/000001",
            password_hash=get_password_hash(PORTAL_PASSWORD),
            password_changed_at=now_utc(),
            activated_at=now_utc(),
            preferred_language="en",
        )
        session.add(user)
        await session.flush()
    elif reset_password:
        user.password_hash = get_password_hash(PORTAL_PASSWORD)
        user.status = PortalUserStatus.ACTIVE
        user.registration_status = PortalRegistrationStatus.ACTIVE
        user.actor_role = PortalActorRole.SCHEME_BORROWER
        user.locked_until = None
        user.failed_login_attempts = 0

    link = await scalar_one_or_none(
        session,
        select(PortalUserEntity).where(
            PortalUserEntity.portal_user_id == user.id,
            PortalUserEntity.entity_id == borrower_entity.id,
            PortalUserEntity.organization_id == org.id,
        ),
    )
    if not link:
        session.add(
            PortalUserEntity(
                portal_user_id=user.id,
                entity_id=borrower_entity.id,
                organization_id=org.id,
                granted_at=now_utc() - timedelta(days=20),
                is_link_active=True,
            )
        )
    return user


async def ensure_portal_admin_user(
    session: AsyncSession,
    org: Organization,
    *,
    reset_password: bool,
) -> PortalUser:
    user = await scalar_one_or_none(
        session,
        select(PortalUser).where(
            PortalUser.organization_id == org.id,
            PortalUser.email == PORTAL_ADMIN_EMAIL,
        ),
    )
    if not user:
        user = PortalUser(
            organization_id=org.id,
            mobile="9876501299",
            mobile_verified=True,
            mobile_verified_at=now_naive(),
            email=PORTAL_ADMIN_EMAIL,
            email_verified=True,
            email_verified_at=now_naive(),
            status=PortalUserStatus.ACTIVE,
            registration_status=PortalRegistrationStatus.ACTIVE,
            actor_role=PortalActorRole.SCHEME_ADMIN,
            registration_authorized_signatory_name="UAT SFC Portal Admin",
            registered_at=now_utc() - timedelta(days=30),
            approved_at=now_utc() - timedelta(days=20),
            registration_reference="REG/UAT/ADMIN/000001",
            password_hash=get_password_hash(PORTAL_ADMIN_PASSWORD),
            password_changed_at=now_utc(),
            activated_at=now_utc(),
            preferred_language="en",
        )
        session.add(user)
        await session.flush()
    else:
        user.status = PortalUserStatus.ACTIVE
        user.registration_status = PortalRegistrationStatus.ACTIVE
        user.actor_role = PortalActorRole.SCHEME_ADMIN
        user.locked_until = None
        user.failed_login_attempts = 0
        if reset_password:
            user.password_hash = get_password_hash(PORTAL_ADMIN_PASSWORD)
    return user


def split_contact_name(name: str | None, fallback: str) -> tuple[str, str]:
    raw = (name or fallback).strip() or "Portal User"
    parts = raw.split()
    if len(parts) == 1:
        return parts[0], "-"
    return parts[0], " ".join(parts[1:])


async def ensure_portal_link_contacts(session: AsyncSession) -> None:
    """Backfill borrower contacts for active portal-user/entity links.

    Portal access is held in ``mst_portal_user_entity``. Entity detail pages
    show ``los_entity_contact`` rows, so every active borrower portal link
    should also have an entity contact representing the actual person who logs
    in on behalf of the institution.
    """

    rows = (
        await session.execute(
            select(PortalUserEntity, PortalUser, Entity)
            .join(PortalUser, PortalUser.id == PortalUserEntity.portal_user_id)
            .join(Entity, Entity.id == PortalUserEntity.entity_id)
            .where(
                PortalUserEntity.deleted_at.is_(None),
                PortalUserEntity.is_link_active.is_(True),
                PortalUser.deleted_at.is_(None),
                Entity.deleted_at.is_(None),
            )
        )
    ).all()
    for _link, portal_user, entity in rows:
        filters = [
            EntityContact.entity_id == entity.id,
            EntityContact.deleted_at.is_(None),
        ]
        identity_filters = []
        if portal_user.email:
            identity_filters.append(EntityContact.email == portal_user.email)
        if portal_user.mobile:
            identity_filters.append(EntityContact.mobile == portal_user.mobile)
        if identity_filters:
            filters.append(or_(*identity_filters))
        else:
            first_name, last_name = split_contact_name(
                portal_user.registration_authorized_signatory_name,
                "Portal User",
            )
            filters.extend(
                [
                    EntityContact.first_name == first_name,
                    EntityContact.last_name == last_name,
                ]
            )
        existing = await scalar_one_or_none(
            session,
            select(EntityContact).where(*filters),
        )
        first_name, last_name = split_contact_name(
            portal_user.registration_authorized_signatory_name,
            portal_user.email or "Portal User",
        )
        if existing:
            existing.first_name = first_name
            existing.last_name = last_name
            existing.email = portal_user.email
            existing.mobile = portal_user.mobile
            existing.contact_type = ContactType.AUTHORIZED_SIGNATORY
            existing.designation = existing.designation or "Authorized Signatory"
            existing.is_primary = True
            existing.is_authorized_signatory = True
            existing.kyc_verified = True
            existing.is_active = True
            continue
        session.add(
            EntityContact(
                entity_id=entity.id,
                contact_type=ContactType.AUTHORIZED_SIGNATORY,
                first_name=first_name,
                last_name=last_name,
                designation="Authorized Signatory",
                email=portal_user.email,
                mobile=portal_user.mobile,
                is_primary=True,
                is_authorized_signatory=True,
                kyc_verified=True,
                remarks="Seeded from active borrower portal user/entity link.",
            )
        )
    await session.flush()


async def ensure_portal_audit_user(
    session: AsyncSession,
    org: Organization,
    portal_user: PortalUser,
) -> None:
    """Create an internal audit identity for portal-originated LOS records.

    LOS audit columns currently foreign-key to ``mst_user``. The borrower
    portal has its own auth table, so the UAT portal user needs a matching
    inactive internal identity for audit/maker references without enabling
    a second admin login.
    """
    user = await scalar_one_or_none(session, select(User).where(User.id == portal_user.id))
    if not user:
        session.add(
            User(
                id=portal_user.id,
                username=f"portal_{str(portal_user.id)[:8]}",
                email=f"portal-{portal_user.id}@audit.local",
                full_name=(
                    portal_user.registration_authorized_signatory_name
                    or portal_user.email
                    or "Portal borrower user"
                ),
                employee_code=f"PORTAL-{str(portal_user.id)[:8]}",
                password_hash=get_password_hash(f"disabled-{portal_user.id}"),
                status=UserStatus.INACTIVE.value,
                organization_id=org.id,
                must_change_password=False,
            )
        )
    else:
        user.organization_id = org.id
        user.status = UserStatus.INACTIVE.value


async def seed(reset_password: bool) -> None:
    async with async_session_factory() as session:
        org, admin = await ensure_base_access(session, reset_password=reset_password)
        await seed_lending_master_catalog(session, org.id)

        project_product = await ensure_product(
            session,
            org,
            code="UAT_PROJECT_FIN",
            name="UAT Corporate Project Finance",
            category=ProductCategory.PROJECT_FINANCE,
            repayment_mode=RepaymentMode.STRUCTURED,
        )
        term_product = await ensure_product(
            session,
            org,
            code="UAT_TERM_LOAN",
            name="UAT Corporate Term Loan",
            category=ProductCategory.TERM_LOAN,
            repayment_mode=RepaymentMode.EMI,
        )
        await ensure_active_products_have_application_checklist(session, org)
        await ensure_approval_checklist_template(session, org)

        active_entity = await ensure_entity(
            session,
            org,
            code="UATENT001",
            pan="AAACU0001A",
            legal_name="UAT Coastal Logistics Private Limited",
            rating="A-",
        )
        overdue_entity = await ensure_entity(
            session,
            org,
            code="UATENT002",
            pan="AAACU0002B",
            legal_name="UAT Inland Waterways Private Limited",
            rating="BBB",
        )
        closure_entity = await ensure_entity(
            session,
            org,
            code="UATENT003",
            pan="AAACU0003C",
            legal_name="UAT Shipyard Services Private Limited",
            rating="A",
        )
        await ensure_borrower_contacts(
            session,
            active_entity=active_entity,
            overdue_entity=overdue_entity,
            closure_entity=closure_entity,
        )

        active_app = await ensure_application(
            session,
            org,
            active_entity,
            project_product,
            number="UAT/APP/2026/001",
            amount=money("300000000"),
            stage=ApplicationStage.DISBURSED,
            status=ApplicationStatus.SANCTIONED,
            project_name="Coastal Logistics Terminal Expansion",
        )
        overdue_app = await ensure_application(
            session,
            org,
            overdue_entity,
            term_product,
            number="UAT/APP/2026/002",
            amount=money("180000000"),
            stage=ApplicationStage.DISBURSED,
            status=ApplicationStatus.SANCTIONED,
            project_name="Inland Waterways Cargo Upgrade",
        )
        closure_app = await ensure_application(
            session,
            org,
            closure_entity,
            term_product,
            number="UAT/APP/2026/003",
            amount=money("90000000"),
            stage=ApplicationStage.CLOSED,
            status=ApplicationStatus.SANCTIONED,
            project_name="Shipyard Equipment Modernization",
        )
        submitted_app = await ensure_application(
            session,
            org,
            active_entity,
            project_product,
            number="UAT/APP/2026/004",
            amount=money("125000000"),
            stage=ApplicationStage.APPRAISAL,
            status=ApplicationStatus.SUBMITTED,
            project_name="Draft Borrower Portal Pipeline Application",
        )

        active_sanction = await ensure_sanction(
            session,
            org,
            active_app,
            active_entity,
            project_product,
            number="UAT/SAN/2026/001",
            amount=money("300000000"),
            status=SanctionStatus.ACCEPTED,
            max_tranches=3,
        )
        overdue_sanction = await ensure_sanction(
            session,
            org,
            overdue_app,
            overdue_entity,
            term_product,
            number="UAT/SAN/2026/002",
            amount=money("180000000"),
            status=SanctionStatus.ACTIVE,
            max_tranches=1,
        )
        closure_sanction = await ensure_sanction(
            session,
            org,
            closure_app,
            closure_entity,
            term_product,
            number="UAT/SAN/2026/003",
            amount=money("90000000"),
            status=SanctionStatus.ACTIVE,
            max_tranches=1,
        )

        active_account = await ensure_account(
            session,
            org,
            active_sanction,
            active_entity,
            project_product,
            number="UAT-LA-2026-001",
            status=LoanAccountStatus.ACTIVE,
            disbursed=money("250000000"),
            principal_outstanding=money("232400000"),
        )
        overdue_account = await ensure_account(
            session,
            org,
            overdue_sanction,
            overdue_entity,
            term_product,
            number="UAT-LA-2026-002",
            status=LoanAccountStatus.ACTIVE,
            disbursed=money("180000000"),
            principal_outstanding=money("168500000"),
            interest_overdue=money("7200000"),
            principal_overdue=money("15000000"),
            dpd=96,
            asset_classification=AssetClassification.SUBSTANDARD,
        )
        closure_account = await ensure_account(
            session,
            org,
            closure_sanction,
            closure_entity,
            term_product,
            number="UAT-LA-2026-003",
            status=LoanAccountStatus.CLOSED,
            disbursed=money("90000000"),
            principal_outstanding=money("0"),
            closure_date=today() - timedelta(days=5),
        )

        await ensure_disbursement(
            session,
            active_account,
            sequence=1,
            amount=money("250000000"),
            status=DisbursementStatus.PROCESSED,
        )
        await ensure_disbursement(
            session,
            active_account,
            sequence=2,
            amount=money("50000000"),
            status=DisbursementStatus.PENDING,
        )
        await ensure_disbursement(
            session,
            overdue_account,
            sequence=1,
            amount=money("180000000"),
            status=DisbursementStatus.PROCESSED,
        )
        await ensure_disbursement(
            session,
            closure_account,
            sequence=1,
            amount=money("90000000"),
            status=DisbursementStatus.PROCESSED,
        )

        await ensure_schedule_and_receipt(session, org, active_account, overdue=False)
        await ensure_schedule_and_receipt(session, org, overdue_account, overdue=True)
        await ensure_schedule_and_receipt(session, org, closure_account, overdue=False)
        await ensure_treasury(session, org, active_account)
        await ensure_iif_basics(session, org, active_account)
        await ensure_workflow_definitions(session, org)
        portal_user = await ensure_portal_user(
            session, org, active_entity, reset_password=reset_password
        )
        portal_admin_user = await ensure_portal_admin_user(
            session,
            org,
            reset_password=reset_password,
        )
        await ensure_portal_link_contacts(session)
        await ensure_portal_audit_user(session, org, portal_user)
        await ensure_portal_audit_user(session, org, portal_admin_user)

        await session.commit()

    print("Manual lending UAT seed completed.")
    print(f"Admin login: {ADMIN_USERNAME} / {ADMIN_PASSWORD}")
    print(f"Portal login: {PORTAL_EMAIL} / {PORTAL_PASSWORD}")
    print(f"Portal admin login: {PORTAL_ADMIN_EMAIL} / {PORTAL_ADMIN_PASSWORD}")
    print(f"Organization: {org.code} ({org.id})")
    print(f"Admin user id: {admin.id}")
    print(f"Portal user id: {portal_user.id}")
    print(f"Portal admin user id: {portal_admin_user.id}")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--no-reset-password",
        action="store_true",
        help="Do not reset seeded admin/portal UAT passwords.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv or sys.argv[1:])
    asyncio.run(seed(reset_password=not args.no_reset_password))


if __name__ == "__main__":
    main()
