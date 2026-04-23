"""GST API routers."""

from app.api.v1.gst.gst_rates import router as gst_rates_router
from app.api.v1.gst.hsn_sac import router as hsn_sac_router
from app.api.v1.gst.gst_registrations import router as gst_registrations_router
from app.api.v1.gst.gstn import router as gstn_router

__all__ = [
    "gst_rates_router",
    "hsn_sac_router",
    "gst_registrations_router",
    "gstn_router",
]
