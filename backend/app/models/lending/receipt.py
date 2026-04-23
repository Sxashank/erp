"""
Receipt models re-export.
This module provides compatibility aliases for receipt-related models.
"""

from app.models.lending.loan_account import LoanReceipt

__all__ = ["LoanReceipt"]
