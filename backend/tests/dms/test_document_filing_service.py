"""Document filing engine tests."""

from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth.role import Permission, Role  # noqa: F401
from app.models.dms import (
    DMSDocument,
    DMSFolder,
    DocumentAccessLevel,
    DocumentFilingRule,
    DocumentStatus,
)
from app.models.masters.department import Department  # noqa: F401
from app.models.masters.unit import Unit  # noqa: F401
from app.services.dms.filing_service import (
    DEFAULT_FILING_RULES,
    DocumentFilingService,
    render_path_template,
)


def test_render_path_template_sanitizes_and_falls_back_to_entity_id():
    entity_id = uuid4()

    template = (
        "/Entities/{{ entity.entityCode }}/Loans/{{ loanAccount.accountNumber }}/Closure & Release!"
    )
    path = render_path_template(
        template,
        {"entity": {"entityCode": "ACME/../NBFC"}, "loanAccount": {}},
        entity_type="loan_account",
        entity_id=entity_id,
    )

    assert path == (
        f"/Entities/ACME-.-NBFC/Loans/loan_account-{str(entity_id)[:8]}/Closure & Release-"
    )


@pytest.mark.asyncio
async def test_default_filing_rules_cover_platform_document_catalog(
    session: AsyncSession,
    test_organization,
):
    service = DocumentFilingService(session)

    await service.ensure_default_rules(organization_id=test_organization.id)

    rules = (
        (
            await session.execute(
                select(DocumentFilingRule).where(
                    DocumentFilingRule.organization_id == test_organization.id
                )
            )
        )
        .scalars()
        .all()
    )
    rule_keys = {(rule.module, rule.document_type, rule.entity_type) for rule in rules}

    assert len(rules) >= len(DEFAULT_FILING_RULES)
    assert {
        ("LENDING", "SANCTION_LETTER", "sanction"),
        ("LENDING", "KFS", "application"),
        ("TREASURY", "DRAWDOWN_REQUEST", "lender"),
        ("HRIS", "APPOINTMENT_LETTER", "employee"),
        ("PAYROLL", "PAYSLIP", "employee"),
        ("LEGAL", "SARFAESI_13_2_NOTICE", "legal_case"),
        ("FINANCE", "AUDIT_CONFIRMATION", "financial_year"),
        ("ESS", "LEAVE_APPROVAL", "employee"),
    }.issubset(rule_keys)


@pytest.mark.asyncio
async def test_resolve_folder_creates_governed_path_idempotently(
    session: AsyncSession,
    test_organization,
    test_user,
):
    service = DocumentFilingService(session)
    entity_id = uuid4()
    context = {
        "entity": {"entityCode": "ENT-001"},
        "loanAccount": {"accountNumber": "LN-2026-0001"},
    }

    folder, path, rule = await service.resolve_folder(
        organization_id=test_organization.id,
        module="LENDING",
        document_type="SANCTION_LETTER",
        entity_type="sanction",
        entity_id=entity_id,
        context=context,
        created_by=test_user.id,
    )
    second_folder, second_path, second_rule = await service.resolve_folder(
        organization_id=test_organization.id,
        module="LENDING",
        document_type="SANCTION_LETTER",
        entity_type="sanction",
        entity_id=entity_id,
        context=context,
        created_by=test_user.id,
    )

    folder_count = (
        await session.execute(
            select(func.count(DMSFolder.id)).where(
                DMSFolder.organization_id == test_organization.id,
                DMSFolder.path == path,
            )
        )
    ).scalar_one()

    assert path == "/Entities/ENT-001/Loans/LN-2026-0001/Sanction & Agreements"
    assert folder.id == second_folder.id
    assert second_path == path
    assert folder_count == 1
    assert rule is not None
    assert second_rule is not None
    assert folder.folder_type == "entity"
    assert folder.entity_type == "sanction"
    assert folder.entity_id == entity_id
    assert rule.portal_visible is True


@pytest.mark.asyncio
async def test_file_bytes_stores_document_in_resolved_folder(
    session: AsyncSession,
    test_organization,
    test_user,
    monkeypatch,
):
    service = DocumentFilingService(session)
    entity_id = uuid4()

    async def fake_upload_document(**kwargs):
        document = DMSDocument(
            organization_id=kwargs["organization_id"],
            folder_id=kwargs["folder_id"],
            code=f"DOC-{str(uuid4())[:8]}",
            name=kwargs["name"],
            description=kwargs.get("description"),
            file_name=kwargs["file_name"],
            file_extension="pdf",
            mime_type=kwargs["mime_type"],
            file_size=kwargs["file_size"],
            storage_path=f"tests/{kwargs['file_name']}",
            storage_provider="local",
            checksum="test-checksum",
            document_type=kwargs["document_type"],
            document_subtype=kwargs.get("document_subtype"),
            status=DocumentStatus.ACTIVE,
            access_level=kwargs.get("access_level") or DocumentAccessLevel.ORGANIZATION,
            current_version=1,
            entity_type=kwargs["entity_type"],
            entity_id=kwargs["entity_id"],
            keywords=None,
            created_by=kwargs.get("created_by"),
        )
        session.add(document)
        await session.flush()
        await session.refresh(document)
        return document

    monkeypatch.setattr(service.documents, "upload_document", fake_upload_document)

    document, folder, rule = await service.file_bytes(
        organization_id=test_organization.id,
        content=b"approved sanction letter",
        file_name="sanction-letter.pdf",
        mime_type="application/pdf",
        module="LENDING",
        document_type="SANCTION_LETTER",
        document_subtype="APPROVAL",
        entity_type="sanction",
        entity_id=entity_id,
        context={
            "entity": {"entityCode": "ENT-002"},
            "loanAccount": {"accountNumber": "LN-2026-0002"},
        },
        name="Sanction Letter",
        created_by=test_user.id,
    )

    stored = await session.get(DMSDocument, document.id)

    assert rule is not None
    assert folder.path == "/Entities/ENT-002/Loans/LN-2026-0002/Sanction & Agreements"
    assert stored is not None
    assert stored.folder_id == folder.id
    assert stored.document_type == "SANCTION_LETTER"
    assert stored.document_subtype == "APPROVAL"
    assert stored.entity_type == "sanction"
    assert stored.entity_id == entity_id
    assert stored.checksum


@pytest.mark.asyncio
async def test_filing_rule_is_tenant_isolated(session: AsyncSession, test_organization):
    service = DocumentFilingService(session)
    other_org_id = uuid4()

    await service.ensure_default_rules(organization_id=test_organization.id)
    await service.ensure_default_rules(organization_id=other_org_id)

    rules = (
        (
            await session.execute(
                select(DocumentFilingRule).where(
                    DocumentFilingRule.organization_id == test_organization.id
                )
            )
        )
        .scalars()
        .all()
    )
    other_rules = (
        (
            await session.execute(
                select(DocumentFilingRule).where(DocumentFilingRule.organization_id == other_org_id)
            )
        )
        .scalars()
        .all()
    )

    assert rules
    assert other_rules
    assert {rule.organization_id for rule in rules} == {test_organization.id}
    assert {rule.organization_id for rule in other_rules} == {other_org_id}
