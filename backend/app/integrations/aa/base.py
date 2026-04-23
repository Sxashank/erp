"""Base class for Account Aggregator clients."""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import httpx

from app.integrations.aa.schemas import (
    AAConsentRequest,
    AAConsentResponse,
    AAFetchRequest,
    AAFetchResponse,
    AAFIData,
    AANotification,
    AAHealthCheckResponse,
)

logger = logging.getLogger(__name__)


class AAClientBase(ABC):
    """Abstract base class for Account Aggregator provider clients.

    Implements the FIU (Financial Information User) interface for the
    Account Aggregator ecosystem as per RBI regulations.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        sandbox_mode: bool = True,
    ):
        """Initialize the AA client.

        Args:
            config: Provider-specific configuration including:
                - client_id: FIU client ID
                - client_secret: FIU secret
                - entity_id: FIU entity ID registered with AA
                - api_base_url: Provider API base URL
                - token_url: OAuth token endpoint
                - callback_url: Webhook callback URL
            sandbox_mode: Whether to use sandbox/test environment
        """
        self.config = config
        self.sandbox_mode = sandbox_mode
        self.client_id = config.get("client_id", "")
        self.client_secret = config.get("client_secret", "")
        self.entity_id = config.get("entity_id", "")
        self.callback_url = config.get("callback_url", "")
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None

        # Set API URLs based on mode
        if sandbox_mode:
            self.base_url = config.get("sandbox_url", config.get("api_base_url", ""))
            self.token_url = config.get("sandbox_token_url", config.get("token_url", ""))
        else:
            self.base_url = config.get("api_base_url", "")
            self.token_url = config.get("token_url", "")

    @abstractmethod
    async def get_access_token(self) -> str:
        """Get or refresh OAuth access token.

        Returns:
            Access token string
        """
        pass

    @abstractmethod
    async def create_consent(
        self,
        request: AAConsentRequest,
    ) -> AAConsentResponse:
        """Create a consent request.

        Args:
            request: Consent request parameters

        Returns:
            Consent response with handle and redirect URL
        """
        pass

    @abstractmethod
    async def get_consent_status(
        self,
        consent_handle: str,
    ) -> AAConsentResponse:
        """Get current status of a consent request.

        Args:
            consent_handle: The consent handle from create_consent

        Returns:
            Current consent status
        """
        pass

    @abstractmethod
    async def fetch_consent_artifact(
        self,
        consent_id: str,
    ) -> Dict[str, Any]:
        """Fetch the signed consent artifact after approval.

        Args:
            consent_id: The consent ID (received after approval)

        Returns:
            Signed consent artifact
        """
        pass

    @abstractmethod
    async def initiate_fi_request(
        self,
        request: AAFetchRequest,
    ) -> AAFetchResponse:
        """Initiate a Financial Information fetch request.

        Args:
            request: FI request parameters

        Returns:
            Session information for the FI request
        """
        pass

    @abstractmethod
    async def fetch_fi_data(
        self,
        session_id: str,
        consent_id: str,
    ) -> AAFetchResponse:
        """Fetch the actual financial data for a session.

        Args:
            session_id: The data session ID
            consent_id: The consent ID

        Returns:
            Fetched financial data
        """
        pass

    @abstractmethod
    async def decrypt_fi_data(
        self,
        encrypted_data: Dict[str, Any],
        key_material: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Decrypt the received FI data.

        Args:
            encrypted_data: Encrypted data from FIP
            key_material: Key material for decryption

        Returns:
            Decrypted financial data
        """
        pass

    async def revoke_consent(
        self,
        consent_id: str,
        reason: Optional[str] = None,
    ) -> AAConsentResponse:
        """Revoke an active consent.

        Args:
            consent_id: The consent ID to revoke
            reason: Optional reason for revocation

        Returns:
            Updated consent status
        """
        # Default implementation - override if provider has specific API
        logger.warning(f"Consent revocation not implemented for this provider")
        return AAConsentResponse(
            success=False,
            error_message="Consent revocation not implemented",
        )

    async def health_check(self) -> AAHealthCheckResponse:
        """Check provider API health.

        Returns:
            Health check response
        """
        start_time = datetime.utcnow()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/health")
                response_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

                if response.status_code == 200:
                    return AAHealthCheckResponse(
                        is_healthy=True,
                        provider=self.__class__.__name__,
                        response_time_ms=response_time,
                        timestamp=datetime.utcnow(),
                    )
                return AAHealthCheckResponse(
                    is_healthy=False,
                    provider=self.__class__.__name__,
                    response_time_ms=response_time,
                    timestamp=datetime.utcnow(),
                    error_message=f"Status code: {response.status_code}",
                )
        except Exception as e:
            response_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            return AAHealthCheckResponse(
                is_healthy=False,
                provider=self.__class__.__name__,
                response_time_ms=response_time,
                timestamp=datetime.utcnow(),
                error_message=str(e),
            )

    def verify_webhook_signature(
        self,
        payload: bytes,
        signature: str,
        timestamp: str,
    ) -> bool:
        """Verify webhook signature.

        Args:
            payload: Raw webhook payload
            signature: Signature from header
            timestamp: Timestamp from header

        Returns:
            True if signature is valid
        """
        # Default implementation - override for provider-specific verification
        webhook_secret = self.config.get("webhook_secret")
        if not webhook_secret:
            logger.warning("No webhook secret configured, skipping verification")
            return True

        # Implement HMAC verification
        import hmac
        import hashlib

        expected_signature = hmac.new(
            webhook_secret.encode(),
            f"{timestamp}.{payload.decode()}".encode(),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)

    def parse_notification(
        self,
        payload: Dict[str, Any],
    ) -> AANotification:
        """Parse webhook notification payload.

        Args:
            payload: Raw notification payload

        Returns:
            Parsed notification object
        """
        # Default implementation - override for provider-specific parsing
        notification_type = payload.get("type", payload.get("notificationType", "UNKNOWN"))

        return AANotification(
            notification_type=notification_type,
            timestamp=datetime.utcnow(),
            consent_handle=payload.get("consentHandle"),
            consent_id=payload.get("consentId"),
            session_id=payload.get("sessionId"),
            status=payload.get("status"),
            fi_status_response=payload.get("FIStatusResponse"),
            payload=payload,
        )

    def _get_purpose_code(self, purpose: str) -> str:
        """Map purpose string to AA purpose code.

        Purpose codes as per AA spec:
        - 101: Wealth Management
        - 102: Customer Spending Patterns
        - 103: Aggregated Statement
        - 104: Explicit Consent for Data
        - 105: Personal Finance Management
        """
        purpose_map = {
            "WEALTH_MANAGEMENT": "101",
            "UNDERWRITING": "102",
            "MONITORING": "103",
            "BANK_STATEMENT_ANALYSIS": "103",
            "INCOME_VERIFICATION": "102",
            "ACCOUNT_AGGREGATION": "103",
            "TAX_FILING": "104",
        }
        return purpose_map.get(purpose, "102")

    def _get_fi_type_code(self, fi_type: str) -> str:
        """Map FI type to AA FI type code."""
        fi_type_map = {
            "DEPOSIT": "DEPOSIT",
            "TERM_DEPOSIT": "TERM_DEPOSIT",
            "RECURRING_DEPOSIT": "RECURRING_DEPOSIT",
            "SIP": "SIP",
            "CP": "CP",
            "GOVT_SECURITIES": "GOVT_SECURITIES",
            "EQUITIES": "EQUITIES",
            "BONDS": "BONDS",
            "DEBENTURES": "DEBENTURES",
            "MUTUAL_FUNDS": "MUTUAL_FUNDS",
            "ETF": "ETF",
            "IDR": "IDR",
            "CIS": "CIS",
            "AIF": "AIF",
            "INSURANCE_POLICIES": "INSURANCE_POLICIES",
            "NPS": "NPS",
            "INVIT": "INVIT",
            "REIT": "REIT",
            "GSTR1_3B": "GSTR1_3B",
        }
        return fi_type_map.get(fi_type, fi_type)
