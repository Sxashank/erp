"""Borrower-portal wrappers for the lifecycle event log and certificate flow.

These three endpoints mirror the admin-side `/lending/...` ones but enforce
the borrower JWT (`get_portal_user`) and intersect with the borrower's
accessible loan / application set.

- ``GET  /portal/loans/{loan_id}/lifecycle``
- ``GET  /portal/applications/{application_id}/certificates``
- ``POST /portal/certificates/{certificate_id}/acknowledge``  (KFS ack)
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.portal.auth import get_portal_db_with_tenant, get_portal_user
from app.core.exceptions import BadRequestException, NotFoundException
from app.models.lending.loan_certificate import CertificateType, LoanCertificate
from app.services.lending.certificate_service import CertificateService
from app.services.lending.lifecycle_service import LifecycleService
from app.services.portal.entity_access import (
    assert_application_access,
    assert_loan_access,
)

router = APIRouter(tags=["Borrower Portal · Lifecycle & Certificates"])


@router.get("/loans/{loan_id}/lifecycle")
async def borrower_loan_lifecycle(
    loan_id: UUID,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
) -> dict:
    """Return the borrower-visible lifecycle events for a loan they own."""
    loan = await assert_loan_access(user, loan_id, db)

    svc = LifecycleService(db)
    events = await svc.list_for_loan_account(
        loan_account_id=loan.id,
        organization_id=user.organization_id,
        application_id=loan.application_id,
        borrower_visible_only=True,
    )
    return {
        "loanAccountId": str(loan.id),
        "events": [
            {
                "id": str(e.id),
                "eventAt": e.event_at.isoformat() if e.event_at else None,
                "eventType": e.event_type,
                "actorKind": (
                    e.actor_kind.value if hasattr(e.actor_kind, "value") else str(e.actor_kind)
                ),
                "stateFrom": e.state_from,
                "stateTo": e.state_to,
                "reasonText": e.reason_text,
                "payload": e.payload or {},
                "attachments": e.attachments or [],
                "regulatoryTags": list(e.regulatory_tags or []),
            }
            for e in events
        ],
    }


@router.get("/applications/{application_id}/certificates")
async def borrower_application_certificates(
    application_id: UUID,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
) -> dict:
    """List certificates associated with the borrower's application (KFS, etc.)."""
    application = await assert_application_access(user, application_id, db)

    stmt = (
        select(LoanCertificate)
        .where(
            LoanCertificate.organization_id == user.organization_id,
            LoanCertificate.application_id == application.id,
        )
        .order_by(LoanCertificate.issued_at.desc())
    )
    rows = (await db.execute(stmt)).scalars().all()
    return {
        "applicationId": str(application.id),
        "items": [
            {
                "id": str(r.id),
                "certificateType": (
                    r.certificate_type.value
                    if hasattr(r.certificate_type, "value")
                    else str(r.certificate_type)
                ),
                "certificateNumber": r.certificate_number,
                "issuedAt": r.issued_at.isoformat() if r.issued_at else None,
                "requiresAcknowledgement": r.requires_acknowledgement,
                "isAcknowledged": r.is_acknowledged,
                "acknowledgedAt": r.acknowledged_at.isoformat() if r.acknowledged_at else None,
                "dmsDocumentId": str(r.dms_document_id) if r.dms_document_id else None,
            }
            for r in rows
        ],
    }


@router.post("/certificates/{certificate_id}/acknowledge")
async def borrower_acknowledge_certificate(
    certificate_id: UUID,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_portal_db_with_tenant),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> dict:
    """Borrower acknowledges a KFS certificate (RBI Oct-2024 mandate)."""
    cert = await db.get(LoanCertificate, certificate_id)
    if cert is None or cert.organization_id != user.organization_id:
        raise NotFoundException(
            detail="Certificate not found",
            error_code="CERTIFICATE_NOT_FOUND",
        )
    if cert.certificate_type != CertificateType.KFS:
        raise BadRequestException(
            "Only KFS certificates can be acknowledged.",
            error_code="CERTIFICATE_TYPE_NOT_ACKNOWLEDGEABLE",
        )
    # Verify the borrower owns the application this cert was issued against
    if cert.application_id is not None:
        await assert_application_access(user, cert.application_id, db)

    svc = CertificateService(db)
    updated = await svc.acknowledge_kfs(
        organization_id=user.organization_id,
        certificate_id=certificate_id,
        portal_user_id=user.id,
    )
    await db.commit()
    return {
        "id": str(updated.id),
        "isAcknowledged": updated.is_acknowledged,
        "acknowledgedAt": updated.acknowledged_at.isoformat() if updated.acknowledged_at else None,
    }
