"""BI/Analytics module enums."""

from enum import Enum


class WidgetType(str, Enum):
    """Widget types for dashboard widgets."""
    KPI_CARD = "KPI_CARD"
    LINE_CHART = "LINE_CHART"
    BAR_CHART = "BAR_CHART"
    PIE_CHART = "PIE_CHART"
    DONUT_CHART = "DONUT_CHART"
    AREA_CHART = "AREA_CHART"
    DATA_TABLE = "DATA_TABLE"
    TEXT_MARKDOWN = "TEXT_MARKDOWN"
    GAUGE_PROGRESS = "GAUGE_PROGRESS"


class ChartType(str, Enum):
    """Chart types for chart definitions."""
    LINE = "LINE"
    BAR = "BAR"
    PIE = "PIE"
    DONUT = "DONUT"
    AREA = "AREA"
    GAUGE = "GAUGE"
    KPI = "KPI"
    TABLE = "TABLE"


class BIModule(str, Enum):
    """Module tags for BI charts."""
    FINANCE = "FINANCE"
    LENDING = "LENDING"
    HR = "HR"
    TREASURY = "TREASURY"
    PROCUREMENT = "PROCUREMENT"
    INVENTORY = "INVENTORY"
    TAX = "TAX"
    COLLECTIONS = "COLLECTIONS"
    LEGAL = "LEGAL"
    PORTAL = "PORTAL"


class DataSourceType(str, Enum):
    """Data source types."""
    API_ENDPOINT = "API_ENDPOINT"
    SQL_QUERY = "SQL_QUERY"
    STATIC = "STATIC"


class APIMethod(str, Enum):
    """HTTP methods for API data sources."""
    GET = "GET"
    POST = "POST"
