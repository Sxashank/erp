"""BI Dashboard schemas."""

from typing import Optional, List
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, AuditSchema
from app.models.bi.enums import WidgetType, ChartType, BIModule


# Widget schemas
class DashboardWidgetBase(BaseSchema):
    """Base dashboard widget schema."""

    widget_key: str = Field(..., min_length=1, max_length=100)
    title: str = Field(..., min_length=1, max_length=200)
    widget_type: WidgetType
    grid_x: int = Field(default=0, ge=0)
    grid_y: int = Field(default=0, ge=0)
    grid_w: int = Field(default=4, ge=1, le=12)
    grid_h: int = Field(default=3, ge=1, le=12)
    config: Optional[dict] = None
    display_order: int = 0


class DashboardWidgetCreate(DashboardWidgetBase):
    """Dashboard widget creation schema."""

    chart_definition_id: Optional[UUID] = None
    data_source_id: Optional[UUID] = None


class DashboardWidgetUpdate(BaseSchema):
    """Dashboard widget update schema."""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    grid_x: Optional[int] = Field(None, ge=0)
    grid_y: Optional[int] = Field(None, ge=0)
    grid_w: Optional[int] = Field(None, ge=1, le=12)
    grid_h: Optional[int] = Field(None, ge=1, le=12)
    config: Optional[dict] = None
    display_order: Optional[int] = None
    chart_definition_id: Optional[UUID] = None
    data_source_id: Optional[UUID] = None


class DashboardWidgetLayoutUpdate(BaseSchema):
    """Layout update for a single widget."""

    widget_id: UUID
    grid_x: int = Field(..., ge=0)
    grid_y: int = Field(..., ge=0)
    grid_w: int = Field(..., ge=1, le=12)
    grid_h: int = Field(..., ge=1, le=12)


class BulkLayoutUpdateRequest(BaseSchema):
    """Bulk widget layout update request."""

    layouts: List[DashboardWidgetLayoutUpdate]


class ChartDefinitionBrief(BaseSchema):
    """Brief chart definition info for widget response."""

    id: UUID
    code: str
    name: str
    chart_type: ChartType
    module: BIModule


class DataSourceBrief(BaseSchema):
    """Brief data source info for widget response."""

    id: UUID
    code: str
    name: str


class DashboardWidgetResponse(DashboardWidgetBase, AuditSchema):
    """Dashboard widget response schema."""

    id: UUID
    dashboard_id: UUID
    chart_definition_id: Optional[UUID] = None
    data_source_id: Optional[UUID] = None
    chart_definition: Optional[ChartDefinitionBrief] = None
    data_source: Optional[DataSourceBrief] = None


# Role access schemas
class DashboardRoleAccessBase(BaseSchema):
    """Base dashboard role access schema."""

    role_id: UUID
    can_view: bool = True
    can_edit: bool = False
    show_on_landing: bool = False
    landing_order: int = 0


class DashboardRoleAccessCreate(DashboardRoleAccessBase):
    """Dashboard role access creation schema."""
    pass


class DashboardRoleAccessUpdate(BaseSchema):
    """Dashboard role access update schema."""

    can_view: Optional[bool] = None
    can_edit: Optional[bool] = None
    show_on_landing: Optional[bool] = None
    landing_order: Optional[int] = None


class DashboardRoleAccessResponse(DashboardRoleAccessBase, AuditSchema):
    """Dashboard role access response schema."""

    id: UUID
    dashboard_id: UUID
    role_name: Optional[str] = None
    role_code: Optional[str] = None


# Dashboard schemas
class DashboardBase(BaseSchema):
    """Base dashboard schema."""

    code: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    is_default: bool = False
    is_public: bool = False
    layout_config: Optional[dict] = None
    display_order: int = 0
    auto_refresh: bool = False
    refresh_interval_seconds: int = Field(default=60, ge=10)


class DashboardCreate(DashboardBase):
    """Dashboard creation schema."""

    organization_id: UUID


class DashboardUpdate(BaseSchema):
    """Dashboard update schema."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    is_default: Optional[bool] = None
    is_public: Optional[bool] = None
    layout_config: Optional[dict] = None
    display_order: Optional[int] = None
    auto_refresh: Optional[bool] = None
    refresh_interval_seconds: Optional[int] = Field(None, ge=10)


class DashboardResponse(DashboardBase, AuditSchema):
    """Dashboard response schema."""

    id: UUID
    organization_id: UUID
    widgets: List[DashboardWidgetResponse] = []
    role_access: List[DashboardRoleAccessResponse] = []


class DashboardListResponse(BaseSchema):
    """Dashboard list item response schema."""

    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    is_default: bool
    is_public: bool
    display_order: int
    widget_count: int = 0
    is_active: bool


class LandingDashboardResponse(BaseSchema):
    """Dashboard for landing page."""

    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    display_order: int
    landing_order: int
    auto_refresh: bool
    refresh_interval_seconds: int
    widgets: List[DashboardWidgetResponse] = []
