"""SFC borrower-portal API endpoints."""

from fastapi import APIRouter

from app.api.v1.portal.applications import router as applications_router
from app.api.v1.portal.auth import router as auth_router
from app.api.v1.portal.claims import router as claims_router
from app.api.v1.portal.communication import router as communication_router
from app.api.v1.portal.dashboard import router as dashboard_router
from app.api.v1.portal.documents import router as documents_router
from app.api.v1.portal.lifecycle_certificates import (
    router as lifecycle_certificates_router,
)
from app.api.v1.portal.payments import router as payments_router
from app.api.v1.portal.products import router as products_router
from app.api.v1.portal.registration import router as registration_router
from app.api.v1.portal.reports import router as reports_router
from app.api.v1.portal.service_requests import router as service_requests_router
from app.api.v1.portal.utilization_categories import (
    router as utilization_categories_router,
)
from app.api.v1.portal.workbench import router as workbench_router

router = APIRouter(prefix="/portal", tags=["Borrower Portal"])

router.include_router(auth_router)
router.include_router(registration_router)
router.include_router(workbench_router)
router.include_router(reports_router)
router.include_router(products_router)
router.include_router(utilization_categories_router)
router.include_router(dashboard_router)
router.include_router(payments_router)
router.include_router(documents_router)
router.include_router(service_requests_router)
router.include_router(communication_router)
router.include_router(communication_router, prefix="/communication")
router.include_router(applications_router)
router.include_router(claims_router)
# Phase A-E — borrower lifecycle + certificate endpoints
router.include_router(lifecycle_certificates_router)
