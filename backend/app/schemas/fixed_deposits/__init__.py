"""
Fixed Deposits Module Schemas
"""

from app.schemas.fixed_deposits.fd_product import (
    FDProductCreate,
    FDProductUpdate,
    FDProductResponse,
    FDProductListResponse,
    FDInterestSlabCreate,
    FDInterestSlabUpdate,
    FDInterestSlabResponse,
)
from app.schemas.fixed_deposits.fixed_deposit import (
    FixedDepositCreate,
    FixedDepositUpdate,
    FixedDepositResponse,
    FixedDepositListResponse,
    FixedDepositSummary,
    FDInterestAccrualResponse,
    FDTransactionResponse,
    FDNomineeCreate,
    FDNomineeUpdate,
    FDNomineeResponse,
    FDMaturityProjection,
    FDClosureRequest,
    FDRenewalRequest,
)

__all__ = [
    # Product schemas
    "FDProductCreate",
    "FDProductUpdate",
    "FDProductResponse",
    "FDProductListResponse",
    "FDInterestSlabCreate",
    "FDInterestSlabUpdate",
    "FDInterestSlabResponse",
    # FD schemas
    "FixedDepositCreate",
    "FixedDepositUpdate",
    "FixedDepositResponse",
    "FixedDepositListResponse",
    "FixedDepositSummary",
    "FDInterestAccrualResponse",
    "FDTransactionResponse",
    "FDNomineeCreate",
    "FDNomineeUpdate",
    "FDNomineeResponse",
    "FDMaturityProjection",
    "FDClosureRequest",
    "FDRenewalRequest",
]
