"""Vendor Portal Main Router."""

from fastapi import APIRouter

from app.api.v1.vendor_portal import (
    auth,
    registration,
    profile,
    purchase_orders,
    invoices,
    asn,
    payments,
    compliance,
    dashboard,
)

router = APIRouter(prefix="/vendor-portal", tags=["Vendor Portal"])

# Include all sub-routers
router.include_router(auth.router, prefix="/auth", tags=["Vendor Auth"])
router.include_router(registration.router, prefix="/registration", tags=["Vendor Registration"])
router.include_router(profile.router, prefix="/profile", tags=["Vendor Profile"])
router.include_router(purchase_orders.router, prefix="/purchase-orders", tags=["Vendor POs"])
router.include_router(invoices.router, prefix="/invoices", tags=["Vendor Invoices"])
router.include_router(asn.router, prefix="/asn", tags=["Vendor ASN"])
router.include_router(payments.router, prefix="/payments", tags=["Vendor Payments"])
router.include_router(compliance.router, prefix="/compliance", tags=["Vendor Compliance"])
router.include_router(dashboard.router, prefix="/dashboard", tags=["Vendor Dashboard"])
