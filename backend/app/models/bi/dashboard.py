"""BI Dashboard, Widget, and Role Access models."""

from typing import TYPE_CHECKING, Optional, List
from uuid import UUID

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.bi.enums import WidgetType


if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.bi.chart import ChartDefinition
    from app.models.bi.datasource import DataSource
    from app.models.auth.role import Role


class Dashboard(BaseModel):
    """BI Dashboard - container for widgets."""

    __tablename__ = "bi_dashboard"

    # Unique code
    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Unique dashboard code",
    )

    # Basic info
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Dashboard name",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Dashboard description",
    )

    # Organization scope
    organization_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Organization this dashboard belongs to",
    )

    # Dashboard settings
    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Is this the default dashboard for the organization?",
    )
    is_public: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Is this dashboard visible to all users?",
    )

    # Layout configuration
    layout_config: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Grid layout configuration",
    )

    # Display order
    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Display order in lists",
    )

    # Auto-refresh settings
    auto_refresh: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Enable auto-refresh?",
    )
    refresh_interval_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=60,
        comment="Auto-refresh interval in seconds",
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(
        "Organization",
        lazy="selectin",
    )
    widgets: Mapped[List["DashboardWidget"]] = relationship(
        "DashboardWidget",
        back_populates="dashboard",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="DashboardWidget.display_order",
    )
    role_access: Mapped[List["DashboardRoleAccess"]] = relationship(
        "DashboardRoleAccess",
        back_populates="dashboard",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_bi_dashboard_org_code", "organization_id", "code", unique=True),
    )

    def __repr__(self) -> str:
        return f"<Dashboard(code={self.code}, name={self.name})>"


class DashboardWidget(BaseModel):
    """Widget within a dashboard."""

    __tablename__ = "bi_dashboard_widget"

    # Parent dashboard
    dashboard_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("bi_dashboard.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent dashboard ID",
    )

    # Widget key (unique within dashboard)
    widget_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Unique key within dashboard",
    )

    # Widget title
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Widget title",
    )

    # Widget type
    widget_type: Mapped[WidgetType] = mapped_column(
        Enum(WidgetType),
        nullable=False,
        comment="Type of widget",
    )

    # Optional chart definition reference
    chart_definition_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("bi_chart_definition.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Pre-defined chart to use (optional)",
    )

    # Optional data source override
    data_source_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("bi_data_source.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Data source override (optional)",
    )

    # Grid position
    grid_x: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Grid X position",
    )
    grid_y: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Grid Y position",
    )
    grid_w: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=4,
        comment="Grid width (columns)",
    )
    grid_h: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3,
        comment="Grid height (rows)",
    )

    # Widget configuration
    config: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Widget-specific configuration",
    )

    # Display order
    display_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Display order",
    )

    # Relationships
    dashboard: Mapped["Dashboard"] = relationship(
        "Dashboard",
        back_populates="widgets",
        lazy="selectin",
    )
    chart_definition: Mapped[Optional["ChartDefinition"]] = relationship(
        "ChartDefinition",
        lazy="selectin",
    )
    data_source: Mapped[Optional["DataSource"]] = relationship(
        "DataSource",
        lazy="selectin",
    )

    __table_args__ = (
        Index(
            "ix_bi_widget_dashboard_key",
            "dashboard_id",
            "widget_key",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return f"<DashboardWidget(key={self.widget_key}, type={self.widget_type})>"


class DashboardRoleAccess(BaseModel):
    """Defines role access to dashboards."""

    __tablename__ = "bi_dashboard_role_access"

    # Dashboard
    dashboard_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("bi_dashboard.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Dashboard ID",
    )

    # Role
    role_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_role.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Role ID",
    )

    # Permissions
    can_view: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="Can view this dashboard?",
    )
    can_edit: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Can edit this dashboard?",
    )

    # Landing page settings
    show_on_landing: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="Show on landing page for this role?",
    )
    landing_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Order on landing page",
    )

    # Relationships
    dashboard: Mapped["Dashboard"] = relationship(
        "Dashboard",
        back_populates="role_access",
        lazy="selectin",
    )
    role: Mapped["Role"] = relationship(
        "Role",
        lazy="selectin",
    )

    __table_args__ = (
        Index(
            "ix_bi_dashboard_role_access_unique",
            "dashboard_id",
            "role_id",
            unique=True,
        ),
        Index("ix_bi_dashboard_role_landing", "role_id", "show_on_landing"),
    )

    def __repr__(self) -> str:
        return f"<DashboardRoleAccess(dashboard={self.dashboard_id}, role={self.role_id})>"
