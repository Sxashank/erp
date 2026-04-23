"""GSTN Authentication Manager.

Handles OTP-based authentication flow with GSTN portal.
Uses ASP (Application Service Provider) credentials for API access.
"""

import base64
import hashlib
import json
import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple

import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)


class GSTNAuthManager:
    """Manages GSTN API authentication.

    GSTN uses a complex authentication flow:
    1. Request OTP with GSTIN and username
    2. Encrypt OTP using public key
    3. Exchange encrypted OTP for auth token
    4. Use auth token + SEK for subsequent API calls

    All API requests are encrypted using AES-256-ECB with the SEK.
    """

    # GSTN API endpoints
    SANDBOX_BASE_URL = "https://gspapi.sandbox.gst.gov.in"
    PRODUCTION_BASE_URL = "https://gspapi.gst.gov.in"

    def __init__(
        self,
        asp_id: str,
        asp_secret: str,
        asp_userid: str,
        public_key_pem: str,
        sandbox_mode: bool = True,
    ):
        """Initialize GSTN Auth Manager.

        Args:
            asp_id: ASP ID provided by GSTN
            asp_secret: ASP secret key
            asp_userid: ASP user ID
            public_key_pem: GSTN public key in PEM format for encryption
            sandbox_mode: Whether to use sandbox environment
        """
        self.asp_id = asp_id
        self.asp_secret = asp_secret
        self.asp_userid = asp_userid
        self.sandbox_mode = sandbox_mode
        self.base_url = self.SANDBOX_BASE_URL if sandbox_mode else self.PRODUCTION_BASE_URL

        # Load public key for encryption
        self._public_key = serialization.load_pem_public_key(
            public_key_pem.encode(),
            backend=default_backend()
        )

        # HTTP client
        self._client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        """Close HTTP client."""
        await self._client.aclose()

    def _generate_app_key(self) -> Tuple[str, bytes]:
        """Generate application key for session.

        Returns:
            Tuple of (encrypted_app_key, raw_app_key)
        """
        # Generate 32-byte random key
        raw_app_key = secrets.token_bytes(32)

        # Encrypt with GSTN public key
        encrypted = self._public_key.encrypt(
            raw_app_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        return base64.b64encode(encrypted).decode(), raw_app_key

    def _encrypt_data(self, data: str, key: bytes) -> str:
        """Encrypt data using AES-256-ECB.

        GSTN uses ECB mode (not recommended but required by their API).
        """
        # Pad data to 16-byte boundary
        pad_length = 16 - (len(data.encode()) % 16)
        padded_data = data.encode() + bytes([pad_length] * pad_length)

        # Encrypt
        cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted = encryptor.update(padded_data) + encryptor.finalize()

        return base64.b64encode(encrypted).decode()

    def _decrypt_data(self, encrypted_data: str, key: bytes) -> str:
        """Decrypt data using AES-256-ECB."""
        encrypted_bytes = base64.b64decode(encrypted_data)

        cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(encrypted_bytes) + decryptor.finalize()

        # Remove padding
        pad_length = decrypted[-1]
        return decrypted[:-pad_length].decode()

    def _decrypt_sek(self, encrypted_sek: str, app_key: bytes) -> bytes:
        """Decrypt Session Encryption Key using application key."""
        encrypted_bytes = base64.b64decode(encrypted_sek)

        cipher = Cipher(algorithms.AES(app_key), modes.ECB(), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(encrypted_bytes) + decryptor.finalize()

        # Remove padding and return raw bytes
        pad_length = decrypted[-1]
        return decrypted[:-pad_length]

    def _get_base_headers(self) -> Dict[str, str]:
        """Get base headers for GSTN API requests."""
        return {
            "Content-Type": "application/json",
            "asp-id": self.asp_id,
            "asp-secret": self.asp_secret,
            "Gstn-Txn-Id": f"TXN{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
        }

    async def request_otp(self, gstin: str, username: str) -> Dict[str, Any]:
        """Request OTP for GSTN authentication.

        Args:
            gstin: 15-digit GSTIN
            username: GSTN portal username

        Returns:
            Response containing status and OTP reference
        """
        encrypted_app_key, raw_app_key = self._generate_app_key()

        headers = self._get_base_headers()

        payload = {
            "action": "OTPREQUEST",
            "app_key": encrypted_app_key,
            "username": username,
            "gstin": gstin,
        }

        try:
            response = await self._client.post(
                f"{self.base_url}/taxpayerapi/v0.2/authenticate",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()

            result = response.json()
            logger.info(f"OTP request for GSTIN {gstin}: {result.get('status_cd')}")

            return {
                "success": result.get("status_cd") == "1",
                "message": result.get("status_desc", ""),
                "otp_reference": result.get("data", {}).get("otp_txn_id"),
                "raw_app_key": base64.b64encode(raw_app_key).decode(),
                "raw_response": result,
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"GSTN OTP request failed: {e}")
            return {
                "success": False,
                "message": str(e),
                "otp_reference": None,
            }
        except Exception as e:
            logger.error(f"GSTN OTP request error: {e}")
            return {
                "success": False,
                "message": str(e),
                "otp_reference": None,
            }

    async def verify_otp(
        self,
        gstin: str,
        username: str,
        otp: str,
        otp_reference: str,
        app_key_b64: str,
    ) -> Dict[str, Any]:
        """Verify OTP and get authentication token.

        Args:
            gstin: 15-digit GSTIN
            username: GSTN portal username
            otp: 6-digit OTP entered by user
            otp_reference: OTP reference from request_otp
            app_key_b64: Base64-encoded app key from request_otp

        Returns:
            Authentication token and SEK if successful
        """
        raw_app_key = base64.b64decode(app_key_b64)

        # Encrypt OTP with app key
        encrypted_otp = self._encrypt_data(otp, raw_app_key)

        headers = self._get_base_headers()

        payload = {
            "action": "AUTHTOKEN",
            "app_key": self._generate_app_key()[0],  # Generate new app key for this request
            "username": username,
            "gstin": gstin,
            "otp": encrypted_otp,
        }

        try:
            response = await self._client.post(
                f"{self.base_url}/taxpayerapi/v0.2/authenticate",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()

            result = response.json()

            if result.get("status_cd") == "1":
                data = result.get("data", {})
                auth_token = data.get("auth_token")
                encrypted_sek = data.get("sek")
                expiry = data.get("expiry")

                # Decrypt SEK
                sek = self._decrypt_sek(encrypted_sek, raw_app_key)

                # Calculate token expiry (usually 6 hours from GSTN)
                token_expires_at = datetime.utcnow() + timedelta(hours=6)
                if expiry:
                    try:
                        token_expires_at = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
                    except ValueError:
                        pass

                logger.info(f"GSTN auth successful for GSTIN {gstin}")

                return {
                    "success": True,
                    "auth_token": auth_token,
                    "sek": base64.b64encode(sek).decode(),
                    "token_expires_at": token_expires_at,
                    "raw_response": result,
                }
            else:
                logger.warning(f"GSTN auth failed for GSTIN {gstin}: {result.get('status_desc')}")
                return {
                    "success": False,
                    "message": result.get("status_desc", "Authentication failed"),
                    "error_cd": result.get("error", {}).get("error_cd"),
                }

        except httpx.HTTPStatusError as e:
            logger.error(f"GSTN auth verification failed: {e}")
            return {
                "success": False,
                "message": str(e),
            }
        except Exception as e:
            logger.error(f"GSTN auth verification error: {e}")
            return {
                "success": False,
                "message": str(e),
            }

    async def refresh_token(
        self,
        gstin: str,
        username: str,
        auth_token: str,
        sek_b64: str,
    ) -> Dict[str, Any]:
        """Refresh authentication token.

        Args:
            gstin: 15-digit GSTIN
            username: GSTN portal username
            auth_token: Current auth token
            sek_b64: Base64-encoded SEK

        Returns:
            New authentication token and SEK
        """
        encrypted_app_key, raw_app_key = self._generate_app_key()
        sek = base64.b64decode(sek_b64)

        headers = self._get_base_headers()
        headers["auth-token"] = auth_token

        payload = {
            "action": "REFRESHTOKEN",
            "app_key": encrypted_app_key,
            "username": username,
            "gstin": gstin,
        }

        # Encrypt payload with SEK
        encrypted_payload = self._encrypt_data(json.dumps(payload), sek)

        try:
            response = await self._client.post(
                f"{self.base_url}/taxpayerapi/v0.2/authenticate",
                headers=headers,
                json={"data": encrypted_payload},
            )
            response.raise_for_status()

            result = response.json()

            if result.get("status_cd") == "1":
                # Decrypt response
                encrypted_data = result.get("data")
                decrypted_data = json.loads(self._decrypt_data(encrypted_data, sek))

                new_auth_token = decrypted_data.get("auth_token")
                new_encrypted_sek = decrypted_data.get("sek")
                new_sek = self._decrypt_sek(new_encrypted_sek, raw_app_key)

                return {
                    "success": True,
                    "auth_token": new_auth_token,
                    "sek": base64.b64encode(new_sek).decode(),
                    "token_expires_at": datetime.utcnow() + timedelta(hours=6),
                }
            else:
                return {
                    "success": False,
                    "message": result.get("status_desc", "Token refresh failed"),
                }

        except Exception as e:
            logger.error(f"GSTN token refresh error: {e}")
            return {
                "success": False,
                "message": str(e),
            }

    def encrypt_request_payload(self, payload: Dict[str, Any], sek_b64: str) -> str:
        """Encrypt API request payload.

        Args:
            payload: Request payload as dictionary
            sek_b64: Base64-encoded SEK

        Returns:
            Base64-encoded encrypted payload
        """
        sek = base64.b64decode(sek_b64)
        payload_str = json.dumps(payload)
        return self._encrypt_data(payload_str, sek)

    def decrypt_response_payload(self, encrypted_data: str, sek_b64: str) -> Dict[str, Any]:
        """Decrypt API response payload.

        Args:
            encrypted_data: Base64-encoded encrypted response
            sek_b64: Base64-encoded SEK

        Returns:
            Decrypted response as dictionary
        """
        sek = base64.b64decode(sek_b64)
        decrypted_str = self._decrypt_data(encrypted_data, sek)
        return json.loads(decrypted_str)
