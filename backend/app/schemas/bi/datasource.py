"""BI Data Source schemas."""

from typing import Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, AuditSchema
from app.models.bi.enums import DataSourceType, APIMethod


class DataSourceBase(BaseSchema):
    """Base data source schema."""

    code: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    source_type: DataSourceType
    api_endpoint: Optional[str] = Field(None, max_length=500)
    api_method: Optional[APIMethod] = APIMethod.GET
    query_template: Optional[str] = None
    static_data: Optional[dict] = None
    parameters_schema: Optional[dict] = None
    response_transform: Optional[dict] = None
    cache_ttl_seconds: int = Field(default=300, ge=0)


class DataSourceCreate(DataSourceBase):
    """Data source creation schema."""

    organization_id: Optional[UUID] = None


class DataSourceUpdate(BaseSchema):
    """Data source update schema."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    api_endpoint: Optional[str] = Field(None, max_length=500)
    api_method: Optional[APIMethod] = None
    query_template: Optional[str] = None
    static_data: Optional[dict] = None
    parameters_schema: Optional[dict] = None
    response_transform: Optional[dict] = None
    cache_ttl_seconds: Optional[int] = Field(None, ge=0)


class DataSourceResponse(DataSourceBase, AuditSchema):
    """Data source response schema."""

    id: UUID
    organization_id: Optional[UUID] = None


class DataSourceListResponse(BaseSchema):
    """Data source list item response schema."""

    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    source_type: DataSourceType
    organization_id: Optional[UUID] = None
    cache_ttl_seconds: int = Field(default=300, ge=0)
    is_active: bool


class DataSourceFetchRequest(BaseSchema):
    """Request to fetch data from a data source."""

    parameters: Optional[dict] = None


class DataSourceFetchResponse(BaseSchema):
    """Response from fetching data source."""

    data: dict
    cached: bool = False
