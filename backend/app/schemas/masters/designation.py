"""Designation schemas."""

from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, AuditSchema
from app.core.constants import EntityStatus


class DesignationBase(BaseSchema):
    """Base designation schema."""

    code: str = Field(..., min_length=2, max_length=20)
    name: str = Field(..., min_length=2, max_length=200)
    short_name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None


class DesignationCreate(DesignationBase):
    """Designation creation schema."""

    department_id: Optional[UUID] = None
    level: int = Field(default=1, ge=1)
    reporting_to_id: Optional[UUID] = None

    # Approval Limits
    approval_limit: Optional[Decimal] = Field(None, ge=0)

    # Requirements
    min_experience_years: int = Field(default=0, ge=0)
    min_qualification: Optional[str] = Field(None, max_length=200)

    # Job details
    job_description: Optional[str] = None
    responsibilities: Optional[str] = None


class DesignationUpdate(BaseSchema):
    """Designation update schema."""

    name: Optional[str] = Field(None, min_length=2, max_length=200)
    short_name: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    department_id: Optional[UUID] = None
    level: Optional[int] = Field(None, ge=1)
    reporting_to_id: Optional[UUID] = None

    # Approval Limits
    approval_limit: Optional[Decimal] = Field(None, ge=0)

    # Requirements
    min_experience_years: Optional[int] = Field(None, ge=0)
    min_qualification: Optional[str] = Field(None, max_length=200)

    # Job details
    job_description: Optional[str] = None
    responsibilities: Optional[str] = None

    status: Optional[str] = None


class DesignationResponse(DesignationBase, AuditSchema):
    """Designation response schema."""

    id: UUID
    department_id: Optional[UUID] = None
    level: int
    reporting_to_id: Optional[UUID] = None

    # Approval Limits
    approval_limit: Optional[Decimal] = None

    # Requirements
    min_experience_years: int
    min_qualification: Optional[str] = None

    # Job details
    job_description: Optional[str] = None
    responsibilities: Optional[str] = None

    status: str

    # Related
    department_name: Optional[str] = None
    reporting_to_name: Optional[str] = None
