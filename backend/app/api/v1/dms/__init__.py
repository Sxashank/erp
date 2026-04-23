"""DMS API module."""

from fastapi import APIRouter

from app.api.v1.dms.documents import router as documents_router
from app.api.v1.dms.folders import router as folders_router
from app.api.v1.dms.tags import router as tags_router

router = APIRouter(prefix="/dms")

router.include_router(documents_router)
router.include_router(folders_router)
router.include_router(tags_router)
