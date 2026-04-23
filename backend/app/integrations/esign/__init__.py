"""eSign Integration for digital document signing.

Supports:
- Aadhaar eSign (UIDAI/NSDL)
- Digital Signature Certificates (DSC)
- OTP-based eSign
"""

from app.integrations.esign.base import (
    ESignProvider,
    ESignRequest,
    ESignResponse,
    ESignStatus,
    ESignError,
)
from app.integrations.esign.aadhaar_esign import AadhaarESignProvider
from app.integrations.esign.service import ESignService

__all__ = [
    "ESignProvider",
    "ESignRequest",
    "ESignResponse",
    "ESignStatus",
    "ESignError",
    "AadhaarESignProvider",
    "ESignService",
]
