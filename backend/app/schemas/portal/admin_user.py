"""Admin schemas for integrated scheme-portal users."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.base import CamelSchema


class AdminPortalUserEntityLink(CamelSchema):
    entity_id: UUID
    legal_name: str


class AdminPortalUserListItem(CamelSchema):
    portal_user_id: UUID
    mobile: str
    email: str | None = None
    display_name: str | None = None
    actor_role: str
    registration_status: str
    status: str
    linked_entity_ids: list[UUID] = Field(default_factory=list)
    linked_entities: list[AdminPortalUserEntityLink] = Field(default_factory=list)
    last_login_at: datetime | None = None
    created_at: datetime


class AdminPortalUserDetail(AdminPortalUserListItem):
    preferred_language: str | None = None
    approved_at: datetime | None = None
    approved_by: UUID | None = None
    mobile_verified: bool = False
    email_verified: bool = False
    is_2fa_enabled: bool = False
    password_login_enabled: bool = False
    invite_pending: bool = False
    invited_at: datetime | None = None
    invite_expires_at: datetime | None = None
    activated_at: datetime | None = None


class AdminPortalUserListResponse(CamelSchema):
    items: list[AdminPortalUserListItem]
    total: int
    page: int
    page_size: int


class AdminPortalInviteResponse(CamelSchema):
    portal_user_id: UUID
    email: str
    invite_expires_at: datetime
    activation_token: str
    activation_url: str


class AdminPortalUserCreateRequest(CamelSchema):
    mobile: str = Field(..., min_length=10, max_length=15)
    email: str | None = Field(None, max_length=255)
    display_name: str = Field(..., min_length=2, max_length=200)
    actor_role: str
    preferred_language: str = Field(default="en", max_length=5)
    status: str = Field(default="ACTIVE")
    linked_entity_ids: list[UUID] = Field(default_factory=list)


class AdminPortalUserUpdateRequest(CamelSchema):
    email: str | None = Field(None, max_length=255)
    display_name: str | None = Field(None, min_length=2, max_length=200)
    actor_role: str | None = None
    preferred_language: str | None = Field(None, max_length=5)
    status: str | None = None
    linked_entity_ids: list[UUID] | None = None
