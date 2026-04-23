"""Aadhaar eSign Provider Implementation.

Integrates with UIDAI-approved eSign ASPs (Application Service Providers)
like NSDL, eMudhra, Sify, etc.
"""

import base64
import hashlib
import hmac
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

from app.integrations.esign.base import (
    AuthMode,
    ESignError,
    ESignProvider,
    ESignRequest,
    ESignResponse,
    ESignStatus,
    Signer,
)

logger = logging.getLogger(__name__)


class AadhaarESignProvider(ESignProvider):
    """
    Aadhaar eSign provider using UIDAI-approved ASP.

    Implements eSign 2.1 API specification.
    """

    provider_name = "aadhaar_esign"

    def _validate_config(self) -> None:
        """Validate Aadhaar eSign configuration."""
        required = ["asp_id", "api_key", "base_url", "aua_code", "sub_aua_code"]
        for key in required:
            if key not in self.config:
                raise ESignError(
                    f"Missing required config: {key}",
                    code="CONFIG_ERROR",
                    provider=self.provider_name,
                )

    def _get_headers(self) -> Dict[str, str]:
        """Get API headers."""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config['api_key']}",
            "X-ASP-ID": self.config["asp_id"],
        }

    async def initiate_signing(self, request: ESignRequest) -> ESignResponse:
        """
        Initiate Aadhaar eSign request.

        Steps:
        1. Upload document to ASP
        2. Create signing request with signer details
        3. Return signing URL for each signer
        """
        base_url = self.config["base_url"]

        # Read document
        try:
            with open(request.document_path, "rb") as f:
                document_content = f.read()
            document_hash = hashlib.sha256(document_content).hexdigest()
            document_base64 = base64.b64encode(document_content).decode()
        except Exception as e:
            raise ESignError(
                f"Failed to read document: {str(e)}",
                code="DOCUMENT_ERROR",
                provider=self.provider_name,
            )

        # Build signing request
        payload = {
            "document": {
                "name": request.document_name,
                "content": document_base64,
                "contentType": "application/pdf",
                "hash": document_hash,
            },
            "signers": [
                {
                    "name": signer.name,
                    "email": signer.email,
                    "phone": signer.phone,
                    "aadhaar": self._mask_aadhaar(signer.aadhaar_number),
                    "authMode": signer.auth_mode.value,
                    "signPositions": signer.sign_positions,
                }
                for signer in request.signers
            ],
            "auaCode": self.config["aua_code"],
            "subAuaCode": self.config["sub_aua_code"],
            "txnId": request.document_id,
            "consent": True,
            "consentText": "I hereby authorize the use of my Aadhaar for eSign",
            "responseUrl": request.callback_url,
            "expiry": (
                datetime.utcnow() + timedelta(hours=request.expiry_hours)
            ).isoformat(),
            "metadata": request.metadata,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{base_url}/esign/v2.1/init",
                    json=payload,
                    headers=self._get_headers(),
                    timeout=60.0,
                )

                data = response.json()

                if response.status_code == 200 and data.get("success"):
                    return ESignResponse(
                        success=True,
                        request_id=request.document_id,
                        provider_request_id=data.get("requestId"),
                        status=ESignStatus.INITIATED,
                        signing_url=data.get("signingUrl"),
                        signers_status=[
                            {
                                "signer_id": s.get("signerId"),
                                "name": s.get("name"),
                                "status": "PENDING",
                                "signing_url": s.get("signingUrl"),
                            }
                            for s in data.get("signers", [])
                        ],
                        created_at=datetime.utcnow(),
                        metadata={
                            "document_hash": document_hash,
                            "expiry": payload["expiry"],
                        },
                    )
                else:
                    error = data.get("error", {})
                    return ESignResponse(
                        success=False,
                        status=ESignStatus.FAILED,
                        error_code=error.get("code"),
                        error_message=error.get("message"),
                    )

        except Exception as e:
            raise ESignError(
                f"Failed to initiate eSign: {str(e)}",
                code="INIT_ERROR",
                provider=self.provider_name,
            )

    async def send_otp(self, request_id: str, signer_id: str) -> bool:
        """Send OTP to signer's Aadhaar-linked mobile."""
        base_url = self.config["base_url"]

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{base_url}/esign/v2.1/otp/send",
                    json={
                        "requestId": request_id,
                        "signerId": signer_id,
                    },
                    headers=self._get_headers(),
                    timeout=30.0,
                )

                data = response.json()
                return data.get("success", False)

        except Exception as e:
            logger.error(f"Failed to send OTP: {e}")
            return False

    async def verify_otp(
        self, request_id: str, signer_id: str, otp: str
    ) -> ESignResponse:
        """Verify OTP and complete signing for signer."""
        base_url = self.config["base_url"]

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{base_url}/esign/v2.1/otp/verify",
                    json={
                        "requestId": request_id,
                        "signerId": signer_id,
                        "otp": otp,
                    },
                    headers=self._get_headers(),
                    timeout=60.0,
                )

                data = response.json()

                if data.get("success"):
                    return ESignResponse(
                        success=True,
                        request_id=request_id,
                        status=ESignStatus.COMPLETED
                        if data.get("allSigned")
                        else ESignStatus.SIGNING,
                        signed_document_path=data.get("signedDocumentPath"),
                        signed_document_url=data.get("signedDocumentUrl"),
                        certificate_info=data.get("certificate"),
                    )
                else:
                    return ESignResponse(
                        success=False,
                        request_id=request_id,
                        status=ESignStatus.FAILED,
                        error_code=data.get("error", {}).get("code"),
                        error_message=data.get("error", {}).get("message"),
                    )

        except Exception as e:
            raise ESignError(
                f"Failed to verify OTP: {str(e)}",
                code="OTP_VERIFY_ERROR",
                provider=self.provider_name,
            )

    async def get_status(self, request_id: str) -> ESignResponse:
        """Get signing request status."""
        base_url = self.config["base_url"]

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{base_url}/esign/v2.1/status/{request_id}",
                    headers=self._get_headers(),
                    timeout=30.0,
                )

                data = response.json()

                status_map = {
                    "INITIATED": ESignStatus.INITIATED,
                    "OTP_SENT": ESignStatus.OTP_SENT,
                    "SIGNING": ESignStatus.SIGNING,
                    "COMPLETED": ESignStatus.COMPLETED,
                    "FAILED": ESignStatus.FAILED,
                    "EXPIRED": ESignStatus.EXPIRED,
                    "CANCELLED": ESignStatus.CANCELLED,
                }

                return ESignResponse(
                    success=True,
                    request_id=request_id,
                    provider_request_id=data.get("providerRequestId"),
                    status=status_map.get(
                        data.get("status"), ESignStatus.INITIATED
                    ),
                    signed_document_path=data.get("signedDocumentPath"),
                    signed_document_url=data.get("signedDocumentUrl"),
                    signers_status=data.get("signers", []),
                    certificate_info=data.get("certificate"),
                    completed_at=datetime.fromisoformat(data["completedAt"])
                    if data.get("completedAt")
                    else None,
                )

        except Exception as e:
            raise ESignError(
                f"Failed to get status: {str(e)}",
                code="STATUS_ERROR",
                provider=self.provider_name,
            )

    async def download_signed_document(
        self, request_id: str
    ) -> Optional[bytes]:
        """Download signed document."""
        base_url = self.config["base_url"]

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{base_url}/esign/v2.1/document/{request_id}",
                    headers=self._get_headers(),
                    timeout=60.0,
                )

                if response.status_code == 200:
                    return response.content
                else:
                    logger.error(f"Failed to download document: {response.status_code}")
                    return None

        except Exception as e:
            logger.error(f"Failed to download document: {e}")
            return None

    async def cancel_request(self, request_id: str) -> bool:
        """Cancel signing request."""
        base_url = self.config["base_url"]

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{base_url}/esign/v2.1/cancel",
                    json={"requestId": request_id},
                    headers=self._get_headers(),
                    timeout=30.0,
                )

                data = response.json()
                return data.get("success", False)

        except Exception as e:
            logger.error(f"Failed to cancel request: {e}")
            return False

    async def verify_webhook_signature(
        self, payload: bytes, signature: str
    ) -> bool:
        """Verify webhook signature."""
        webhook_secret = self.config.get("webhook_secret", "")
        if not webhook_secret:
            return False

        expected = hmac.new(
            webhook_secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected, signature)

    def _mask_aadhaar(self, aadhaar: Optional[str]) -> Optional[str]:
        """Mask Aadhaar number for logging/display."""
        if not aadhaar:
            return None
        # Only send last 4 digits for initiation, full number sent during OTP
        return f"XXXX-XXXX-{aadhaar[-4:]}"

    async def verify_aadhaar(self, aadhaar: str, otp: str) -> Dict[str, Any]:
        """
        Verify Aadhaar number using OTP.

        This is for eKYC verification, not signing.
        """
        base_url = self.config["base_url"]

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{base_url}/ekyc/v2/verify",
                    json={
                        "aadhaar": aadhaar,
                        "otp": otp,
                        "auaCode": self.config["aua_code"],
                    },
                    headers=self._get_headers(),
                    timeout=60.0,
                )

                data = response.json()

                if data.get("success"):
                    return {
                        "verified": True,
                        "name": data.get("name"),
                        "dob": data.get("dob"),
                        "gender": data.get("gender"),
                        "address": data.get("address"),
                        "photo": data.get("photo"),  # Base64 encoded
                    }
                else:
                    return {
                        "verified": False,
                        "error": data.get("error", {}).get("message"),
                    }

        except Exception as e:
            return {"verified": False, "error": str(e)}
