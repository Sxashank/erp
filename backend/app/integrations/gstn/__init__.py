"""GSTN Portal Integration package.

Provides API client for interacting with GSTN (GST Network) portal for:
- OTP-based authentication
- GSTR-1 submission
- GSTR-3B submission
- GSTR-2A/2B data fetch
- Return filing status
"""

from app.integrations.gstn.client import GSTNClient
from app.integrations.gstn.auth import GSTNAuthManager

__all__ = [
    "GSTNClient",
    "GSTNAuthManager",
]
