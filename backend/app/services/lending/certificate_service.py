"""CertificateService — issues borrower-facing certificates and letters.

Flow per issuance:

1. Look up the operator-managed template body in ``mst_document_template``
   for the requested certificate code (uses the current row).
2. Build merge_data from the loan / sanction / application snapshot.
3. Render via the appropriate ``pdf_generator`` function.
4. Upload PDF to DMS.
5. Persist a ``LoanCertificate`` row pointing at the DMS document.
6. Emit a lifecycle event (``CERTIFICATE_ISSUED`` family) so the timeline
   shows the issuance.
7. Optionally send a communication to the borrower (SMS / email) via
   CommunicationService.

The service is intentionally narrow: each certificate-type has a public
``issue_*`` method. They share the post-PDF persistence + event +
notification side via ``_persist_and_emit``.
"""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from decimal import Decimal
from io import BytesIO
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.dms import DMSDocument
from app.models.document_studio import DocumentModule
from app.models.lending.lifecycle_event import (
    LifecycleActorKind,
    LifecycleSubjectType,
)
from app.models.lending.loan_certificate import CertificateType, LoanCertificate
from app.models.lending.masters import DocumentTemplate
from app.services.dms.document_service import DocumentService
from app.services.document_studio_service import DocumentStudioService
from app.services.lending.lifecycle_service import LifecycleService
from app.services.portal import pdf_generator as pdfg

logger = logging.getLogger(__name__)


# Map certificate type → (template code, lifecycle event_type)
_CERT_TYPE_META: dict[CertificateType, tuple[str, str]] = {
    CertificateType.KFS: ("KFS", "KFS_ISSUED"),
    CertificateType.NDC: ("NDC", "NDC_ISSUED"),
    CertificateType.FORECLOSURE_LETTER: ("FORECLOSURE_LETTER", "FORECLOSURE_QUOTE_ISSUED"),
    CertificateType.BALANCE_CONFIRMATION: ("BALANCE_CONFIRMATION", "STATEMENT_ISSUED"),
    CertificateType.CHARGE_RELEASE_LETTER: ("CHARGE_RELEASE_LETTER", "ORIGINAL_DOCS_RELEASED"),
    CertificateType.RATE_REVISION_INTIMATION: ("RATE_REVISION_INTIMATION", "RATE_RESET_APPLIED"),
    CertificateType.DEMAND_NOTICE: ("DEMAND_NOTICE", "DEMAND_NOTICE_ISSUED"),
    CertificateType.PRINCIPAL_PAID_CERT: ("PRINCIPAL_PAID_CERT", "STATEMENT_ISSUED"),
    CertificateType.PROVISIONAL_INTEREST_CERT: (
        "PROVISIONAL_INTEREST_CERT",
        "PROVISIONAL_INTEREST_CERT_ISSUED",
    ),
    CertificateType.INTEREST_CERT: ("INTEREST_CERT", "INTEREST_CERT_ISSUED"),
    CertificateType.STATEMENT_OF_ACCOUNT: ("STATEMENT_OF_ACCOUNT", "STATEMENT_ISSUED"),
}


def _studio_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, date | datetime):
        return value.isoformat()
    return value


class CertificateService:
    """Borrower-facing certificate issuance + acknowledgement."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.lifecycle = LifecycleService(session)
        self.dms = DocumentService(session)

    async def _next_certificate_number(
        self, organization_id: UUID, cert_type: CertificateType
    ) -> str:
        """Generate SMFC/CERT/{TYPE}/{FY}/{NNNN}."""
        from datetime import datetime as _dt

        today = _dt.now(UTC).date()
        fy = (
            f"{today.year - (1 if today.month < 4 else 0)}-"
            f"{(today.year - (1 if today.month < 4 else 0) + 1) % 100:02d}"
        )

        from sqlalchemy import func

        existing = (
            await self.session.execute(
                select(func.count(LoanCertificate.id)).where(
                    LoanCertificate.organization_id == organization_id,
                    LoanCertificate.certificate_type == cert_type,
                )
            )
        ).scalar() or 0
        seq = existing + 1
        return f"CERT/{cert_type.value}/{fy}/{seq:04d}"

    async def _template_body(self, organization_id: UUID, template_code: str) -> tuple[str, int]:
        """Return (body, version) of the current template for this code.

        Falls back to a minimal default body if no template seeded yet.
        """
        stmt = (
            select(DocumentTemplate)
            .where(
                DocumentTemplate.organization_id == organization_id,
                DocumentTemplate.code == template_code,
                DocumentTemplate.is_current.is_(True),
            )
            .limit(1)
        )
        template = (await self.session.execute(stmt)).scalar_one_or_none()
        if template is None:
            logger.warning(
                "certificate.template_missing code=%s — using minimal default",
                template_code,
            )
            return (f"# {template_code}\n\nThis document is system-generated.", 0)
        return (template.body, template.template_version)

    async def _persist_and_emit(
        self,
        *,
        organization_id: UUID,
        cert_type: CertificateType,
        pdf_bytes: bytes | None = None,
        file_name: str,
        certificate_number: str,
        loan_account_id: UUID | None = None,
        application_id: UUID | None = None,
        sanction_id: UUID | None = None,
        issued_by_id: UUID | None = None,
        issued_to_portal_user_id: UUID | None = None,
        period_from: date | None = None,
        period_to: date | None = None,
        financial_year: str | None = None,
        requires_ack: bool = False,
        template_code: str | None = None,
        template_version: int | None = None,
        business_number: str | None = None,
        regulatory_tags: list[str] | None = None,
        dms_document: DMSDocument | None = None,
    ) -> LoanCertificate:
        """Shared post-PDF flow: DMS upload + row insert + lifecycle event."""
        if dms_document is None:
            if pdf_bytes is None:
                raise ValueError("pdf_bytes is required when no DMS document is supplied")
            # Upload to DMS — store under the loan account (or application) entity.
            dms_doc = await self.dms.upload_document(
                organization_id=organization_id,
                file=BytesIO(pdf_bytes),
                file_name=file_name,
                file_size=len(pdf_bytes),
                mime_type="application/pdf",
                name=f"{cert_type.value} — {certificate_number}",
                document_type="LOAN_CERTIFICATE",
                document_subtype=cert_type.value,
                entity_type="loan_account" if loan_account_id else "application",
                entity_id=loan_account_id or application_id,
                created_by=issued_by_id,
                auto_commit=False,
            )
            file_size = len(pdf_bytes)
        else:
            dms_doc = dms_document
            file_size = dms_doc.file_size

        row = LoanCertificate(
            organization_id=organization_id,
            loan_account_id=loan_account_id,
            application_id=application_id,
            sanction_id=sanction_id,
            certificate_type=cert_type,
            certificate_number=certificate_number,
            dms_document_id=dms_doc.id,
            file_path=dms_doc.storage_path,
            file_size=file_size,
            issued_at=datetime.now(UTC),
            issued_by_id=issued_by_id,
            issued_to_portal_user_id=issued_to_portal_user_id,
            period_from=period_from,
            period_to=period_to,
            financial_year=financial_year,
            requires_acknowledgement=requires_ack,
            template_code=template_code,
            template_version=template_version,
        )
        self.session.add(row)
        await self.session.flush()

        # Lifecycle event — uses the cert-type-mapped event name where present
        event_type = _CERT_TYPE_META.get(cert_type, (None, "CERTIFICATE_ISSUED"))[1]
        subject_type = (
            LifecycleSubjectType.LOAN_ACCOUNT
            if loan_account_id
            else (
                LifecycleSubjectType.APPLICATION
                if application_id
                else LifecycleSubjectType.CERTIFICATE
            )
        )
        subject_id = loan_account_id or application_id or row.id

        await self.lifecycle.record_event(
            organization_id=organization_id,
            subject_type=subject_type,
            subject_id=subject_id,
            event_type=event_type,
            actor_kind=LifecycleActorKind.LENDER if issued_by_id else LifecycleActorKind.SYSTEM,
            actor_user_id=issued_by_id,
            business_number=business_number,
            payload={
                "certificate_id": str(row.id),
                "certificate_type": cert_type.value,
                "certificate_number": certificate_number,
                "dms_document_id": str(dms_doc.id),
            },
            attachments=[
                {
                    "dms_document_id": str(dms_doc.id),
                    "file_name": file_name,
                    "mime_type": "application/pdf",
                }
            ],
            regulatory_tags=regulatory_tags or [],
        )
        return row

    async def _try_document_studio_issue(
        self,
        *,
        organization_id: UUID,
        cert_type: CertificateType,
        document_type: str,
        file_name: str,
        certificate_number: str,
        entity_type: str,
        entity_id: UUID,
        context: dict[str, Any],
        issued_by_id: UUID,
        business_number: str | None = None,
    ) -> tuple[DMSDocument, str, int] | None:
        try:
            generated = await DocumentStudioService(self.session).generate(
                organization_id=organization_id,
                user_id=issued_by_id,
                data={
                    "module": DocumentModule.LENDING,
                    "document_type": document_type,
                    "document_subtype": cert_type.value,
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "generated_from": "LENDING_CERTIFICATE",
                    "business_number": business_number or certificate_number,
                    "file_name": file_name,
                    "context": context,
                    "portal_visible": True,
                },
            )
            dms_doc = await self.session.get(DMSDocument, generated.dms_document_id)
            if dms_doc is None:
                return None
            return dms_doc, generated.template_code, generated.template_version
        except Exception:
            logger.warning(
                "certificate.document_studio_fallback",
                extra={
                    "document_type": document_type,
                    "certificate_number": certificate_number,
                    "entity_type": entity_type,
                    "entity_id": str(entity_id),
                },
                exc_info=True,
            )
            return None

    # ------------------------------------------------------------------
    # Issue methods (one per certificate type)
    # ------------------------------------------------------------------

    async def issue_kfs(
        self,
        *,
        organization_id: UUID,
        sanction_id: UUID,
        application_id: UUID,
        issued_by_id: UUID,
        organization_name: str,
        organization_address: str | None,
        merge_data: dict[str, Any],
        summary: dict[str, Any],
    ) -> LoanCertificate:
        """RBI-mandated Key Facts Statement."""
        body, version = await self._template_body(organization_id, "KFS")
        cert_number = await self._next_certificate_number(organization_id, CertificateType.KFS)
        file_name = f"KFS_{cert_number.replace('/', '_')}.pdf"
        studio_doc = await self._try_document_studio_issue(
            organization_id=organization_id,
            cert_type=CertificateType.KFS,
            document_type="KFS",
            file_name=file_name,
            certificate_number=cert_number,
            entity_type="application",
            entity_id=application_id,
            issued_by_id=issued_by_id,
            business_number=merge_data.get("application_number")
            or merge_data.get("applicationNumber")
            or str(application_id),
            context={
                "organization": {
                    "name": organization_name,
                    "registeredAddress": organization_address,
                },
                "entity": {
                    "entityCode": merge_data.get("entity_code")
                    or merge_data.get("entityCode")
                    or str(application_id)[:8],
                    "legalName": merge_data.get("borrower_name")
                    or merge_data.get("entity_name")
                    or merge_data.get("legal_name")
                    or "Borrower",
                },
                "application": {
                    "applicationNumber": merge_data.get("application_number")
                    or merge_data.get("applicationNumber")
                    or str(application_id),
                },
                "sanction": {
                    "sanctionNumber": merge_data.get("sanction_number")
                    or merge_data.get("sanctionNumber")
                    or str(sanction_id),
                    "sanctionedAmount": _studio_value(
                        summary.get("sanctioned_amount")
                        or summary.get("sanctionedAmount")
                        or merge_data.get("sanctioned_amount")
                    ),
                },
                "loanAccount": {
                    "accountNumber": merge_data.get("loan_account_number")
                    or merge_data.get("loanAccountNumber")
                    or str(application_id)[:8],
                    "interestRate": _studio_value(
                        summary.get("interest_rate")
                        or summary.get("interestRate")
                        or merge_data.get("interest_rate")
                    ),
                },
            },
        )
        if studio_doc:
            dms_doc, template_code, template_version = studio_doc
            return await self._persist_and_emit(
                organization_id=organization_id,
                cert_type=CertificateType.KFS,
                file_name=file_name,
                certificate_number=cert_number,
                application_id=application_id,
                sanction_id=sanction_id,
                issued_by_id=issued_by_id,
                requires_ack=True,
                template_code=template_code,
                template_version=template_version,
                regulatory_tags=["KFS_ISSUED"],
                dms_document=dms_doc,
            )

        pdf = pdfg.render_kfs_pdf(
            organization_name=organization_name,
            organization_address=organization_address,
            body_markdown=body,
            merge_data=merge_data,
            certificate_number=cert_number,
            summary=summary,
        )
        return await self._persist_and_emit(
            organization_id=organization_id,
            cert_type=CertificateType.KFS,
            pdf_bytes=pdf,
            file_name=file_name,
            certificate_number=cert_number,
            application_id=application_id,
            sanction_id=sanction_id,
            issued_by_id=issued_by_id,
            requires_ack=True,
            template_code="KFS",
            template_version=version,
            regulatory_tags=["KFS_ISSUED"],
        )

    async def acknowledge_kfs(
        self,
        *,
        organization_id: UUID,
        certificate_id: UUID,
        portal_user_id: UUID,
    ) -> LoanCertificate:
        """Borrower clicks 'I acknowledge the KFS' on portal."""
        row = await self.session.get(LoanCertificate, certificate_id)
        if row is None or row.organization_id != organization_id:
            raise NotFoundException(
                detail="KFS certificate not found",
                error_code="KFS_NOT_FOUND",
            )
        if row.certificate_type != CertificateType.KFS:
            raise NotFoundException(
                detail="Certificate is not a KFS",
                error_code="KFS_TYPE_MISMATCH",
            )
        row.is_acknowledged = True
        row.acknowledged_at = datetime.now(UTC)
        row.acknowledged_by_portal_user_id = portal_user_id

        await self.lifecycle.record_event(
            organization_id=organization_id,
            subject_type=(
                LifecycleSubjectType.APPLICATION
                if row.application_id
                else LifecycleSubjectType.SANCTION
            ),
            subject_id=row.application_id or row.sanction_id or row.id,
            event_type="KFS_ACKNOWLEDGED",
            actor_kind=LifecycleActorKind.BORROWER,
            actor_user_id=None,
            actor_role="BORROWER",
            payload={
                "certificate_id": str(row.id),
                "portal_user_id": str(portal_user_id),
            },
            regulatory_tags=["KFS_ACKNOWLEDGED"],
        )
        await self.session.flush()
        return row

    async def issue_ndc(
        self,
        *,
        organization_id: UUID,
        loan_account_id: UUID,
        issued_by_id: UUID,
        organization_name: str,
        organization_address: str | None,
        borrower_name: str,
        loan_account_number: str,
        closure_date: date,
        period_start: date,
        merge_data: dict[str, Any] | None = None,
    ) -> LoanCertificate:
        body, version = await self._template_body(organization_id, "NDC")
        cert_number = await self._next_certificate_number(organization_id, CertificateType.NDC)
        file_name = f"NDC_{cert_number.replace('/', '_')}.pdf"
        studio_doc = await self._try_document_studio_issue(
            organization_id=organization_id,
            cert_type=CertificateType.NDC,
            document_type="NDC",
            file_name=file_name,
            certificate_number=cert_number,
            entity_type="loan_account",
            entity_id=loan_account_id,
            issued_by_id=issued_by_id,
            business_number=loan_account_number,
            context={
                "organization": {
                    "name": organization_name,
                    "registeredAddress": organization_address,
                },
                "entity": {
                    "entityCode": (merge_data or {}).get("entity_code")
                    or (merge_data or {}).get("entityCode")
                    or loan_account_number,
                    "legalName": borrower_name,
                },
                "loanAccount": {"accountNumber": loan_account_number},
            },
        )
        if studio_doc:
            dms_doc, template_code, template_version = studio_doc
            return await self._persist_and_emit(
                organization_id=organization_id,
                cert_type=CertificateType.NDC,
                file_name=file_name,
                certificate_number=cert_number,
                loan_account_id=loan_account_id,
                issued_by_id=issued_by_id,
                template_code=template_code,
                template_version=template_version,
                business_number=loan_account_number,
                dms_document=dms_doc,
            )

        pdf = pdfg.render_no_dues_certificate_pdf(
            organization_name=organization_name,
            organization_address=organization_address,
            body_markdown=body,
            merge_data=merge_data
            or {
                "borrower_name": borrower_name,
                "loan_account_number": loan_account_number,
                "closure_date": closure_date,
            },
            certificate_number=cert_number,
            borrower_name=borrower_name,
            loan_account_number=loan_account_number,
            closure_date=closure_date,
            period_start=period_start,
        )
        return await self._persist_and_emit(
            organization_id=organization_id,
            cert_type=CertificateType.NDC,
            pdf_bytes=pdf,
            file_name=file_name,
            certificate_number=cert_number,
            loan_account_id=loan_account_id,
            issued_by_id=issued_by_id,
            template_code="NDC",
            template_version=version,
            business_number=loan_account_number,
        )

    async def issue_foreclosure_letter(
        self,
        *,
        organization_id: UUID,
        loan_account_id: UUID,
        issued_by_id: UUID,
        organization_name: str,
        organization_address: str | None,
        borrower_name: str,
        loan_account_number: str,
        as_of_date: date,
        valid_till: date,
        principal_outstanding: Decimal,
        interest_accrued: Decimal,
        foreclosure_fee: Decimal,
        other_charges: Decimal,
        payment_account_details: str,
        merge_data: dict[str, Any] | None = None,
    ) -> LoanCertificate:
        body, version = await self._template_body(organization_id, "FORECLOSURE_LETTER")
        cert_number = await self._next_certificate_number(
            organization_id, CertificateType.FORECLOSURE_LETTER
        )
        file_name = f"FORECLOSURE_{cert_number.replace('/', '_')}.pdf"
        studio_doc = await self._try_document_studio_issue(
            organization_id=organization_id,
            cert_type=CertificateType.FORECLOSURE_LETTER,
            document_type="FORECLOSURE_LETTER",
            file_name=file_name,
            certificate_number=cert_number,
            entity_type="loan_account",
            entity_id=loan_account_id,
            issued_by_id=issued_by_id,
            business_number=loan_account_number,
            context={
                "organization": {
                    "name": organization_name,
                    "registeredAddress": organization_address,
                },
                "entity": {
                    "entityCode": (merge_data or {}).get("entity_code")
                    or (merge_data or {}).get("entityCode")
                    or loan_account_number,
                    "legalName": borrower_name,
                },
                "loanAccount": {"accountNumber": loan_account_number},
                "foreclosure": {
                    "asOfDate": _studio_value(as_of_date),
                    "validTill": _studio_value(valid_till),
                    "principalOutstanding": _studio_value(principal_outstanding),
                    "interestAccrued": _studio_value(interest_accrued),
                    "foreclosureFee": _studio_value(foreclosure_fee),
                    "otherCharges": _studio_value(other_charges),
                    "paymentAccountDetails": payment_account_details,
                },
            },
        )
        if studio_doc:
            dms_doc, template_code, template_version = studio_doc
            return await self._persist_and_emit(
                organization_id=organization_id,
                cert_type=CertificateType.FORECLOSURE_LETTER,
                file_name=file_name,
                certificate_number=cert_number,
                loan_account_id=loan_account_id,
                issued_by_id=issued_by_id,
                template_code=template_code,
                template_version=template_version,
                business_number=loan_account_number,
                dms_document=dms_doc,
            )

        pdf = pdfg.render_foreclosure_letter_pdf(
            organization_name=organization_name,
            organization_address=organization_address,
            body_markdown=body,
            merge_data=merge_data or {},
            certificate_number=cert_number,
            borrower_name=borrower_name,
            loan_account_number=loan_account_number,
            as_of_date=as_of_date,
            valid_till=valid_till,
            principal_outstanding=principal_outstanding,
            interest_accrued=interest_accrued,
            foreclosure_fee=foreclosure_fee,
            other_charges=other_charges,
            payment_account_details=payment_account_details,
        )
        return await self._persist_and_emit(
            organization_id=organization_id,
            cert_type=CertificateType.FORECLOSURE_LETTER,
            pdf_bytes=pdf,
            file_name=file_name,
            certificate_number=cert_number,
            loan_account_id=loan_account_id,
            issued_by_id=issued_by_id,
            template_code="FORECLOSURE_LETTER",
            template_version=version,
            business_number=loan_account_number,
        )

    async def list_for_loan(
        self,
        *,
        organization_id: UUID,
        loan_account_id: UUID,
    ) -> list[LoanCertificate]:
        stmt = (
            select(LoanCertificate)
            .where(
                LoanCertificate.organization_id == organization_id,
                LoanCertificate.loan_account_id == loan_account_id,
            )
            .order_by(LoanCertificate.issued_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_for_application(
        self,
        *,
        organization_id: UUID,
        application_id: UUID,
    ) -> list[LoanCertificate]:
        stmt = (
            select(LoanCertificate)
            .where(
                LoanCertificate.organization_id == organization_id,
                LoanCertificate.application_id == application_id,
            )
            .order_by(LoanCertificate.issued_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get(self, *, organization_id: UUID, certificate_id: UUID) -> LoanCertificate:
        row = await self.session.get(LoanCertificate, certificate_id)
        if row is None or row.organization_id != organization_id:
            raise NotFoundException(
                detail=f"Certificate {certificate_id} not found",
                error_code="CERTIFICATE_NOT_FOUND",
            )
        return row
