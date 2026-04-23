"""
Fixed Deposits API Routes
"""

from fastapi import APIRouter

from app.api.v1.fixed_deposits.products import router as products_router
from app.api.v1.fixed_deposits.deposits import router as deposits_router

router = APIRouter()

router.include_router(products_router, prefix="/products", tags=["FD Products"])
router.include_router(deposits_router, prefix="/deposits", tags=["Fixed Deposits"])
