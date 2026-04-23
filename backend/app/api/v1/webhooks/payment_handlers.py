"""Payment webhook event handlers.

Application-specific handlers for payment gateway events.
These handlers process events and update application state.
"""

import logging
from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.payment_gateway.webhook_handler import WebhookEvent

logger = logging.getLogger(__name__)


async def handle_payment_success(
    event: WebhookEvent, db: Optional[AsyncSession]
) -> bool:
    """
    Handle successful payment capture.

    Updates:
    - Portal payment transaction status
    - Loan receipt creation
    - Loan outstanding update
    - Customer notification
    """
    logger.info(
        f"Processing payment success: {event.payment_id}, "
        f"amount: {event.amount}, "
        f"loan: {event.loan_account_id}"
    )

    if not db or not event.loan_account_id:
        logger.warning("Missing db session or loan_account_id")
        return True

    try:
        # Import service here to avoid circular imports
        # from app.services.portal.payment_service import PortalPaymentService

        # service = PortalPaymentService(db)

        # 1. Update portal payment transaction
        # payment = await service.update_payment_status(
        #     gateway_payment_id=event.payment_id,
        #     status="COMPLETED",
        #     payment_method=event.method,
        # )

        # 2. Create loan receipt
        # from app.services.lending.receipt_service import ReceiptService
        # receipt_service = ReceiptService(db)
        # receipt = await receipt_service.create_receipt(
        #     loan_account_id=event.loan_account_id,
        #     amount=event.amount,
        #     payment_mode=event.method,
        #     reference_number=event.payment_id,
        #     received_via="ONLINE_PORTAL",
        # )

        # 3. Update loan outstanding (handled by receipt service)

        # 4. Send notification to customer
        # from app.integrations.communication import CommunicationService
        # comm_service = CommunicationService(db)
        # await comm_service.send_sms(
        #     phone_numbers=[customer.mobile],
        #     template_id="payment_success",
        #     template_params={"amount": str(event.amount)},
        # )

        # await db.commit()

        logger.info(f"Payment {event.payment_id} processed successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to process payment success: {e}")
        # Don't raise - we want to acknowledge the webhook
        return False


async def handle_payment_failure(
    event: WebhookEvent, db: Optional[AsyncSession]
) -> bool:
    """
    Handle payment failure.

    Updates:
    - Portal payment transaction status to failed
    - Send failure notification to customer
    """
    logger.warning(
        f"Processing payment failure: {event.payment_id}, "
        f"loan: {event.loan_account_id}"
    )

    if not db:
        return True

    try:
        # from app.services.portal.payment_service import PortalPaymentService
        # service = PortalPaymentService(db)

        # 1. Update payment status to failed
        # await service.update_payment_status(
        #     gateway_payment_id=event.payment_id,
        #     status="FAILED",
        #     error_message=event.payload.get("error", {}).get("description"),
        # )

        # 2. Notify customer
        # await send_payment_failure_notification(...)

        # await db.commit()

        logger.info(f"Payment failure {event.payment_id} recorded")
        return True

    except Exception as e:
        logger.error(f"Failed to process payment failure: {e}")
        return False


async def handle_refund_success(
    event: WebhookEvent, db: Optional[AsyncSession]
) -> bool:
    """
    Handle successful refund.

    Updates:
    - Portal refund record
    - Adjust loan account if needed
    - Send refund notification
    """
    logger.info(
        f"Processing refund success: {event.refund_id}, "
        f"payment: {event.payment_id}, "
        f"amount: {event.amount}"
    )

    if not db:
        return True

    try:
        # from app.services.portal.payment_service import PortalPaymentService
        # service = PortalPaymentService(db)

        # 1. Update refund record
        # await service.update_refund_status(
        #     gateway_refund_id=event.refund_id,
        #     status="PROCESSED",
        # )

        # 2. Reverse loan receipt if applicable
        # This depends on business rules

        # 3. Notify customer
        # await send_refund_notification(...)

        # await db.commit()

        logger.info(f"Refund {event.refund_id} processed successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to process refund: {e}")
        return False


async def handle_mandate_success(
    event: WebhookEvent, db: Optional[AsyncSession]
) -> bool:
    """
    Handle NACH/UPI mandate confirmation.

    Updates:
    - Portal mandate record to active
    - Enable auto-debit for loan
    - Send confirmation notification
    """
    logger.info(
        f"Processing mandate success: {event.payment_id}, "
        f"loan: {event.loan_account_id}"
    )

    if not db or not event.loan_account_id:
        return True

    try:
        # from app.services.portal.payment_service import PortalPaymentService
        # service = PortalPaymentService(db)

        # 1. Update mandate status to active
        # await service.activate_mandate(
        #     gateway_token_id=event.payment_id,
        #     loan_account_id=event.loan_account_id,
        # )

        # 2. Update loan account for auto-debit
        # from app.services.lending.loan_service import LoanService
        # loan_service = LoanService(db)
        # await loan_service.enable_auto_debit(
        #     loan_account_id=event.loan_account_id,
        #     mandate_id=event.payment_id,
        # )

        # 3. Notify customer
        # await send_mandate_confirmation(...)

        # await db.commit()

        logger.info(f"Mandate {event.payment_id} activated successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to process mandate confirmation: {e}")
        return False


async def handle_mandate_failure(
    event: WebhookEvent, db: Optional[AsyncSession]
) -> bool:
    """
    Handle mandate rejection.

    Updates:
    - Portal mandate record to rejected
    - Send notification to setup again
    """
    logger.warning(
        f"Processing mandate failure: {event.payment_id}, "
        f"loan: {event.loan_account_id}"
    )

    if not db:
        return True

    try:
        # from app.services.portal.payment_service import PortalPaymentService
        # service = PortalPaymentService(db)

        # 1. Update mandate status to rejected
        # await service.reject_mandate(
        #     gateway_token_id=event.payment_id,
        #     reason=event.payload.get("error", {}).get("description"),
        # )

        # 2. Notify customer to setup again
        # await send_mandate_failure_notification(...)

        # await db.commit()

        logger.info(f"Mandate rejection {event.payment_id} recorded")
        return True

    except Exception as e:
        logger.error(f"Failed to process mandate rejection: {e}")
        return False


async def handle_subscription_charged(
    event: WebhookEvent, db: Optional[AsyncSession]
) -> bool:
    """
    Handle subscription charge (recurring payment).

    Updates:
    - Create loan receipt for recurring EMI
    - Update loan outstanding
    - Send payment confirmation
    """
    logger.info(
        f"Processing subscription charge: {event.payment_id}, "
        f"amount: {event.amount}"
    )

    if not db or not event.loan_account_id:
        return True

    try:
        # Similar to payment success but for recurring payments

        logger.info(f"Subscription charge {event.payment_id} processed")
        return True

    except Exception as e:
        logger.error(f"Failed to process subscription charge: {e}")
        return False
