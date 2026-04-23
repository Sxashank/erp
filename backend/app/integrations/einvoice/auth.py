"""E-Invoice IRP Authentication Manager.

Handles authentication with the E-Invoice IRP (Invoice Registration Portal):
- Token generation
- Request signing
- Response decryption
"""

import base64
import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

import httpx
from Crypto.Cipher import AES
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from Crypto.Random import get_random_bytes

logger = logging.getLogger(__name__)


class EInvoiceAuthManager:
    """Authentication manager for E-Invoice IRP APIs.

    Supports NIC and GSP-based E-Invoice generation.
    Handles encryption/decryption as per IRP specifications.
    """

    # NIC IRP URLs
    NIC_PROD_URL = "https://einv-apisandbox.nic.in"  # Production placeholder
    NIC_SANDBOX_URL = "https://einv-apisandbox.nic.in"

    # GSP URLs (ClearTax example)
    GSP_PROD_URL = "https://api.cleartax.in/einvoice/v1"
    GSP_SANDBOX_URL = "https://api-sandbox.cleartax.in/einvoice/v1"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        username: str,
        password: str,
        gstin: str,
        public_key_pem: Optional[str] = None,
        sandbox_mode: bool = True,
        provider: str = "NIC",
    ):
        """Initialize E-Invoice Auth Manager.

        Args:
            client_id: API client ID (ASP ID for NIC)
            client_secret: API client secret
            username: E-Invoice portal username
            password: E-Invoice portal password
            gstin: GSTIN for authentication
            public_key_pem: Public key for encryption (NIC)
            sandbox_mode: Whether to use sandbox environment
            provider: Provider type (NIC/CLEARTAX/etc.)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self.gstin = gstin
        self.public_key_pem = public_key_pem
        self.sandbox_mode = sandbox_mode
        self.provider = provider

        # Set base URL based on provider
        if provider == "NIC":
            self.base_url = self.NIC_SANDBOX_URL if sandbox_mode else self.NIC_PROD_URL
        else:
            self.base_url = self.GSP_SANDBOX_URL if sandbox_mode else self.GSP_PROD_URL

        self._client = httpx.AsyncClient(timeout=60.0)
        self._auth_token: Optional[str] = None
        self._sek: Optional[bytes] = None
        self._token_expiry: Optional[datetime] = None

    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()

    def _generate_app_key(self) -> Tuple[bytes, str]:
        """Generate application key for session.

        Returns:
            Tuple of (raw_app_key, encrypted_app_key_b64)
        """
        # Generate 32-byte random app key
        app_key = get_random_bytes(32)

        if self.public_key_pem:
            # Encrypt with NIC public key
            rsa_key = RSA.import_key(self.public_key_pem)
            cipher = PKCS1_v1_5.new(rsa_key)
            encrypted_app_key = cipher.encrypt(app_key)
            encrypted_app_key_b64 = base64.b64encode(encrypted_app_key).decode()
        else:
            # For GSP, app key might not need encryption
            encrypted_app_key_b64 = base64.b64encode(app_key).decode()

        return app_key, encrypted_app_key_b64

    def _encrypt_password(self, password: str, app_key: bytes) -> str:
        """Encrypt password with app key using AES.

        Args:
            password: Plain text password
            app_key: AES encryption key

        Returns:
            Base64 encoded encrypted password
        """
        # Pad password to 16-byte boundary
        padded = password + (16 - len(password) % 16) * chr(16 - len(password) % 16)

        # Encrypt with AES-256-ECB
        cipher = AES.new(app_key, AES.MODE_ECB)
        encrypted = cipher.encrypt(padded.encode())

        return base64.b64encode(encrypted).decode()

    def _decrypt_sek(self, encrypted_sek_b64: str, app_key: bytes) -> bytes:
        """Decrypt Session Encryption Key.

        Args:
            encrypted_sek_b64: Base64 encoded encrypted SEK
            app_key: Application key used for decryption

        Returns:
            Decrypted SEK bytes
        """
        encrypted_sek = base64.b64decode(encrypted_sek_b64)
        cipher = AES.new(app_key, AES.MODE_ECB)
        decrypted = cipher.decrypt(encrypted_sek)

        # Remove PKCS7 padding
        pad_len = decrypted[-1]
        return decrypted[:-pad_len]

    async def authenticate(self) -> Dict[str, Any]:
        """Authenticate with E-Invoice IRP and get auth token.

        Returns:
            Authentication result with token and SEK
        """
        # Generate app key
        app_key, encrypted_app_key = self._generate_app_key()

        # Encrypt password
        encrypted_password = self._encrypt_password(self.password, app_key)

        headers = {
            "Content-Type": "application/json",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "gstin": self.gstin,
        }

        payload = {
            "UserName": self.username,
            "Password": encrypted_password,
            "AppKey": encrypted_app_key,
            "ForceRefreshAccessToken": False,
        }

        try:
            response = await self._client.post(
                f"{self.base_url}/eivital/v1.04/auth",
                headers=headers,
                json={"Data": base64.b64encode(json.dumps(payload).encode()).decode()},
            )

            result = response.json()

            if result.get("Status") == 1:
                data = result.get("Data", {})

                # Decrypt SEK
                encrypted_sek = data.get("Sek")
                if encrypted_sek:
                    self._sek = self._decrypt_sek(encrypted_sek, app_key)

                self._auth_token = data.get("AuthToken")
                self._token_expiry = datetime.utcnow() + timedelta(hours=6)

                return {
                    "success": True,
                    "auth_token": self._auth_token,
                    "sek": base64.b64encode(self._sek).decode() if self._sek else None,
                    "token_expiry": self._token_expiry.isoformat(),
                    "user_gstin": data.get("UserGstin"),
                }
            else:
                return {
                    "success": False,
                    "error_code": result.get("ErrorDetails", [{}])[0].get("ErrorCode"),
                    "error_message": result.get("ErrorDetails", [{}])[0].get("ErrorMessage"),
                    "raw_response": result,
                }

        except Exception as e:
            logger.error(f"E-Invoice authentication error: {e}")
            return {
                "success": False,
                "error_message": str(e),
            }

    def encrypt_payload(self, payload: Dict[str, Any]) -> str:
        """Encrypt request payload with SEK.

        Args:
            payload: Request payload dictionary

        Returns:
            Base64 encoded encrypted payload
        """
        if not self._sek:
            raise ValueError("Not authenticated - SEK not available")

        # Convert to JSON
        json_data = json.dumps(payload)

        # Pad to 16-byte boundary
        padded = json_data + (16 - len(json_data) % 16) * chr(16 - len(json_data) % 16)

        # Encrypt with AES-256-ECB
        cipher = AES.new(self._sek, AES.MODE_ECB)
        encrypted = cipher.encrypt(padded.encode())

        return base64.b64encode(encrypted).decode()

    def decrypt_payload(self, encrypted_b64: str) -> Dict[str, Any]:
        """Decrypt response payload.

        Args:
            encrypted_b64: Base64 encoded encrypted response

        Returns:
            Decrypted payload dictionary
        """
        if not self._sek:
            raise ValueError("Not authenticated - SEK not available")

        encrypted = base64.b64decode(encrypted_b64)
        cipher = AES.new(self._sek, AES.MODE_ECB)
        decrypted = cipher.decrypt(encrypted)

        # Remove PKCS7 padding
        pad_len = decrypted[-1]
        json_data = decrypted[:-pad_len].decode()

        return json.loads(json_data)

    @property
    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        if not self._auth_token or not self._token_expiry:
            return False
        return datetime.utcnow() < self._token_expiry

    @property
    def auth_token(self) -> Optional[str]:
        """Get current auth token."""
        return self._auth_token

    @property
    def sek_b64(self) -> Optional[str]:
        """Get base64 encoded SEK."""
        return base64.b64encode(self._sek).decode() if self._sek else None
