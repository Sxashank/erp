"""BI Data Source model."""

from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Integer, String, Text, Index
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.bi.enums import DataSourceType, APIMethod


if TYPE_CHECKING:
    from app.models.masters.organization import Organization


class DataSource(BaseModel):
    """BI Data Source - defines where widget data comes from."""

    __tablename__ = "bi_data_source"

    # Unique code
    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Unique data source code",
    )

    # Basic info
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Data source name",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Data source description",
    )

    # Organization scope (null = system-wide)
    organization_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mst_organization.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Organization (null = system-wide data source)",
    )

    # Source type
    source_type: Mapped[DataSourceType] = mapped_column(
        Enum(DataSourceType),
        nullable=False,
        comment="Type of data source",
    )

    # API endpoint configuration
    api_endpoint: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="API endpoint path (for API_ENDPOINT type)",
    )
    api_method: Mapped[Optional[APIMethod]] = mapped_column(
        Enum(APIMethod),
        nullable=True,
        default=APIMethod.GET,
        comment="HTTP method for API calls",
    )

    # SQL query configuration
    query_template: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="SQL query template (for SQL_QUERY type)",
    )

    # Static data configuration
    static_data: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Static data (for STATIC type)",
    )

    # Parameters schema - defines what parameters can be passed
    parameters_schema: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="JSON schema for parameters",
    )

    # Response transformation
    response_transform: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="Response transformation config (field mappings, etc.)",
    )

    # Caching
    cache_ttl_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=300,
        comment="Cache TTL in seconds (0 = no caching)",
    )

    # Relationships
    organization: Mapped[Optional["Organization"]] = relationship(
        "Organization",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_bi_datasource_code_unique", "code", unique=True),
        Index("ix_bi_datasource_org_code", "organization_id", "code"),
    )

    def __repr__(self) -> str:
        return f"<DataSource(code={self.code}, type={self.source_type})>"
