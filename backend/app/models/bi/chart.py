"""BI Chart Definition and Chart Role Access models."""

from typing import TYPE_CHECKING, Optional, List
from uuid import UUID

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.bi.enums import ChartType, BIModule


if TYPE_CHECKING:
    from app.models.masters.organization import Organization
    from app.models.bi.datasource import DataSource
    from app.models.auth.role import Role


class ChartDefinition(BaseModel):
    """BI Chart Definition - pre-designed charts that can be added to dashboards."""

    __tablename__ = "bi_chart_definition"

    # Unique code
    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Unique chart code e.g., FIN_REV_MTD",
    )

    # Basic info
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Chart name",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Chart description",
    )

    # Organization scope (null = system-wide)
    organization_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Organization (null = system-wide chart)",
    )

    # Module tag
    module: Mapped[BIModule] = mapped_column(
        Enum(BIModule),
        nullable=False,
        index=True,
        comment="Module this chart belongs to",
    )

    # Chart type
    chart_type: Mapped[ChartType] = mapped_column(
        Enum(ChartType),
        nullable=False,
        comment="Type of chart visualization",
    )

    # Default data source
    default_data_source_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("bi_data_source.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Default data source for this chart",
    )

    # Chart configuration
    config: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Chart configuration (colors, legend, etc.)",
    )

    # Data mapping
    data_mapping: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="How to map data source fields to chart fields",
    )

    # System flag
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="True for pre-built system charts",
    )

    # Relationships
    organization: Mapped[Optional["Organization"]] = relationship(
        "Organization",
        lazy="selectin",
    )
    default_data_source: Mapped[Optional["DataSource"]] = relationship(
        "DataSource",
        lazy="selectin",
    )
    role_access: Mapped[List["ChartRoleAccess"]] = relationship(
        "ChartRoleAccess",
        back_populates="chart_definition",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_bi_chart_code_unique", "code", unique=True),
        Index("ix_bi_chart_org_module", "organization_id", "module"),
    )

    def __repr__(self) -> str:
        return f"<ChartDefinition(code={self.code}, module={self.module})>"


class ChartRoleAccess(BaseModel):
    """Defines which roles can use which chart definitions."""

    __tablename__ = "bi_chart_role_access"

    # Chart definition
    chart_definition_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("bi_chart_definition.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Chart definition ID",
    )

    # Role
    role_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_role.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Role ID",
    )

    # Relationships
    chart_definition: Mapped["ChartDefinition"] = relationship(
        "ChartDefinition",
        back_populates="role_access",
        lazy="selectin",
    )
    role: Mapped["Role"] = relationship(
        "Role",
        lazy="selectin",
    )

    __table_args__ = (
        Index(
            "ix_bi_chart_role_access_unique",
            "chart_definition_id",
            "role_id",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return f"<ChartRoleAccess(chart={self.chart_definition_id}, role={self.role_id})>"
