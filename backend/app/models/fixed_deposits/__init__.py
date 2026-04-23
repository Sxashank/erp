"""
Fixed Deposits Module Models
"""

from app.models.fixed_deposits.fd_product import FDProduct, FDInterestSlab
from app.models.fixed_deposits.fixed_deposit import (
    FixedDeposit,
    FDInterestAccrual,
    FDTransaction,
    FDNominee,
)

__all__ = [
    "FDProduct",
    "FDInterestSlab",
    "FixedDeposit",
    "FDInterestAccrual",
    "FDTransaction",
    "FDNominee",
]
