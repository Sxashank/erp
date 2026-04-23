"""Payment Gateway Webhook API endpoints.

Handles callbacks from payment gateways (Razorpay, PayU, etc.)
"""

import logging
from typing import Optional

from fastapi import APIRouter, Request, Header, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.config import settings
from app.integrations.payment_gateway import RazorpayGateway, create_webhook_handler
from app.integrations.payment_gateway.webhook_handler import WebhookEvent

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
    x_razorpay_signature: Optional[str] = Header(None),
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-Razorpay-Signature header",
        )

    # Read raw body for signature verification
    body = await request.body()

    try:
        gateway = get_razorpay_gateway()
        webhook_handler = create_webhook_handler(gateway, db, register_default_handlers=True)

        # Register custom handlers for our application
        from app.api.v1.webhooks.payment_handlers import (
            handle_payment_success,
            handle_payment_failure,
            handle_refund_success,
            handle_mandate_success,
            handle_mandate_failure,
        )
        from app.integrations.payment_gateway.webhook_handler import WebhookEventType

        webhook_handler.register_handlers({
            WebhookEventType.PAYMENT_CAPTURED: handle_payment_success,
            WebhookEventType.PAYMENT_FAILED: handle_payment_failure,
            WebhookEventType.REFUND_PROCESSED: handle_refund_success,
            WebhookEventType.TOKEN_CONFIRMED: handle_mandate_success,
            WebhookEventType.TOKEN_REJECTED: handle_mandate_failure,
        })

        # Process webhook
        result = await webhook_handler.handle_webhook(body, x_razorpay_signature)

        if not result.get("success"):
            logger.error(f"Webhook processing failed: {result}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Webhook processing failed"),
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
    description="Handle Paytm payment webhooks",
)
async def paytm_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle Paytm webhook events."""
    body = await request.json()

    logger.info(f"Paytm webhook received: {body.get('ORDERID')}")

    # TODO: Implement Paytm webhook handling
    # - Verify checksum
    # - Process payment status
    # - Update records

    return {"status": "ok"}


@router.post(
    "/ccavenue",
    summary="CCAvenue Webhook",
    description="Handle CCAvenue payment webhooks",
)
async def ccavenue_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle CCAvenue webhook events."""
    # CCAvenue sends encrypted response
    form_data = await request.form()
    enc_resp = form_data.get("encResp")

    if not enc_resp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing encResp",
        )

    logger.info("CCAvenue webhook received")

    # TODO: Implement CCAvenue webhook handling
    # - Decrypt response
    # - Verify order
    # - Process payment status

    return {"status": "ok"}


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
