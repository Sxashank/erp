"""E-Way Bill Integration package.

Provides API client for E-Way Bill generation via NIC portal:
- E-Way Bill generation
- E-Way Bill cancellation
- Vehicle update (Part B)
- E-Way Bill extension
- Consolidated E-Way Bill
"""

from app.integrations.ewaybill.client import EWayBillClient
from app.integrations.ewaybill.auth import EWayBillAuthManager

__all__ = [
    "EWayBillClient",
    "EWayBillAuthManager",
]
