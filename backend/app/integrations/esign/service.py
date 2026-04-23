"""eSign Service for managing document signing workflows."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.esign.base import (
    AuthMode,
    ESignError,
    ESignProvider,
    ESignRequest,
    ESignResponse,
    ESignStatus,
    Signer,
    SignerType,
)
from app.integrations.esign.aadhaar_esign import AadhaarESignProvider

logger = logging.getLogger(__name__)


class ESignService:
    """
    Unified eSign service for document signing.

    Features:
    - Multiple provider support
    - Document signing workflow management
    - Status tracking
    - Webhook handling
    """

    def __init__(
        self,
        db: Optional[AsyncSession] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        """Initialize eSign service."""
        self.db = db
        self.config = config or {}
        self._providers: Dict[str, ESignProvider] = {}
        self._initialize_providers()

    def _initialize_providers(self) -> None:
        """Initialize configured providers."""
        aadhaar_config = self.config.get("aadhaar_esign", {})
        if aadhaar_config.get("enabled"):
            try:
                self._providers["aadhaar"] = AadhaarESignProvider(aadhaar_config)
            except Exception as e:
                logger.error(f"Failed to initialize Aadhaar eSign: {e}")

    def _get_provider(self, auth_mode: AuthMode) -> Optional[ESignProvider]:
        """Get provider for auth mode."""
        if auth_mode in [AuthMode.AADHAAR_OTP, AuthMode.AADHAAR_BIOMETRIC]:
            return self._providers.get("aadhaar")
        return None

    async def create_signing_request(
        self,
        document_path: str,
        document_name: str,
        signers: List[Dict[str, Any]],
        organization_id: UUID,
        entity_type: str,
        entity_id: UUID,
        callback_url: Optional[str] = None,
        expiry_hours: int = 72,
    ) -> ESignResponse:
        """
        Create a document signing request.

        Args:
            document_path: Path to PDF document
            document_name: Display name of document
            signers: List of signer details
            organization_id: Organization ID
            entity_type: Entity type (loan_agreement, noc, etc.)
            entity_id: Entity ID
            callback_url: Webhook callback URL
            expiry_hours: Request expiry in hours

        Returns:
            ESignResponse with signing URL
        """
        # Convert signer dicts to Signer objects
        signer_objects = []
        for s in signers:
            signer_objects.append(
                Signer(
                    name=s["name"],
                    email=s["email"],
                    phone=s["phone"],
                    aadhaar_number=s.get("aadhaar_number"),
                    pan_number=s.get("pan_number"),
                    signer_type=SignerType(s.get("signer_type", "INDIVIDUAL")),
                    auth_mode=AuthMode(s.get("auth_mode", "AADHAAR_OTP")),
                    sign_positions=s.get("sign_positions", []),
                )
            )

        # Determine provider based on first signer's auth mode
        provider = self._get_provider(signer_objects[0].auth_mode)
        if not provider:
            raise ESignError(
                "No provider available for auth mode",
                code="NO_PROVIDER",
            )

        # Create request
        request = ESignRequest(
            document_id=f"{entity_type}_{entity_id}_{datetime.utcnow().timestamp()}",
            document_name=document_name,
            document_path=document_path,
            signers=signer_objects,
            organization_id=organization_id,
            entity_type=entity_type,
            entity_id=entity_id,
            callback_url=callback_url,
            expiry_hours=expiry_hours,
        )

        # Initiate signing
        response = await provider.initiate_signing(request)

        # Store request in database
        if self.db and response.success:
            await self._store_signing_request(request, response, provider.provider_name)

        return response

    async def send_signer_otp(
        self, request_id: str, signer_id: str
    ) -> bool:
        """Send OTP to signer."""
        # Determine provider from stored request
        provider = self._providers.get("aadhaar")
        if not provider:
            return False

        return await provider.send_otp(request_id, signer_id)

    async def verify_signer_otp(
        self, request_id: str, signer_id: str, otp: str
    ) -> ESignResponse:
        """Verify signer OTP and complete signing."""
        provider = self._providers.get("aadhaar")
        if not provider:
            raise ESignError("Provider not available", code="NO_PROVIDER")

        response = await provider.verify_otp(request_id, signer_id, otp)

        # Update database
        if self.db:
            await self._update_signing_status(request_id, response)

        return response

    async def get_signing_status(self, request_id: str) -> ESignResponse:
        """Get current status of signing request."""
        provider = self._providers.get("aadhaar")
        if not provider:
            raise ESignError("Provider not available", code="NO_PROVIDER")

        return await provider.get_status(request_id)

    async def download_signed_document(
        self, request_id: str, save_path: Optional[str] = None
    ) -> Optional[str]:
        """Download signed document."""
        provider = self._providers.get("aadhaar")
        if not provider:
            return None

        content = await provider.download_signed_document(request_id)
        if not content:
            return None

        if save_path:
            with open(save_path, "wb") as f:
                f.write(content)
            return save_path

        return None

    async def cancel_signing(self, request_id: str) -> bool:
        """Cancel signing request."""
        provider = self._providers.get("aadhaar")
        if not provider:
            return False

        result = await provider.cancel_request(request_id)

        if result and self.db:
            await self._update_signing_status(
                request_id,
                ESignResponse(
                    success=True,
                    request_id=request_id,
                    status=ESignStatus.CANCELLED,
                ),
            )

        return result

    async def handle_webhook(
        self, provider_name: str, payload: bytes, signature: str
    ) -> Dict[str, Any]:
        """Handle webhook from eSign provider."""
        provider = self._providers.get(provider_name)
        if not provider:
            return {"success": False, "error": "Unknown provider"}

        # Verify signature
        if not await provider.verify_webhook_signature(payload, signature):
            return {"success": False, "error": "Invalid signature"}

        # Parse and process webhook
        import json
        data = json.loads(payload.decode())

        event_type = data.get("event")
        request_id = data.get("requestId")

        logger.info(f"eSign webhook: {event_type} for {request_id}")

        # Update status based on event
        if event_type == "signing.completed":
            response = ESignResponse(
                success=True,
                request_id=request_id,
                status=ESignStatus.COMPLETED,
                signed_document_url=data.get("signedDocumentUrl"),
            )
        elif event_type == "signing.failed":
            response = ESignResponse(
                success=False,
                request_id=request_id,
                status=ESignStatus.FAILED,
                error_message=data.get("error"),
            )
        elif event_type == "signing.expired":
            response = ESignResponse(
                success=False,
                request_id=request_id,
                status=ESignStatus.EXPIRED,
            )
        else:
            return {"success": True, "message": "Event not handled"}

        if self.db:
            await self._update_signing_status(request_id, response)

        return {"success": True, "status": response.status.value}

    async def _store_signing_request(
        self,
        request: ESignRequest,
        response: ESignResponse,
        provider_name: str,
    ) -> None:
        """Store signing request in database."""
        # TODO: Create ESignRequest model and store
        pass

    async def _update_signing_status(
        self, request_id: str, response: ESignResponse
    ) -> None:
        """Update signing request status in database."""
        # TODO: Update ESignRequest model
        pass


# Convenience functions

async def sign_loan_agreement(
    db: AsyncSession,
    loan_account_id: UUID,
    agreement_path: str,
    borrower_details: Dict[str, Any],
    organization_id: UUID,
    config: Dict[str, Any],
) -> ESignResponse:
    """
    Sign loan agreement using eSign.

    Args:
        db: Database session
        loan_account_id: Loan account ID
        agreement_path: Path to agreement PDF
        borrower_details: Borrower details (name, phone, aadhaar)
        organization_id: Organization ID
        config: eSign configuration

    Returns:
        ESignResponse
    """
    service = ESignService(db=db, config=config)

    return await service.create_signing_request(
        document_path=agreement_path,
        document_name="Loan Agreement",
        signers=[
            {
                "name": borrower_details["name"],
                "email": borrower_details.get("email", ""),
                "phone": borrower_details["phone"],
                "aadhaar_number": borrower_details.get("aadhaar"),
                "auth_mode": "AADHAAR_OTP",
                "sign_positions": [
                    {"page": 1, "x": 100, "y": 700},  # Example position
                ],
            }
        ],
        organization_id=organization_id,
        entity_type="loan_agreement",
        entity_id=loan_account_id,
    )
