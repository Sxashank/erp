"""NACH webhook handlers for receiving provider notifications."""

import hashlib
import hmac
import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status, Header
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.lending.nach_batch import NachBatch, NachTransaction, NachMandateLog
from app.models.lending.loan_account import LoanMandate, LoanReceipt
from app.models.lending.enums import (
    NachBatchStatus, NachTransactionStatus, NachReturnCode, NachFileFormat,
    MandateStatus, ReceiptMode, ReceiptStatus, ReceiptType
)
from app.models.core.integration_config import IntegrationConfig, IntegrationType, IntegrationProvider

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Razorpay Webhooks
# =============================================================================


@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Handle Razorpay NACH/Auto-debit webhooks.

    Events handled:
    - token.confirmed: Mandate registered successfully
    - token.cancelled: Mandate cancelled
    - payment.captured: Debit successful
    - payment.failed: Debit failed
    """
    body = await request.body()
    payload = await request.json()

    # Get integration config for webhook secret
    query = select(IntegrationConfig).where(
        and_(
            IntegrationConfig.provider == IntegrationProvider.RAZORPAY_NACH,
            IntegrationConfig.is_active == True,
        )
    )
    result = await db.execute(query)
    config = result.scalar_one_or_none()

    if config and config.webhook_secret and x_razorpay_signature:
        # Verify signature
        expected = hmac.new(
            config.webhook_secret.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected, x_razorpay_signature):
            logger.warning("Invalid Razorpay webhook signature")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature",
            )

    event = payload.get("event", "")
    entity = payload.get("payload", {}).get("token", {}).get("entity", {}) or \
             payload.get("payload", {}).get("payment", {}).get("entity", {})

    logger.info(f"Razorpay webhook received: {event}")

    try:
        if event == "token.confirmed":
            await _handle_razorpay_mandate_confirmed(db, entity)
        elif event == "token.cancelled":
            await _handle_razorpay_mandate_cancelled(db, entity)
        elif event == "payment.captured":
            await _handle_razorpay_payment_success(db, entity)
        elif event == "payment.failed":
            await _handle_razorpay_payment_failed(db, entity)
        else:
            logger.info(f"Unhandled Razorpay event: {event}")

        await db.commit()

    except Exception as e:
        logger.error(f"Error processing Razorpay webhook: {e}")
        await db.rollback()
        # Don't raise - return 200 to prevent retries for processing errors

    return {"status": "ok"}


async def _handle_razorpay_mandate_confirmed(db: AsyncSession, entity: Dict):
    """Handle mandate confirmation."""
    notes = entity.get("notes", {})
    mandate_reference = notes.get("mandate_reference")
    token_id = entity.get("id")

    if mandate_reference:
        query = select(LoanMandate).where(
            LoanMandate.mandate_reference == mandate_reference
        )
        result = await db.execute(query)
        mandate = result.scalar_one_or_none()

        if mandate:
            mandate.umrn = token_id
            mandate.status = MandateStatus.ACTIVE
            mandate.registration_date = datetime.utcnow().date()
            logger.info(f"Mandate {mandate_reference} confirmed with UMRN {token_id}")


async def _handle_razorpay_mandate_cancelled(db: AsyncSession, entity: Dict):
    """Handle mandate cancellation."""
    token_id = entity.get("id")

    query = select(LoanMandate).where(LoanMandate.umrn == token_id)
    result = await db.execute(query)
    mandate = result.scalar_one_or_none()

    if mandate:
        mandate.status = MandateStatus.CANCELLED
        mandate.cancellation_date = datetime.utcnow().date()
        logger.info(f"Mandate {mandate.mandate_reference} cancelled")


async def _handle_razorpay_payment_success(db: AsyncSession, entity: Dict):
    """Handle successful payment."""
    payment_id = entity.get("id")
    notes = entity.get("notes", {})
    transaction_ref = notes.get("transaction_reference")

    if transaction_ref:
        query = select(NachTransaction).where(
            NachTransaction.transaction_reference == transaction_ref
        )
        result = await db.execute(query)
        txn = result.scalar_one_or_none()

        if txn:
            txn.status = NachTransactionStatus.SUCCESS
            txn.bank_reference = payment_id
            txn.return_code = NachReturnCode.SUCCESS
            txn.processed_at = datetime.utcnow()

            # Create receipt
            from app.models.lending.loan_account import LoanAccount
            loan_account = await db.get(LoanAccount, txn.loan_account_id)

            receipt = LoanReceipt(
                organization_id=loan_account.organization_id,
                loan_account_id=txn.loan_account_id,
                receipt_number=f"NACH/{txn.transaction_reference}",
                receipt_date=datetime.utcnow().date(),
                value_date=datetime.utcnow().date(),
                receipt_amount=txn.debit_amount,
                receipt_type=ReceiptType.REGULAR,
                receipt_mode=ReceiptMode.NACH,
                instrument_number=payment_id,
                instrument_date=datetime.utcnow().date(),
                mandate_id=txn.loan_mandate_id,
                status=ReceiptStatus.PENDING,
            )
            db.add(receipt)
            await db.flush()
            txn.receipt_id = receipt.id

            logger.info(f"NACH payment {transaction_ref} successful")


async def _handle_razorpay_payment_failed(db: AsyncSession, entity: Dict):
    """Handle failed payment."""
    notes = entity.get("notes", {})
    transaction_ref = notes.get("transaction_reference")
    error = entity.get("error", {})

    if transaction_ref:
        query = select(NachTransaction).where(
            NachTransaction.transaction_reference == transaction_ref
        )
        result = await db.execute(query)
        txn = result.scalar_one_or_none()

        if txn:
            txn.status = NachTransactionStatus.BOUNCED
            txn.failure_reason = error.get("description", "Payment failed")
            txn.response_message = json.dumps(error)
            txn.processed_at = datetime.utcnow()

            # Check if retryable
            error_code = error.get("code", "")
            if error_code in ("BAD_REQUEST_ERROR_INSUFFICIENT_FUNDS",):
                if txn.retry_count < txn.max_retries:
                    txn.status = NachTransactionStatus.RETRY_SCHEDULED
                    from datetime import timedelta
                    txn.next_retry_date = datetime.utcnow().date() + timedelta(days=7)

            logger.info(f"NACH payment {transaction_ref} failed: {error.get('description')}")


# =============================================================================
# Cashfree Webhooks
# =============================================================================


@router.post("/cashfree")
async def cashfree_webhook(
    request: Request,
    x_cf_signature: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Handle Cashfree NACH/Auto-collect webhooks.

    Events handled:
    - SUBSCRIPTION_AUTHORIZATION_SUCCESS
    - SUBSCRIPTION_AUTHORIZATION_FAILED
    - SUBSCRIPTION_PAYMENT_SUCCESS
    - SUBSCRIPTION_PAYMENT_FAILED
    """
    body = await request.body()
    payload = await request.json()

    # Get integration config for signature verification
    query = select(IntegrationConfig).where(
        and_(
            IntegrationConfig.provider == IntegrationProvider.CASHFREE_NACH,
            IntegrationConfig.is_active == True,
        )
    )
    result = await db.execute(query)
    config = result.scalar_one_or_none()

    if config and config.webhook_secret and x_cf_signature:
        # Verify Cashfree signature
        timestamp = request.headers.get("x-cf-timestamp", "")
        signature_data = f"{timestamp}{body.decode()}"
        expected = hmac.new(
            config.webhook_secret.encode(),
            signature_data.encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected, x_cf_signature):
            logger.warning("Invalid Cashfree webhook signature")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature",
            )

    event_type = payload.get("type", "")
    data = payload.get("data", {})

    logger.info(f"Cashfree webhook received: {event_type}")

    try:
        if event_type == "SUBSCRIPTION_AUTHORIZATION_SUCCESS":
            await _handle_cashfree_auth_success(db, data)
        elif event_type == "SUBSCRIPTION_AUTHORIZATION_FAILED":
            await _handle_cashfree_auth_failed(db, data)
        elif event_type == "SUBSCRIPTION_PAYMENT_SUCCESS":
            await _handle_cashfree_payment_success(db, data)
        elif event_type == "SUBSCRIPTION_PAYMENT_FAILED":
            await _handle_cashfree_payment_failed(db, data)
        else:
            logger.info(f"Unhandled Cashfree event: {event_type}")

        await db.commit()

    except Exception as e:
        logger.error(f"Error processing Cashfree webhook: {e}")
        await db.rollback()

    return {"status": "ok"}


async def _handle_cashfree_auth_success(db: AsyncSession, data: Dict):
    """Handle mandate authorization success."""
    subscription_id = data.get("subscription", {}).get("subscription_id")
    umrn = data.get("authorization", {}).get("umrn")

    if subscription_id:
        query = select(LoanMandate).where(
            LoanMandate.mandate_reference == subscription_id
        )
        result = await db.execute(query)
        mandate = result.scalar_one_or_none()

        if mandate:
            mandate.umrn = umrn
            mandate.status = MandateStatus.ACTIVE
            mandate.registration_date = datetime.utcnow().date()
            logger.info(f"Cashfree mandate {subscription_id} authorized with UMRN {umrn}")


async def _handle_cashfree_auth_failed(db: AsyncSession, data: Dict):
    """Handle mandate authorization failure."""
    subscription_id = data.get("subscription", {}).get("subscription_id")
    error = data.get("error", {})

    if subscription_id:
        query = select(LoanMandate).where(
            LoanMandate.mandate_reference == subscription_id
        )
        result = await db.execute(query)
        mandate = result.scalar_one_or_none()

        if mandate:
            mandate.status = MandateStatus.REJECTED
            mandate.rejection_reason = error.get("message", "Authorization failed")
            logger.info(f"Cashfree mandate {subscription_id} authorization failed")


async def _handle_cashfree_payment_success(db: AsyncSession, data: Dict):
    """Handle successful payment."""
    payment_id = data.get("payment", {}).get("cf_payment_id")
    cf_order_id = data.get("payment", {}).get("order_id")

    # Order ID should match our transaction reference
    if cf_order_id:
        query = select(NachTransaction).where(
            NachTransaction.transaction_reference == cf_order_id
        )
        result = await db.execute(query)
        txn = result.scalar_one_or_none()

        if txn:
            txn.status = NachTransactionStatus.SUCCESS
            txn.bank_reference = payment_id
            txn.return_code = NachReturnCode.SUCCESS
            txn.processed_at = datetime.utcnow()

            # Create receipt (similar to Razorpay handler)
            from app.models.lending.loan_account import LoanAccount
            loan_account = await db.get(LoanAccount, txn.loan_account_id)

            receipt = LoanReceipt(
                organization_id=loan_account.organization_id,
                loan_account_id=txn.loan_account_id,
                receipt_number=f"NACH/{txn.transaction_reference}",
                receipt_date=datetime.utcnow().date(),
                value_date=datetime.utcnow().date(),
                receipt_amount=txn.debit_amount,
                receipt_type=ReceiptType.REGULAR,
                receipt_mode=ReceiptMode.NACH,
                instrument_number=payment_id,
                instrument_date=datetime.utcnow().date(),
                mandate_id=txn.loan_mandate_id,
                status=ReceiptStatus.PENDING,
            )
            db.add(receipt)
            await db.flush()
            txn.receipt_id = receipt.id

            logger.info(f"Cashfree payment {cf_order_id} successful")


async def _handle_cashfree_payment_failed(db: AsyncSession, data: Dict):
    """Handle failed payment."""
    cf_order_id = data.get("payment", {}).get("order_id")
    error = data.get("error", {})

    if cf_order_id:
        query = select(NachTransaction).where(
            NachTransaction.transaction_reference == cf_order_id
        )
        result = await db.execute(query)
        txn = result.scalar_one_or_none()

        if txn:
            txn.status = NachTransactionStatus.BOUNCED
            txn.failure_reason = error.get("message", "Payment failed")
            txn.response_message = json.dumps(error)
            txn.processed_at = datetime.utcnow()

            # Check if retryable based on error code
            error_code = error.get("code", "")
            retryable_codes = {"INSUFFICIENT_BALANCE",}
            if error_code in retryable_codes:
                if txn.retry_count < txn.max_retries:
                    txn.status = NachTransactionStatus.RETRY_SCHEDULED
                    from datetime import timedelta
                    txn.next_retry_date = datetime.utcnow().date() + timedelta(days=7)

            logger.info(f"Cashfree payment {cf_order_id} failed: {error.get('message')}")
