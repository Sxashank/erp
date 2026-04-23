"""BI/Analytics API routes package."""

from fastapi import APIRouter

from app.api.v1.bi.dashboards import router as dashboards_router
from app.api.v1.bi.widgets import router as widgets_router
from app.api.v1.bi.chart_definitions import router as chart_definitions_router
from app.api.v1.bi.data_sources import router as data_sources_router

router = APIRouter()

# Dashboard routes (including nested widgets and access)
router.include_router(dashboards_router, prefix="/dashboards", tags=["BI Dashboards"])
router.include_router(widgets_router, prefix="/dashboards", tags=["BI Widgets"])

# Chart definitions
router.include_router(chart_definitions_router, prefix="/chart-definitions", tags=["BI Chart Definitions"])

# Data sources
router.include_router(data_sources_router, prefix="/data-sources", tags=["BI Data Sources"])
