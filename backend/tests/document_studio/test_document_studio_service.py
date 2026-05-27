"""Enterprise Document Studio service tests."""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestException
from app.models.auth.role import Permission, Role  # noqa: F401
from app.models.dms import DMSDocument, DocumentAccessLevel, DocumentStatus
from app.models.document_studio import (
    DocumentModule,
    DocumentPackageStatus,
    DocumentTemplateStatus,
)
from app.models.masters.department import Department  # noqa: F401
from app.models.masters.unit import Unit  # noqa: F401
from app.services.document_studio_service import (
    DEFAULT_DOCUMENT_TEMPLATES,
    DocumentStudioService,
    render_template_text,
)


def test_render_template_text_replaces_variables_and_reports_missing():
    template = (
        "Dear {{ entity.legalName | uppercase }}, amount "
        "{{ sanction.sanctionedAmount | amount }} {{ sanction.validityDate }}"
    )
    rendered, missing = render_template_text(
        template,
        {
            "entity": {"legalName": "Acme Finance"},
            "sanction": {"sanctionedAmount": 1250000},
        },
    )

    assert rendered == "Dear ACME FINANCE, amount ₹ 1,250,000.00 "
    assert missing == ["sanction.validityDate"]


async def _published_sanction_template(
    service: DocumentStudioService,
    *,
    organization_id,
    user_id,
):
    template = await service.create_template(
        organization_id=organization_id,
        created_by=user_id,
        data={
            "module": DocumentModule.LENDING,
            "document_type": "SANCTION_LETTER",
            "code": "SANCTION_STD",
            "name": "Standard Sanction Letter",
            "entity_type": "sanction",
        },
    )
    version = await service.create_version(
        organization_id=organization_id,
        template_id=template.id,
        created_by=user_id,
        data={
            "body": (
                "Dear {{ entity.legalName }}, sanctioned amount is "
                "{{ sanction.sanctionedAmount | amount }}."
            ),
            "header": "{{ organization.name }}",
            "footer": "Loan {{ loanAccount.accountNumber }}",
            "required_variables": [
                "entity.legalName",
                "sanction.sanctionedAmount",
                "loanAccount.accountNumber",
            ],
        },
    )
    await service.transition_version(
        organization_id=organization_id,
        version_id=version.id,
        action="approve",
        user_id=user_id,
    )
    published = await service.transition_version(
        organization_id=organization_id,
        version_id=version.id,
        action="publish",
        user_id=user_id,
    )
    return template, published


@pytest.mark.asyncio
async def test_default_templates_seed_platform_wide_starter_catalog(
    session: AsyncSession,
    test_organization,
    test_user,
):
    service = DocumentStudioService(session)

    await service.ensure_default_templates(
        organization_id=test_organization.id,
        created_by=test_user.id,
    )
    templates = await service.list_templates(organization_id=test_organization.id)

    codes = {template.code for template in templates}
    modules = {template.module for template in templates}

    assert len(codes) >= len(DEFAULT_DOCUMENT_TEMPLATES)
    assert {
        DocumentModule.LENDING,
        DocumentModule.TREASURY,
        DocumentModule.HRIS,
        DocumentModule.PAYROLL,
        DocumentModule.LEGAL,
        DocumentModule.FINANCE,
        DocumentModule.AP_AR,
        DocumentModule.ESS,
        DocumentModule.BORROWER_PORTAL,
        DocumentModule.VENDOR_PORTAL,
    }.issubset(modules)
    assert {
        "SANCTION_LETTER_DEFAULT",
        "PAYSLIP_DEFAULT",
        "LEGAL_NOTICE_DEFAULT",
        "VENDOR_CERTIFICATE_DEFAULT",
        "ESS_LEAVE_APPROVAL_DEFAULT",
    }.issubset(codes)


@pytest.mark.asyncio
async def test_template_publish_retires_prior_published_versions(
    session: AsyncSession,
    test_organization,
    test_user,
):
    service = DocumentStudioService(session)
    template, first_version = await _published_sanction_template(
        service,
        organization_id=test_organization.id,
        user_id=test_user.id,
    )

    second_version = await service.create_version(
        organization_id=test_organization.id,
        template_id=template.id,
        created_by=test_user.id,
        data={
            "body": "Revised letter for {{ entity.legalName }}",
            "required_variables": ["entity.legalName"],
            "change_notes": "Regulatory wording update",
        },
    )
    await service.transition_version(
        organization_id=test_organization.id,
        version_id=second_version.id,
        action="approve",
        user_id=test_user.id,
    )
    await service.transition_version(
        organization_id=test_organization.id,
        version_id=second_version.id,
        action="publish",
        user_id=test_user.id,
    )

    await session.refresh(first_version)
    await session.refresh(second_version)

    assert first_version.status == DocumentTemplateStatus.RETIRED
    assert second_version.status == DocumentTemplateStatus.PUBLISHED
    assert first_version.retired_at is not None


@pytest.mark.asyncio
async def test_generate_document_files_pdf_in_dms_with_template_snapshot(
    session: AsyncSession,
    test_organization,
    test_user,
    monkeypatch,
):
    service = DocumentStudioService(session)

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

    monkeypatch.setattr(service.filing.documents, "upload_document", fake_upload_document)
    _, version = await _published_sanction_template(
        service,
        organization_id=test_organization.id,
        user_id=test_user.id,
    )
    sanction_id = uuid4()

    generated = await service.generate(
        organization_id=test_organization.id,
        user_id=test_user.id,
        data={
            "module": DocumentModule.LENDING,
            "document_type": "SANCTION_LETTER",
            "template_version_id": version.id,
            "entity_type": "sanction",
            "entity_id": sanction_id,
            "generated_from": "LOS_SANCTION",
            "business_number": "SAN-2026-0001",
            "context": {
                "organization": {"name": "SMFC NBFC"},
                "entity": {"entityCode": "ENT-100", "legalName": "Acme Finance Pvt Ltd"},
                "sanction": {"sanctionedAmount": 7500000},
                "loanAccount": {"accountNumber": "LN-2026-0100"},
            },
        },
    )

    dms_doc = await session.get(DMSDocument, generated.dms_document_id)

    assert generated.template_version == version.version_number
    assert generated.checksum
    assert generated.portal_visible is True
    assert generated.business_number == "SAN-2026-0001"
    assert "Acme Finance Pvt Ltd" in generated.render_snapshot["renderedHtml"]
    assert dms_doc is not None
    assert dms_doc.entity_type == "sanction"
    assert dms_doc.entity_id == sanction_id
    assert dms_doc.document_type == "SANCTION_LETTER"
    assert dms_doc.extracted_metadata["templateCode"] == "SANCTION_STD"
    assert dms_doc.extracted_metadata["generatedDocumentId"] == str(generated.id)


@pytest.mark.asyncio
async def test_generate_document_blocks_when_required_variables_missing(
    session: AsyncSession,
    test_organization,
    test_user,
):
    service = DocumentStudioService(session)
    _, version = await _published_sanction_template(
        service,
        organization_id=test_organization.id,
        user_id=test_user.id,
    )

    with pytest.raises(BadRequestException):
        await service.generate(
            organization_id=test_organization.id,
            user_id=test_user.id,
            data={
                "module": DocumentModule.LENDING,
                "document_type": "SANCTION_LETTER",
                "template_version_id": version.id,
                "entity_type": "sanction",
                "entity_id": uuid4(),
                "context": {
                    "organization": {"name": "SMFC NBFC"},
                    "entity": {"entityCode": "ENT-100", "legalName": "Acme Finance Pvt Ltd"},
                    "loanAccount": {"accountNumber": "LN-2026-0100"},
                },
            },
        )


@pytest.mark.asyncio
async def test_default_templates_allow_sanction_generation_without_manual_setup(
    session: AsyncSession,
    test_organization,
    test_user,
    monkeypatch,
):
    service = DocumentStudioService(session)

    async def fake_upload_document(**kwargs):
        document = DMSDocument(
            organization_id=kwargs["organization_id"],
            folder_id=kwargs["folder_id"],
            code=f"DOC-{str(uuid4())[:8]}",
            name=kwargs["name"],
            file_name=kwargs["file_name"],
            file_extension="pdf",
            mime_type=kwargs["mime_type"],
            file_size=kwargs["file_size"],
            storage_path=f"tests/{kwargs['file_name']}",
            storage_provider="local",
            checksum="test-checksum",
            document_type=kwargs["document_type"],
            status=DocumentStatus.ACTIVE,
            access_level=kwargs.get("access_level") or DocumentAccessLevel.ORGANIZATION,
            current_version=1,
            entity_type=kwargs["entity_type"],
            entity_id=kwargs["entity_id"],
            created_by=kwargs.get("created_by"),
        )
        session.add(document)
        await session.flush()
        await session.refresh(document)
        return document

    monkeypatch.setattr(service.filing.documents, "upload_document", fake_upload_document)

    generated = await service.generate(
        organization_id=test_organization.id,
        user_id=test_user.id,
        data={
            "module": DocumentModule.LENDING,
            "document_type": "SANCTION_LETTER",
            "entity_type": "sanction",
            "entity_id": uuid4(),
            "context": {
                "organization": {"name": "SMFC NBFC"},
                "entity": {"entityCode": "ENT-200", "legalName": "Default Borrower"},
                "sanction": {
                    "sanctionNumber": "SAN-2026-0200",
                    "sanctionedAmount": 100000,
                    "validityDate": "2026-07-01",
                },
                "loanAccount": {"accountNumber": "LN-200", "interestRate": 12.5},
            },
        },
    )

    assert generated.template_code == "SANCTION_LETTER_DEFAULT"
    assert generated.dms_document_id is not None


@pytest.mark.asyncio
async def test_document_package_lifecycle(
    session: AsyncSession,
    test_organization,
    test_user,
):
    service = DocumentStudioService(session)
    entity_id = uuid4()
    package = await service.create_package(
        organization_id=test_organization.id,
        created_by=test_user.id,
        data={
            "package_type": "SANCTION_PACKAGE",
            "name": "Sanction package",
            "entity_type": "sanction",
            "entity_id": entity_id,
            "manifest": {"purpose": "board-review"},
        },
    )
    dms_doc = DMSDocument(
        organization_id=test_organization.id,
        code="DOC-PKG-001",
        name="Sanction Letter",
        file_name="sanction.pdf",
        file_extension="pdf",
        mime_type="application/pdf",
        file_size=128,
        storage_path="tests/sanction.pdf",
        storage_provider="local",
        checksum="test-checksum",
        document_type="SANCTION_LETTER",
        status=DocumentStatus.ACTIVE,
        access_level=DocumentAccessLevel.ORGANIZATION,
        current_version=1,
        entity_type="sanction",
        entity_id=entity_id,
        created_by=test_user.id,
    )
    session.add(dms_doc)
    await session.flush()

    item = await service.add_package_item(
        organization_id=test_organization.id,
        package_id=package.id,
        created_by=test_user.id,
        data={
            "dms_document_id": dms_doc.id,
            "role": "PRIMARY",
            "sort_order": 1,
        },
    )
    finalized, items = await service.finalize_package(
        organization_id=test_organization.id,
        package_id=package.id,
        manifest={"approvedBy": "Credit Committee"},
        user_id=test_user.id,
    )

    assert item.role == "PRIMARY"
    assert finalized.status == DocumentPackageStatus.FINALIZED
    assert finalized.manifest["purpose"] == "board-review"
    assert finalized.manifest["approvedBy"] == "Credit Committee"
    assert finalized.manifest["documentCount"] == 1
    assert items[0].dms_document_id == dms_doc.id
