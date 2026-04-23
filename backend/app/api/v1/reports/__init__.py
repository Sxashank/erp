"""Report API endpoints."""

from fastapi import APIRouter

from app.api.v1.reports.financial_reports import router as financial_router
from app.api.v1.reports.regulatory import router as regulatory_router
from app.api.v1.reports.mis import router as mis_router

router = APIRouter()

router.include_router(financial_router, prefix="/financial", tags=["Financial Reports"])
router.include_router(regulatory_router, prefix="/regulatory", tags=["Regulatory Reports"])
router.include_router(mis_router, prefix="/mis", tags=["MIS Reports"])

__all__ = ["router"]
