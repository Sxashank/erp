"""
Compliance API Router

Aggregates all compliance-related routes.
"""

from fastapi import APIRouter

from app.api.v1.compliance.compliance import router as compliance_router

router = APIRouter()

# Mount compliance routes
router.include_router(compliance_router, tags=["Compliance"])
