"""Portal Module API endpoints.

Provides REST API for customer self-service portal including:
- OTP-based Authentication
- Loan Dashboard
- Payments
- Documents
- Service Requests
- Communication
"""

from fastapi import APIRouter

from app.api.v1.portal.auth import router as auth_router
from app.api.v1.portal.dashboard import router as dashboard_router
from app.api.v1.portal.payments import router as payments_router
from app.api.v1.portal.documents import router as documents_router
from app.api.v1.portal.service_requests import router as service_requests_router
from app.api.v1.portal.communication import router as communication_router

router = APIRouter(prefix="/portal", tags=["Customer Portal"])

router.include_router(auth_router)
router.include_router(dashboard_router)
router.include_router(payments_router)
router.include_router(documents_router)
router.include_router(service_requests_router)
router.include_router(communication_router)
