"""IIF (Interest Incentivization Fund) API package.

Sub-routers per aggregate. Mounted on /api/v1/lending/iif by the parent
lending router.
"""

from fastapi import APIRouter

from app.api.v1.lending.iif.application_utilization import (
    router as application_utilization_router,
)
from app.api.v1.lending.iif.claims import router as claims_router
from app.api.v1.lending.iif.enrollments import router as enrollments_router
from app.api.v1.lending.iif.subvention_schemes import router as schemes_router
from app.api.v1.lending.iif.utilization_categories import (
    router as categories_router,
)

router = APIRouter()

router.include_router(schemes_router, prefix="/schemes", tags=["IIF - Schemes"])
router.include_router(
    categories_router, prefix="/categories", tags=["IIF - Utilization Categories"]
)
router.include_router(
    application_utilization_router,
    prefix="/applications",
    tags=["IIF - Application Utilization"],
)
router.include_router(enrollments_router, prefix="/enrollments", tags=["IIF - Enrollments"])
router.include_router(claims_router, prefix="/claims", tags=["IIF - Claims"])


__all__ = ["router"]
