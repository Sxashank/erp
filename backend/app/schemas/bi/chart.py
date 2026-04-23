"""BI Chart Definition schemas."""

from typing import Optional, List
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, AuditSchema
from app.models.bi.enums import ChartType, BIModule


class ChartRoleAccessBase(BaseSchema):
    """Base chart role access schema."""

    role_id: UUID


class ChartRoleAccessCreate(ChartRoleAccessBase):
    """Chart role access creation schema."""
    pass


class ChartRoleAccessResponse(ChartRoleAccessBase, AuditSchema):
    """Chart role access response schema."""

    id: UUID
    chart_definition_id: UUID
    role_name: Optional[str] = None
    role_code: Optional[str] = None


class ChartDefinitionBase(BaseSchema):
    """Base chart definition schema."""

    code: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    module: BIModule
    chart_type: ChartType
    config: Optional[dict] = None
    data_mapping: Optional[dict] = None


class ChartDefinitionCreate(ChartDefinitionBase):
    """Chart definition creation schema."""

    organization_id: Optional[UUID] = None
    default_data_source_id: Optional[UUID] = None
    is_system: bool = False
    role_ids: Optional[List[UUID]] = Field(default_factory=list)


class ChartDefinitionUpdate(BaseSchema):
    """Chart definition update schema."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    default_data_source_id: Optional[UUID] = None
    config: Optional[dict] = None
    data_mapping: Optional[dict] = None


class ChartDefinitionResponse(ChartDefinitionBase, AuditSchema):
    """Chart definition response schema."""

    id: UUID
    organization_id: Optional[UUID] = None
    default_data_source_id: Optional[UUID] = None
    is_system: bool
    role_access: List[ChartRoleAccessResponse] = []


class ChartDefinitionListResponse(BaseSchema):
    """Chart definition list item response schema."""

    id: UUID
    code: str
    name: str
    description: Optional[str] = None
    module: BIModule
    chart_type: ChartType
    is_system: bool
    is_active: bool


class SetChartRoleAccessRequest(BaseSchema):
    """Request to set chart role access."""

    role_ids: List[UUID]
