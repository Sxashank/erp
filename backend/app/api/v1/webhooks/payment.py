"""Payment Gateway Webhook API endpoints.

Handles callbacks from payment gateways (Razorpay, PayU, etc.)
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.config import settings
from app.integrations.payment_gateway import RazorpayGateway, create_webhook_handler
from app.core.exceptions import BadRequestException

logger = logging.getLogger(__name__)

router = APIRouter()


def get_razorpay_gateway() -> RazorpayGateway:
    """Get Razorpay gateway instance."""
    return RazorpayGateway(
        api_key=settings.RAZORPAY_KEY_ID or "",
        api_secret=settings.RAZORPAY_KEY_SECRET or "",
        webhook_secret=settings.RAZORPAY_WEBHOOK_SECRET or "",
    )


@router.post(
    "/razorpay",
    summary="Razorpay Webhook",
    description="Handle Razorpay payment webhooks (payment.captured, payment.failed, refund.*, etc.)",
)
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Handle Razorpay webhook events.

    Events handled:
    - payment.authorized
    - payment.captured
    - payment.failed
    - refund.created
    - refund.processed
    - order.paid
    - subscription.activated
    - subscription.charged
    - token.confirmed (NACH/UPI AutoPay)
    - token.rejected
    """
    if not x_razorpay_signature:
        raise BadRequestException(
            detail="Missing X-Razorpay-Signature header",
            error_code="MISSING_X_RAZORPAY_SIGNATURE_HEADER",
        )

    # Read raw body for signature verification
    body = await request.body()

    try:
        gateway = get_razorpay_gateway()
        webhook_handler = create_webhook_handler(gateway, db, register_default_handlers=True)

        # Register custom handlers for our application
        from app.api.v1.webhooks.payment_handlers import (
            handle_mandate_failure,
            handle_mandate_success,
            handle_payment_failure,
            handle_payment_success,
            handle_refund_success,
        )
        from app.integrations.payment_gateway.webhook_handler import WebhookEventType

        webhook_handler.register_handlers(
            {
                WebhookEventType.PAYMENT_CAPTURED: handle_payment_success,
                WebhookEventType.PAYMENT_FAILED: handle_payment_failure,
                WebhookEventType.REFUND_PROCESSED: handle_refund_success,
                WebhookEventType.TOKEN_CONFIRMED: handle_mandate_success,
                WebhookEventType.TOKEN_REJECTED: handle_mandate_failure,
            }
        )

        # Process webhook
        result = await webhook_handler.handle_webhook(body, x_razorpay_signature)

        if not result.get("success"):
            logger.error(f"Webhook processing failed: {result}")
            raise BadRequestException(
                detail=result.get("error", "Webhook processing failed"),
                error_code="BAD_REQUEST",
            )

        return {"status": "ok", **result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Razorpay webhook error: {e}")
        # Return 200 to prevent Razorpay from retrying
        # Log the error for investigation
        return {"status": "error", "message": str(e)}


@router.post(
    "/paytm",
    summary="Paytm Webhook",
    description="Handle Paytm payment webhooks — HMAC verified via tenant IntegrationConfig",
)
async def paytm_webhook(
    request: Request,
    organization_id: UUID,
    x_paytm_checksum: str | None = Header(None),
    x_paytm_timestamp: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Handle Paytm webhook events.

    Signature is verified against the per-tenant ``webhook_signing_secret`` in
    the IntegrationConfig row keyed by (organization_id, PAYMENT_GATEWAY, PAYTM).
    Domain-specific order-status handling is STAGE-6-PENDING-paytm-live.
    """
    from app.core.webhook_gate import verify_tenant_webhook
    from app.models.core.integration_config import (
        IntegrationProvider,
        IntegrationType,
    )

    body = await request.body()
    envelope = await verify_tenant_webhook(
        session=db,
        organization_id=organization_id,
        integration_type=IntegrationType.PAYMENT_GATEWAY,
        provider=IntegrationProvider.PAYTM,
        vendor_label="Paytm",
        body=body,
        signature=x_paytm_checksum or "",
        timestamp=x_paytm_timestamp,
    )
    logger.info(
        "paytm_webhook_verified org=%s bytes=%d",
        envelope.organization_id,
        len(envelope.body),
    )
    # TODO[STAGE-6-PENDING-paytm-live]: dispatch verified payload to the
    # portal payment service (similar to the Razorpay branch above).
    return {"status": "ok", "vendor": "paytm"}


@router.post(
    "/ccavenue",
    summary="CCAvenue Webhook",
    description="Handle CCAvenue payment webhooks — HMAC verified via tenant IntegrationConfig",
)
async def ccavenue_webhook(
    request: Request,
    organization_id: UUID,
    x_ccavenue_signature: str | None = Header(None),
    x_ccavenue_timestamp: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Handle CCAvenue webhook events.

    CCAvenue's real transport is an AES-encrypted form-posted ``encResp``.
    Before we decrypt it we gate on an HMAC signature computed over the raw
    body using the tenant's per-merchant shared secret. That gate matches the
    shape we use for every other vendor so support can reason about signatures
    uniformly.
    """
    from app.core.webhook_gate import verify_tenant_webhook
    from app.models.core.integration_config import (
        IntegrationProvider,
        IntegrationType,
    )

    body = await request.body()
    envelope = await verify_tenant_webhook(
        session=db,
        organization_id=organization_id,
        integration_type=IntegrationType.PAYMENT_GATEWAY,
        provider=IntegrationProvider.CCAVENUE,
        vendor_label="CCAvenue",
        body=body,
        signature=x_ccavenue_signature or "",
        timestamp=x_ccavenue_timestamp,
    )
    logger.info(
        "ccavenue_webhook_verified org=%s bytes=%d",
        envelope.organization_id,
        len(envelope.body),
    )
    # TODO[STAGE-6-PENDING-ccavenue-live]: decrypt `encResp`, verify order,
    # dispatch to portal payment service.
    return {"status": "ok", "vendor": "ccavenue"}


@router.get(
    "/razorpay/verify",
    summary="Verify Razorpay Payment",
    description="Verify payment after customer redirect (callback URL)",
)
async def verify_razorpay_payment(
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify Razorpay payment after redirect.

    This endpoint is called when customer completes payment
    and is redirected back to the application.
    """
    try:
        gateway = get_razorpay_gateway()

        # Verify payment signature
        result = await gateway.verify_payment(
            order_id=razorpay_order_id,
            payment_id=razorpay_payment_id,
            signature=razorpay_signature,
        )

        if not result.success:
            return {
                "success": False,
                "error": result.error_description or "Payment verification failed",
            }

        # Update payment record in database
        # from app.services.portal.payment_service import PortalPaymentService
        # service = PortalPaymentService(db)
        # await service.process_payment_success(...)
        # await db.commit()

        return {
            "success": True,
            "payment_id": result.gateway_payment_id,
            "order_id": razorpay_order_id,
            "status": result.status.value,
            "amount": float(result.amount) if result.amount else None,
            "method": result.payment_method,
        }

    except Exception as e:
        logger.error(f"Payment verification error: {e}")
        return {
            "success": False,
            "error": str(e),
        }
