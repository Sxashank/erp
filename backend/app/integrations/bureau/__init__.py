"""Credit Bureau Integration Package.

Provides clients for pulling credit reports from various bureaus:
- CIBIL (TransUnion)
- Experian
- Equifax
- CRIF High Mark
"""

from app.integrations.bureau.base import BaseBureauClient, BureauConfig
from app.integrations.bureau.cibil import CIBILClient
from app.integrations.bureau.experian import ExperianClient
from app.integrations.bureau.parser import BureauReportParser

__all__ = [
    "BaseBureauClient",
    "BureauConfig",
    "CIBILClient",
    "ExperianClient",
    "BureauReportParser",
]
