"""OneMoney Account Aggregator client implementation."""

import base64
import hashlib
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives import serialization

from app.integrations.aa.base import AAClientBase
from app.integrations.aa.schemas import (
    AAConsentRequest,
    AAConsentResponse,
    AAFetchRequest,
    AAFetchResponse,
    AAFIData,
)

logger = logging.getLogger(__name__)


class OneMoneyAAClient(AAClientBase):
    """OneMoney Account Aggregator client.

    Implements FIU APIs for OneMoney AA platform.
    Documentation: https://docs.onemoney.in/
    """

    def __init__(self, config: Dict[str, Any], sandbox_mode: bool = True):
        super().__init__(config, sandbox_mode)

        # OneMoney-specific URLs
        if sandbox_mode:
            self.base_url = config.get("sandbox_url", "https://sandbox.onemoney.in/v2")
            self.token_url = config.get("sandbox_token_url", "https://sandbox.onemoney.in/v2/auth/token")
        else:
            self.base_url = config.get("api_base_url", "https://api.onemoney.in/v2")
            self.token_url = config.get("token_url", "https://api.onemoney.in/v2/auth/token")

        # Key pair for encryption
        self._private_key: Optional[X25519PrivateKey] = None
        self._public_key_b64: Optional[str] = None

    async def get_access_token(self) -> str:
        """Get or refresh OAuth access token from OneMoney."""
        if self._access_token and self._token_expires_at:
            if datetime.utcnow() < self._token_expires_at:
                return self._access_token

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.token_url,
                    json={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "grant_type": "client_credentials",
                    },
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code == 200:
                    data = response.json()
                    self._access_token = data.get("access_token")
                    expires_in = data.get("expires_in", 3600)
                    self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 60)
                    return self._access_token
                else:
                    logger.error(f"Failed to get OneMoney access token: {response.text}")
                    raise Exception(f"Token request failed: {response.status_code}")

        except Exception as e:
            logger.error(f"OneMoney token error: {e}")
            raise

    def _get_headers(self) -> Dict[str, str]:
        """Get standard API headers."""
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
            "x-request-id": str(uuid.uuid4()),
            "x-fiu-id": self.entity_id,
        }

    def _generate_key_pair(self) -> tuple[str, str]:
        """Generate X25519 key pair for encryption."""
        self._private_key = X25519PrivateKey.generate()
        public_key = self._private_key.public_key()
        public_key_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        self._public_key_b64 = base64.b64encode(public_key_bytes).decode()

        # Generate nonce
        nonce = base64.b64encode(uuid.uuid4().bytes).decode()

        return self._public_key_b64, nonce

    async def create_consent(
        self,
        request: AAConsentRequest,
    ) -> AAConsentResponse:
        """Create a consent request with OneMoney."""
        try:
            await self.get_access_token()

            # Build consent request
            consent_start = datetime.utcnow()
            consent_expiry = consent_start + timedelta(days=request.consent_validity_months * 30)

            payload = {
                "ver": "2.0.0",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "txnid": str(uuid.uuid4()),
                "ConsentDetail": {
                    "consentStart": consent_start.isoformat() + "Z",
                    "consentExpiry": consent_expiry.isoformat() + "Z",
                    "consentMode": request.consent_mode,
                    "fetchType": request.fetch_type,
                    "consentTypes": ["PROFILE", "SUMMARY", "TRANSACTIONS"],
                    "fiTypes": request.fi_types,
                    "DataConsumer": {
                        "id": self.entity_id,
                        "type": "FIU",
                    },
                    "Customer": {
                        "id": request.customer_vua,
                    },
                    "Purpose": {
                        "code": self._get_purpose_code(request.purpose),
                        "refUri": "https://api.rebit.org.in/aa/purpose/102.xml",
                        "text": request.purpose_description or "Loan underwriting and assessment",
                        "Category": {
                            "type": "string",
                        },
                    },
                    "FIDataRange": {
                        "from": request.data_range_from.isoformat() + "T00:00:00.000Z",
                        "to": request.data_range_to.isoformat() + "T23:59:59.999Z",
                    },
                    "DataLife": {
                        "unit": "MONTH",
                        "value": request.data_life_months,
                    },
                    "Frequency": {
                        "unit": "MONTH" if request.fetch_type == "PERIODIC" else "INF",
                        "value": 1 if request.fetch_type == "PERIODIC" else 0,
                    },
                },
            }

            if request.redirect_url:
                payload["redirectUrl"] = request.redirect_url

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/Consent",
                    json=payload,
                    headers=self._get_headers(),
                )

                data = response.json()

                if response.status_code in (200, 201) and data.get("ConsentHandle"):
                    return AAConsentResponse(
                        success=True,
                        consent_handle=data.get("ConsentHandle"),
                        consent_status="PENDING",
                        redirect_url=data.get("redirectUrl"),
                        raw_response=data,
                    )
                else:
                    error_info = data.get("errorInfo", data)
                    return AAConsentResponse(
                        success=False,
                        error_code=error_info.get("errorCode"),
                        error_message=error_info.get("errorMessage") or error_info.get("message"),
                        raw_response=data,
                    )

        except Exception as e:
            logger.error(f"OneMoney create consent error: {e}")
            return AAConsentResponse(
                success=False,
                error_message=str(e),
            )

    async def get_consent_status(
        self,
        consent_handle: str,
    ) -> AAConsentResponse:
        """Get status of a consent request."""
        try:
            await self.get_access_token()

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/Consent/handle/{consent_handle}",
                    headers=self._get_headers(),
                )

                data = response.json()

                if response.status_code == 200:
                    consent_status = data.get("ConsentStatus", data)
                    return AAConsentResponse(
                        success=True,
                        consent_handle=consent_handle,
                        consent_id=consent_status.get("id") or consent_status.get("consentId"),
                        consent_status=consent_status.get("status", "PENDING"),
                        raw_response=data,
                    )
                else:
                    error_info = data.get("errorInfo", data)
                    return AAConsentResponse(
                        success=False,
                        consent_handle=consent_handle,
                        error_code=error_info.get("errorCode"),
                        error_message=error_info.get("errorMessage"),
                        raw_response=data,
                    )

        except Exception as e:
            logger.error(f"OneMoney consent status error: {e}")
            return AAConsentResponse(
                success=False,
                consent_handle=consent_handle,
                error_message=str(e),
            )

    async def fetch_consent_artifact(
        self,
        consent_id: str,
    ) -> Dict[str, Any]:
        """Fetch signed consent artifact."""
        try:
            await self.get_access_token()

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{self.base_url}/Consent/{consent_id}",
                    headers=self._get_headers(),
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Failed to fetch consent artifact: {response.text}")
                    return {}

        except Exception as e:
            logger.error(f"OneMoney fetch consent artifact error: {e}")
            return {}

    async def initiate_fi_request(
        self,
        request: AAFetchRequest,
    ) -> AAFetchResponse:
        """Initiate FI data fetch request."""
        try:
            await self.get_access_token()

            # Generate key pair
            public_key, nonce = self._generate_key_pair()

            payload = {
                "ver": "2.0.0",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "txnid": str(uuid.uuid4()),
                "Consent": {
                    "id": request.consent_id,
                },
                "KeyMaterial": {
                    "cryptoAlg": "ECDH",
                    "curve": "Curve25519",
                    "params": "AESGCM",
                    "DHPublicKey": {
                        "expiry": (datetime.utcnow() + timedelta(hours=24)).isoformat() + "Z",
                        "Parameters": "",
                        "KeyValue": public_key,
                    },
                    "Nonce": nonce,
                },
            }

            if request.data_range_from or request.data_range_to:
                payload["FIDataRange"] = {}
                if request.data_range_from:
                    payload["FIDataRange"]["from"] = request.data_range_from.isoformat() + "T00:00:00.000Z"
                if request.data_range_to:
                    payload["FIDataRange"]["to"] = request.data_range_to.isoformat() + "T23:59:59.999Z"

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/FI/request",
                    json=payload,
                    headers=self._get_headers(),
                )

                data = response.json()

                if response.status_code in (200, 201):
                    return AAFetchResponse(
                        success=True,
                        session_id=data.get("sessionId"),
                        data_session_id=data.get("dataSessionId"),
                        status="INITIATED",
                        raw_response=data,
                    )
                else:
                    error_info = data.get("errorInfo", data)
                    return AAFetchResponse(
                        success=False,
                        error_code=error_info.get("errorCode"),
                        error_message=error_info.get("errorMessage"),
                        raw_response=data,
                    )

        except Exception as e:
            logger.error(f"OneMoney FI request error: {e}")
            return AAFetchResponse(
                success=False,
                error_message=str(e),
            )

    async def fetch_fi_data(
        self,
        session_id: str,
        consent_id: str,
    ) -> AAFetchResponse:
        """Fetch actual FI data for a session."""
        try:
            await self.get_access_token()

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(
                    f"{self.base_url}/FI/fetch/{session_id}",
                    headers=self._get_headers(),
                )

                data = response.json()

                if response.status_code == 200:
                    fi_data_list = []

                    for fi_item in data.get("FI", []):
                        fi_data = AAFIData(
                            fi_type=fi_item.get("fiType"),
                            fip_id=fi_item.get("fipId"),
                            link_ref_number=fi_item.get("linkRefNumber"),
                            masked_account_number=fi_item.get("maskedAccNumber"),
                            account_type=fi_item.get("accountType"),
                            raw_data=fi_item.get("data"),
                        )

                        # Decrypt if encrypted
                        if fi_item.get("data") and fi_item.get("KeyMaterial"):
                            try:
                                decrypted = await self.decrypt_fi_data(
                                    fi_item.get("data"),
                                    fi_item.get("KeyMaterial"),
                                )
                                fi_data.raw_data = decrypted

                                if decrypted:
                                    fi_data.profile = decrypted.get("Profile")
                                    fi_data.summary = decrypted.get("Summary")
                                    fi_data.transactions = decrypted.get("Transactions", [])
                            except Exception as decrypt_error:
                                logger.error(f"Decryption error: {decrypt_error}")

                        fi_data_list.append(fi_data)

                    return AAFetchResponse(
                        success=True,
                        session_id=session_id,
                        status="COMPLETED",
                        fi_data=fi_data_list,
                        raw_response=data,
                    )
                else:
                    error_info = data.get("errorInfo", data)
                    return AAFetchResponse(
                        success=False,
                        session_id=session_id,
                        error_code=error_info.get("errorCode"),
                        error_message=error_info.get("errorMessage"),
                        raw_response=data,
                    )

        except Exception as e:
            logger.error(f"OneMoney fetch FI data error: {e}")
            return AAFetchResponse(
                success=False,
                session_id=session_id,
                error_message=str(e),
            )

    async def decrypt_fi_data(
        self,
        encrypted_data: Dict[str, Any],
        key_material: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Decrypt FI data using ECDH + AES-GCM."""
        try:
            if not self._private_key:
                raise ValueError("No private key available for decryption")

            # Get FIP's public key
            fip_public_key_b64 = key_material.get("DHPublicKey", {}).get("KeyValue", "")
            fip_public_key_bytes = base64.b64decode(fip_public_key_b64)
            fip_public_key = X25519PublicKey.from_public_bytes(fip_public_key_bytes)

            # Compute shared secret
            shared_key = self._private_key.exchange(fip_public_key)

            # Get nonces
            our_nonce = base64.b64decode(key_material.get("Nonce", ""))
            fip_nonce = base64.b64decode(key_material.get("DHPublicKey", {}).get("Nonce", ""))

            # Derive key
            key_material_bytes = shared_key + our_nonce + fip_nonce
            derived_key = hashlib.sha256(key_material_bytes).digest()

            # Decrypt data
            encrypted_fi_b64 = encrypted_data.get("encryptedFI", "")
            encrypted_nonce_b64 = encrypted_data.get("encryptedNonce", encrypted_data.get("nonce", ""))

            encrypted_bytes = base64.b64decode(encrypted_fi_b64)
            nonce_bytes = base64.b64decode(encrypted_nonce_b64)

            aesgcm = AESGCM(derived_key)
            decrypted_bytes = aesgcm.decrypt(nonce_bytes, encrypted_bytes, None)

            return json.loads(decrypted_bytes.decode())

        except Exception as e:
            logger.error(f"FI data decryption error: {e}")
            raise

    async def revoke_consent(
        self,
        consent_id: str,
        reason: Optional[str] = None,
    ) -> AAConsentResponse:
        """Revoke an active consent."""
        try:
            await self.get_access_token()

            payload = {
                "ver": "2.0.0",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "txnid": str(uuid.uuid4()),
                "ConsentId": consent_id,
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/Consent/revoke",
                    json=payload,
                    headers=self._get_headers(),
                )

                data = response.json() if response.text else {}

                if response.status_code in (200, 201):
                    return AAConsentResponse(
                        success=True,
                        consent_id=consent_id,
                        consent_status="REVOKED",
                        raw_response=data,
                    )
                else:
                    error_info = data.get("errorInfo", data)
                    return AAConsentResponse(
                        success=False,
                        consent_id=consent_id,
                        error_code=error_info.get("errorCode"),
                        error_message=error_info.get("errorMessage"),
                        raw_response=data,
                    )

        except Exception as e:
            logger.error(f"OneMoney consent revocation error: {e}")
            return AAConsentResponse(
                success=False,
                consent_id=consent_id,
                error_message=str(e),
            )
