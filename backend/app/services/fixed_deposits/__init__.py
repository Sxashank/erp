"""
Fixed Deposits Module Services
"""

from app.services.fixed_deposits.fd_product_service import FDProductService
from app.services.fixed_deposits.fd_service import (
    FixedDepositService,
    FDInterestService,
)

__all__ = [
    "FDProductService",
    "FixedDepositService",
    "FDInterestService",
]
