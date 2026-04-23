"""Fixed Assets API endpoints."""

from fastapi import APIRouter

from app.api.v1.fixed_assets.categories import router as categories_router
from app.api.v1.fixed_assets.assets import router as assets_router
from app.api.v1.fixed_assets.depreciation import router as depreciation_router
from app.api.v1.fixed_assets.it_depreciation import router as it_depreciation_router
from app.api.v1.fixed_assets.physical_verification import router as pv_router
from app.api.v1.fixed_assets.reports import router as reports_router
from app.api.v1.fixed_assets.lease import router as lease_router
from app.api.v1.fixed_assets.maintenance import router as maintenance_router
from app.api.v1.fixed_assets.insurance import router as insurance_router
from app.api.v1.fixed_assets.analytics import router as analytics_router
from app.api.v1.fixed_assets.config import router as config_router
from app.api.v1.fixed_assets.bulk_operations import router as bulk_router

router = APIRouter()

router.include_router(categories_router, prefix="/categories", tags=["Asset Categories"])
router.include_router(assets_router, prefix="/assets", tags=["Fixed Assets"])
router.include_router(depreciation_router, prefix="/depreciation", tags=["Depreciation"])
router.include_router(it_depreciation_router, prefix="/it-depreciation", tags=["IT Act Depreciation"])
router.include_router(pv_router, prefix="/verification", tags=["Physical Verification"])
router.include_router(reports_router, prefix="/reports", tags=["FA Reports"])
router.include_router(lease_router, prefix="/leases", tags=["Lease Accounting"])
router.include_router(maintenance_router, prefix="/maintenance", tags=["Maintenance & AMC"])
router.include_router(insurance_router, prefix="/insurance", tags=["Insurance"])
router.include_router(analytics_router, prefix="/analytics", tags=["FA Analytics"])
router.include_router(config_router, tags=["FA Configuration"])
router.include_router(bulk_router, tags=["FA Bulk Operations"])
