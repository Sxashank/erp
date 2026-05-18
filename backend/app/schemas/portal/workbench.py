"""Scheme-portal workbench schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import Field

from app.schemas.base import CamelSchema


class WorkbenchStat(CamelSchema):
    key: str
    label: str
    value: int
    hint: str | None = None


class WorkbenchAction(CamelSchema):
    title: str
    description: str
    href: str
    status: Literal["info", "attention", "success"] = "info"


class WorkbenchApplication(CamelSchema):
    id: UUID
    application_number: str
    entity_legal_name: str | None = None
    product_name: str | None = None
    scheme_status: str
    submitted_at: datetime | None = None
    updated_at: datetime | None = None


class PortalWorkbenchResponse(CamelSchema):
    actor_role: str
    display_name: str
    active_entity_count: int = 0
    stats: list[WorkbenchStat] = Field(default_factory=list)
    priority_actions: list[WorkbenchAction] = Field(default_factory=list)
    recent_applications: list[WorkbenchApplication] = Field(default_factory=list)
