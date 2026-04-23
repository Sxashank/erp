"""Account Aggregator webhook handlers for receiving provider notifications."""

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
from app.models.lending.aa_consent import AAConsent, AAFetchSession
from app.models.lending.enums import AAConsentStatus, AAFetchSessionStatus
from app.models.core.integration_config import IntegrationConfig, IntegrationType
from app.services.lending.aa_service import AAService

logger = logging.getLogger(__name__)

router = APIRouter()


# =============================================================================
# Finvu Webhooks
# =============================================================================


@router.post("/finvu")
async def finvu_webhook(
    request: Request,
    x_finvu_signature: Optional[str] = Header(None),
    x_finvu_timestamp: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Handle Finvu AA webhooks.

    Events handled:
    - Consent/Notification: Consent status updates
    - FI/Notification: FI data ready notification
    """
    body = await request.body()
    payload = await request.json()

    # Get integration config for webhook secret
    query = select(IntegrationConfig).where(
        and_(
            IntegrationConfig.integration_type == IntegrationType.ACCOUNT_AGGREGATOR,
            IntegrationConfig.provider == "FINVU",
            IntegrationConfig.is_active == True,
        )
    )
    result = await db.execute(query)
    config = result.scalar_one_or_none()

    # Verify signature if configured
    if config and config.webhook_secret and x_finvu_signature:
        timestamp = x_finvu_timestamp or ""
        signature_data = f"{timestamp}.{body.decode()}"
        expected = hmac.new(
            config.webhook_secret.encode(),
            signature_data.encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected, x_finvu_signature):
            logger.warning("Invalid Finvu webhook signature")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature",
            )

    # Determine notification type
    notification_type = _determine_finvu_notification_type(payload)
    logger.info(f"Finvu webhook received: {notification_type}")

    try:
        service = AAService(db)

        if notification_type == "CONSENT_STATUS":
            await _handle_finvu_consent_notification(service, payload)
        elif notification_type == "FI_NOTIFICATION":
            await _handle_finvu_fi_notification(service, payload)
        else:
            logger.info(f"Unhandled Finvu notification type: {notification_type}")

        await db.commit()

    except Exception as e:
        logger.error(f"Error processing Finvu webhook: {e}")
        await db.rollback()
        # Don't raise - return 200 to prevent retries for processing errors

    return {"ver": "2.0.0", "timestamp": datetime.utcnow().isoformat() + "Z", "txnid": payload.get("txnid", "")}


def _determine_finvu_notification_type(payload: Dict[str, Any]) -> str:
    """Determine the type of Finvu notification."""
    if "ConsentStatusNotification" in payload:
        return "CONSENT_STATUS"
    elif "FIStatusNotification" in payload or "FIStatusResponse" in payload:
        return "FI_NOTIFICATION"
    elif payload.get("consentStatus"):
        return "CONSENT_STATUS"
    elif payload.get("sessionStatus") or payload.get("FI"):
        return "FI_NOTIFICATION"
    return "UNKNOWN"


async def _handle_finvu_consent_notification(service: AAService, payload: Dict[str, Any]):
    """Handle Finvu consent status notification."""
    notification = payload.get("ConsentStatusNotification", payload)

    consent_handle = notification.get("consentHandle", notification.get("ConsentHandle"))
    consent_id = notification.get("consentId", notification.get("ConsentId"))
    consent_status = notification.get("consentStatus", notification.get("status", ""))

    if consent_handle:
        await service.handle_consent_notification(
            consent_handle=consent_handle,
            consent_id=consent_id,
            status=consent_status,
            raw_payload=payload,
        )
        logger.info(f"Finvu consent {consent_handle} status updated to {consent_status}")


async def _handle_finvu_fi_notification(service: AAService, payload: Dict[str, Any]):
    """Handle Finvu FI data notification."""
    notification = payload.get("FIStatusNotification", payload)

    consent_id = notification.get("consentId", notification.get("Consent", {}).get("id", ""))
    session_id = notification.get("sessionId", notification.get("SessionId", ""))
    session_status = notification.get("sessionStatus", notification.get("status", ""))
    fi_status_response = notification.get("FIStatusResponse", [])

    if session_id:
        await service.handle_fi_notification(
            consent_id=consent_id,
            session_id=session_id,
            status=session_status,
            fi_status_response=fi_status_response,
            raw_payload=payload,
        )
        logger.info(f"Finvu FI session {session_id} status: {session_status}")


# =============================================================================
# Setu Webhooks
# =============================================================================


@router.post("/setu")
async def setu_webhook(
    request: Request,
    x_setu_signature: Optional[str] = Header(None),
    x_setu_timestamp: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Handle Setu AA webhooks.

    Events handled:
    - consent.status: Consent status updates
    - data.ready: FI data ready notification
    - session.status: Session status updates
    """
    body = await request.body()
    payload = await request.json()

    # Get integration config
    query = select(IntegrationConfig).where(
        and_(
            IntegrationConfig.integration_type == IntegrationType.ACCOUNT_AGGREGATOR,
            IntegrationConfig.provider == "SETU",
            IntegrationConfig.is_active == True,
        )
    )
    result = await db.execute(query)
    config = result.scalar_one_or_none()

    # Verify signature
    if config and config.webhook_secret and x_setu_signature:
        timestamp = x_setu_timestamp or ""
        signature_data = f"{timestamp}.{body.decode()}"
        expected = hmac.new(
            config.webhook_secret.encode(),
            signature_data.encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected, x_setu_signature):
            logger.warning("Invalid Setu webhook signature")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature",
            )

    event_type = payload.get("event", payload.get("type", ""))
    data = payload.get("data", payload)

    logger.info(f"Setu webhook received: {event_type}")

    try:
        service = AAService(db)

        if event_type in ("consent.status", "CONSENT_STATUS_UPDATE"):
            await _handle_setu_consent_notification(service, data)
        elif event_type in ("data.ready", "FI_DATA_READY", "session.status"):
            await _handle_setu_fi_notification(service, data)
        else:
            logger.info(f"Unhandled Setu event: {event_type}")

        await db.commit()

    except Exception as e:
        logger.error(f"Error processing Setu webhook: {e}")
        await db.rollback()

    return {"status": "ok", "received_at": datetime.utcnow().isoformat()}


async def _handle_setu_consent_notification(service: AAService, data: Dict[str, Any]):
    """Handle Setu consent status notification."""
    consent_id = data.get("id") or data.get("consentId")
    consent_handle = data.get("handle") or data.get("consentHandle") or consent_id
    consent_status = data.get("status", "")

    if consent_handle:
        await service.handle_consent_notification(
            consent_handle=consent_handle,
            consent_id=consent_id if consent_id != consent_handle else None,
            status=consent_status,
            raw_payload=data,
        )
        logger.info(f"Setu consent {consent_handle} status updated to {consent_status}")


async def _handle_setu_fi_notification(service: AAService, data: Dict[str, Any]):
    """Handle Setu FI data notification."""
    consent_id = data.get("consentId", "")
    session_id = data.get("sessionId") or data.get("id", "")
    session_status = data.get("status", "READY")
    fi_status = data.get("fiStatusResponse", [])

    if session_id:
        await service.handle_fi_notification(
            consent_id=consent_id,
            session_id=session_id,
            status=session_status,
            fi_status_response=fi_status,
            raw_payload=data,
        )
        logger.info(f"Setu FI session {session_id} status: {session_status}")


# =============================================================================
# OneMoney Webhooks
# =============================================================================


@router.post("/onemoney")
async def onemoney_webhook(
    request: Request,
    x_onemoney_signature: Optional[str] = Header(None),
    x_onemoney_timestamp: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Handle OneMoney AA webhooks.

    Events handled:
    - Consent/Notification: Consent status updates
    - FI/Notification: FI data ready notification
    """
    body = await request.body()
    payload = await request.json()

    # Get integration config
    query = select(IntegrationConfig).where(
        and_(
            IntegrationConfig.integration_type == IntegrationType.ACCOUNT_AGGREGATOR,
            IntegrationConfig.provider == "ONEMONEY",
            IntegrationConfig.is_active == True,
        )
    )
    result = await db.execute(query)
    config = result.scalar_one_or_none()

    # Verify signature
    if config and config.webhook_secret and x_onemoney_signature:
        timestamp = x_onemoney_timestamp or ""
        signature_data = f"{timestamp}.{body.decode()}"
        expected = hmac.new(
            config.webhook_secret.encode(),
            signature_data.encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected, x_onemoney_signature):
            logger.warning("Invalid OneMoney webhook signature")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature",
            )

    # OneMoney uses AA 2.0 spec format
    notification_type = _determine_onemoney_notification_type(payload)
    logger.info(f"OneMoney webhook received: {notification_type}")

    try:
        service = AAService(db)

        if notification_type == "CONSENT_STATUS":
            await _handle_onemoney_consent_notification(service, payload)
        elif notification_type == "FI_NOTIFICATION":
            await _handle_onemoney_fi_notification(service, payload)
        else:
            logger.info(f"Unhandled OneMoney notification type: {notification_type}")

        await db.commit()

    except Exception as e:
        logger.error(f"Error processing OneMoney webhook: {e}")
        await db.rollback()

    return {"ver": "2.0.0", "timestamp": datetime.utcnow().isoformat() + "Z", "txnid": payload.get("txnid", "")}


def _determine_onemoney_notification_type(payload: Dict[str, Any]) -> str:
    """Determine the type of OneMoney notification."""
    if "ConsentStatusNotification" in payload or payload.get("notificationType") == "CONSENT_STATUS":
        return "CONSENT_STATUS"
    elif "FIStatusNotification" in payload or payload.get("notificationType") == "FI_NOTIFICATION":
        return "FI_NOTIFICATION"
    elif "consentStatus" in payload or "ConsentStatus" in payload:
        return "CONSENT_STATUS"
    elif "sessionId" in payload or "SessionId" in payload:
        return "FI_NOTIFICATION"
    return "UNKNOWN"


async def _handle_onemoney_consent_notification(service: AAService, payload: Dict[str, Any]):
    """Handle OneMoney consent status notification."""
    notification = payload.get("ConsentStatusNotification", payload)

    consent_handle = notification.get("consentHandle") or notification.get("ConsentHandle")
    consent_id = notification.get("consentId") or notification.get("ConsentId")
    consent_status = notification.get("consentStatus") or notification.get("status", "")

    if consent_handle:
        await service.handle_consent_notification(
            consent_handle=consent_handle,
            consent_id=consent_id,
            status=consent_status,
            raw_payload=payload,
        )
        logger.info(f"OneMoney consent {consent_handle} status updated to {consent_status}")


async def _handle_onemoney_fi_notification(service: AAService, payload: Dict[str, Any]):
    """Handle OneMoney FI data notification."""
    notification = payload.get("FIStatusNotification", payload)

    consent_id = notification.get("consentId") or notification.get("Consent", {}).get("id", "")
    session_id = notification.get("sessionId") or notification.get("SessionId", "")
    session_status = notification.get("sessionStatus") or notification.get("status", "")
    fi_status_response = notification.get("FIStatusResponse", [])

    if session_id:
        await service.handle_fi_notification(
            consent_id=consent_id,
            session_id=session_id,
            status=session_status,
            fi_status_response=fi_status_response,
            raw_payload=payload,
        )
        logger.info(f"OneMoney FI session {session_id} status: {session_status}")


# =============================================================================
# Generic AA Webhook (for testing or custom providers)
# =============================================================================


@router.post("/generic")
async def generic_aa_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Generic AA webhook handler for testing or custom providers.

    Attempts to parse the payload in common AA formats.
    """
    payload = await request.json()

    logger.info(f"Generic AA webhook received: {json.dumps(payload)[:500]}")

    try:
        service = AAService(db)

        # Try to determine the notification type
        consent_handle = (
            payload.get("consentHandle") or
            payload.get("ConsentHandle") or
            payload.get("consent_handle") or
            payload.get("data", {}).get("consentHandle")
        )
        consent_id = (
            payload.get("consentId") or
            payload.get("ConsentId") or
            payload.get("consent_id") or
            payload.get("data", {}).get("consentId")
        )
        session_id = (
            payload.get("sessionId") or
            payload.get("SessionId") or
            payload.get("session_id") or
            payload.get("data", {}).get("sessionId")
        )
        status_value = (
            payload.get("consentStatus") or
            payload.get("status") or
            payload.get("Status") or
            payload.get("data", {}).get("status", "")
        )

        # Handle based on what identifiers are present
        if consent_handle and not session_id:
            # Consent notification
            await service.handle_consent_notification(
                consent_handle=consent_handle,
                consent_id=consent_id,
                status=status_value,
                raw_payload=payload,
            )
            logger.info(f"Generic webhook: consent {consent_handle} status updated")
        elif session_id:
            # FI notification
            fi_status = payload.get("FIStatusResponse", payload.get("fiStatusResponse", []))
            await service.handle_fi_notification(
                consent_id=consent_id or "",
                session_id=session_id,
                status=status_value or "READY",
                fi_status_response=fi_status,
                raw_payload=payload,
            )
            logger.info(f"Generic webhook: FI session {session_id} notification processed")
        else:
            logger.warning(f"Generic webhook: could not determine notification type")

        await db.commit()

    except Exception as e:
        logger.error(f"Error processing generic AA webhook: {e}")
        await db.rollback()

    return {"status": "ok", "received_at": datetime.utcnow().isoformat()}
