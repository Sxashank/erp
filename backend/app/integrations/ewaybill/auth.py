"""E-Way Bill Authentication Manager.

Handles authentication with E-Way Bill Portal:
- Token generation
- Session management
"""

import base64
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


class EWayBillAuthManager:
    """Authentication manager for E-Way Bill APIs.

    Supports NIC E-Way Bill portal authentication.
    """

    # NIC E-Way Bill URLs
    NIC_PROD_URL = "https://api.gst.gov.in"
    NIC_SANDBOX_URL = "https://ewb-gst.nic.in/ewbapi/v1.03"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        username: str,
        password: str,
        gstin: str,
        public_key_pem: Optional[str] = None,
        sandbox_mode: bool = True,
    ):
        """Initialize E-Way Bill Auth Manager.

        Args:
            client_id: API client ID
            client_secret: API client secret
            username: E-Way Bill portal username
            password: E-Way Bill portal password
            gstin: GSTIN for authentication
            public_key_pem: Public key for encryption
            sandbox_mode: Whether to use sandbox environment
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self.gstin = gstin
        self.public_key_pem = public_key_pem
        self.sandbox_mode = sandbox_mode
        self.base_url = self.NIC_SANDBOX_URL if sandbox_mode else self.NIC_PROD_URL

        self._client = httpx.AsyncClient(timeout=60.0)
        self._auth_token: Optional[str] = None
        self._sek: Optional[bytes] = None
        self._token_expiry: Optional[datetime] = None

    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()

    def _generate_app_key(self) -> Tuple[bytes, str]:
        """Generate application key for session."""
        app_key = get_random_bytes(32)

        if self.public_key_pem:
            rsa_key = RSA.import_key(self.public_key_pem)
            cipher = PKCS1_v1_5.new(rsa_key)
            encrypted_app_key = cipher.encrypt(app_key)
            encrypted_app_key_b64 = base64.b64encode(encrypted_app_key).decode()
        else:
            encrypted_app_key_b64 = base64.b64encode(app_key).decode()

        return app_key, encrypted_app_key_b64

    def _encrypt_password(self, password: str, app_key: bytes) -> str:
        """Encrypt password with app key."""
        padded = password + (16 - len(password) % 16) * chr(16 - len(password) % 16)
        cipher = AES.new(app_key, AES.MODE_ECB)
        encrypted = cipher.encrypt(padded.encode())
        return base64.b64encode(encrypted).decode()

    def _decrypt_sek(self, encrypted_sek_b64: str, app_key: bytes) -> bytes:
        """Decrypt Session Encryption Key."""
        encrypted_sek = base64.b64decode(encrypted_sek_b64)
        cipher = AES.new(app_key, AES.MODE_ECB)
        decrypted = cipher.decrypt(encrypted_sek)
        pad_len = decrypted[-1]
        return decrypted[:-pad_len]

    async def authenticate(self) -> Dict[str, Any]:
        """Authenticate with E-Way Bill portal."""
        app_key, encrypted_app_key = self._generate_app_key()
        encrypted_password = self._encrypt_password(self.password, app_key)

        headers = {
            "Content-Type": "application/json",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "gstin": self.gstin,
        }

        payload = {
            "action": "ACCESSTOKEN",
            "username": self.username,
            "password": encrypted_password,
            "app_key": encrypted_app_key,
        }

        try:
            response = await self._client.post(
                f"{self.base_url}/authenticate",
                headers=headers,
                json=payload,
            )

            result = response.json()

            if result.get("status") == 1 or result.get("success"):
                data = result.get("data", result)

                encrypted_sek = data.get("sek")
                if encrypted_sek:
                    self._sek = self._decrypt_sek(encrypted_sek, app_key)

                self._auth_token = data.get("authtoken") or data.get("auth_token")
                self._token_expiry = datetime.utcnow() + timedelta(hours=6)

                return {
                    "success": True,
                    "auth_token": self._auth_token,
                    "sek": base64.b64encode(self._sek).decode() if self._sek else None,
                    "token_expiry": self._token_expiry.isoformat(),
                }
            else:
                return {
                    "success": False,
                    "error_code": result.get("error", {}).get("errorCodes"),
                    "error_message": result.get("error", {}).get("message") or result.get("message"),
                    "raw_response": result,
                }

        except Exception as e:
            logger.error(f"E-Way Bill authentication error: {e}")
            return {
                "success": False,
                "error_message": str(e),
            }

    def encrypt_payload(self, payload: Dict[str, Any]) -> str:
        """Encrypt request payload with SEK."""
        if not self._sek:
            raise ValueError("Not authenticated - SEK not available")

        json_data = json.dumps(payload)
        padded = json_data + (16 - len(json_data) % 16) * chr(16 - len(json_data) % 16)
        cipher = AES.new(self._sek, AES.MODE_ECB)
        encrypted = cipher.encrypt(padded.encode())
        return base64.b64encode(encrypted).decode()

    def decrypt_payload(self, encrypted_b64: str) -> Dict[str, Any]:
        """Decrypt response payload."""
        if not self._sek:
            raise ValueError("Not authenticated - SEK not available")

        encrypted = base64.b64decode(encrypted_b64)
        cipher = AES.new(self._sek, AES.MODE_ECB)
        decrypted = cipher.decrypt(encrypted)
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
