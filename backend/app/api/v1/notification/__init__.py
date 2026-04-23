"""Notification API module."""

from fastapi import APIRouter

from app.api.v1.notification.notifications import router as notifications_router
from app.api.v1.notification.templates import router as templates_router

router = APIRouter(prefix="/notifications", tags=["Notifications"])

router.include_router(notifications_router, prefix="")
router.include_router(templates_router, prefix="/templates")
