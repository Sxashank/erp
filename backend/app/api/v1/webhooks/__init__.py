"""Webhooks API package."""

from fastapi import APIRouter

from app.api.v1.webhooks.nach import router as nach_router
from app.api.v1.webhooks.aa import router as aa_router
from app.api.v1.webhooks.payment import router as payment_router

router = APIRouter()

router.include_router(nach_router, prefix="/nach", tags=["Webhooks - NACH"])
router.include_router(aa_router, prefix="/aa", tags=["Webhooks - Account Aggregator"])
router.include_router(payment_router, prefix="/payment", tags=["Webhooks - Payment Gateway"])
