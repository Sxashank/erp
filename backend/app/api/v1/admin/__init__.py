"""Admin API surface (cross-module).

Routers in this package are mounted under ``/api/v1/admin/...`` by
``app/api/v1/router.py``. They are tenant-aware via
:func:`app.api.deps.get_db_with_tenant` and require an authenticated
``mst_user`` with appropriate permissions.
"""

from fastapi import APIRouter

from app.api.v1.admin.portal_registrations import (
    router as portal_registrations_router,
)
from app.api.v1.admin.portal_users import router as portal_users_router

router = APIRouter(prefix="/admin", tags=["Admin"])
router.include_router(portal_registrations_router)
router.include_router(portal_users_router)
