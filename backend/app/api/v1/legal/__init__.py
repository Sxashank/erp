"""Legal Module API endpoints.

Provides REST API for legal case management including:
- Master Data (Statutory Periods, Courts, Notice Templates)
- Advocate & Law Firm Management
- Notice Generation & Tracking
- SARFAESI Workflow
- Legal Expenses
- Legal Analytics
"""

from fastapi import APIRouter

from app.api.v1.legal.masters import router as masters_router
from app.api.v1.legal.advocates import router as advocates_router
from app.api.v1.legal.notices import router as notices_router
from app.api.v1.legal.sarfaesi import router as sarfaesi_router
from app.api.v1.legal.expenses import router as expenses_router
from app.api.v1.legal.analytics import router as analytics_router

router = APIRouter(prefix="/legal", tags=["Legal"])

router.include_router(masters_router)
router.include_router(advocates_router)
router.include_router(notices_router)
router.include_router(sarfaesi_router)
router.include_router(expenses_router)
router.include_router(analytics_router)
