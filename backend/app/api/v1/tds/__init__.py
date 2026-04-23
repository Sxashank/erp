"""TDS API routers."""

from app.api.v1.tds.tds_sections import router as tds_sections_router
from app.api.v1.tds.tds_entries import router as tds_entries_router
from app.api.v1.tds.tds_challans import router as tds_challans_router
from app.api.v1.tds.tds_returns import router as tds_returns_router
from app.api.v1.tds.form16a import router as form16a_router

__all__ = [
    "tds_sections_router",
    "tds_entries_router",
    "tds_challans_router",
    "tds_returns_router",
    "form16a_router",
]
