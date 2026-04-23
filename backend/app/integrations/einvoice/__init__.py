"""E-Invoice (IRP) Integration package.

Provides API client for interacting with E-Invoice IRP (Invoice Registration Portal) for:
- IRN (Invoice Reference Number) generation
- E-Invoice cancellation
- QR code generation
- E-Way Bill auto-generation with E-Invoice
"""

from app.integrations.einvoice.client import EInvoiceClient
from app.integrations.einvoice.auth import EInvoiceAuthManager

__all__ = [
    "EInvoiceClient",
    "EInvoiceAuthManager",
]
