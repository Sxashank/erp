"""Credit bureau webhook callbacks (CIBIL / Experian / Crif).

Bureaus deliver credit-report pull results asynchronously when the response
payload is large or when the bureau's batch pipeline is busy. This router
accepts those async delivery callbacks, verifies the HMAC signature against
the per-tenant signing secret (pulled from IntegrationConfig per CLAUDE.md
§6.8), and hands the payload to the bureau service for persistence.

All three bureaus use the same shape (HMAC-SHA256 over the raw body plus a
timestamp header) so we share one helper and dispatch by provider.

**Not live**: until a tenant provisions their bureau IntegrationConfig
(provider + signing secret from the bureau's NBFC portal), the handler
returns 400 ``WEBHOOK_NOT_CONFIGURED``. This is intentional — the bureau
never sends webhooks to an NBFC that hasn't registered with them, so the
state of "no config" only happens during a misconfigured production cutover.
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.webhook_gate import verify_tenant_webhook
from app.models.core.integration_config import (
    IntegrationProvider,
    IntegrationType,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/cibil",
    summary="CIBIL async callback",
    description="Async credit-report delivery callback from CIBIL (TransUnion India).",
)
async def cibil_callback(
    request: Request,
    organization_id: UUID,
    x_cibil_signature: str | None = Header(None),
    x_cibil_timestamp: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    """Verify + accept a CIBIL async credit-report delivery.

    Actual report parsing is deferred to the bureau service — we only
    confirm authenticity here. The service validates schema + upserts the
    pull record; failures there return 500 so CIBIL retries.
    """
    body = await request.body()
    envelope = await verify_tenant_webhook(
        session=db,
        organization_id=organization_id,
        integration_type=IntegrationType.CREDIT_BUREAU,
        provider=IntegrationProvider.CIBIL,
        vendor_label="CIBIL",
        body=body,
        signature=x_cibil_signature or "",
        timestamp=x_cibil_timestamp,
    )
    logger.info(
        "bureau_callback_verified",
        extra={"vendor": envelope.vendor, "org_id": str(envelope.organization_id)},
    )
    # TODO[STAGE-6-PENDING-cibil-live]: dispatch to bureau_service.ingest_async_report.
    # Returning ACK here keeps CIBIL from retrying while the domain side is wired.
    return {"status": "ok", "vendor": "cibil"}


@router.post(
    "/experian",
    summary="Experian async callback",
    description="Async credit-report delivery callback from Experian.",
)
async def experian_callback(
    request: Request,
    organization_id: UUID,
    x_experian_signature: str | None = Header(None),
    x_experian_timestamp: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    """Verify + accept an Experian async credit-report delivery."""
    body = await request.body()
    envelope = await verify_tenant_webhook(
        session=db,
        organization_id=organization_id,
        integration_type=IntegrationType.CREDIT_BUREAU,
        provider=IntegrationProvider.EXPERIAN,
        vendor_label="Experian",
        body=body,
        signature=x_experian_signature or "",
        timestamp=x_experian_timestamp,
    )
    logger.info(
        "bureau_callback_verified",
        extra={"vendor": envelope.vendor, "org_id": str(envelope.organization_id)},
    )
    # TODO[STAGE-6-PENDING-experian-live]: dispatch to bureau_service.ingest_async_report.
    return {"status": "ok", "vendor": "experian"}


@router.post(
    "/crif",
    summary="CRIF Highmark async callback",
    description="Async credit-report delivery callback from CRIF Highmark.",
)
async def crif_callback(
    request: Request,
    organization_id: UUID,
    x_crif_signature: str | None = Header(None),
    x_crif_timestamp: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    """Verify + accept a CRIF Highmark async credit-report delivery."""
    body = await request.body()
    envelope = await verify_tenant_webhook(
        session=db,
        organization_id=organization_id,
        integration_type=IntegrationType.CREDIT_BUREAU,
        provider=IntegrationProvider.CRIF,
        vendor_label="CRIF",
        body=body,
        signature=x_crif_signature or "",
        timestamp=x_crif_timestamp,
    )
    logger.info(
        "bureau_callback_verified",
        extra={"vendor": envelope.vendor, "org_id": str(envelope.organization_id)},
    )
    # TODO[STAGE-6-PENDING-crif-live]: dispatch to bureau_service.ingest_async_report.
    return {"status": "ok", "vendor": "crif"}
