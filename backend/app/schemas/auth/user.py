"""User schemas."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from app.schemas.base import BaseSchema, AuditSchema
from app.core.constants import UserStatus, AuthType
from app.core.pii import MaskedPIIModel


class UserBase(BaseSchema):
    """Base user schema."""

    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=200)
    employee_code: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    timezone: str = Field(default="Asia/Kolkata", max_length=50)


class UserCreate(UserBase):
    """User creation schema."""

    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)
    organization_id: Optional[UUID] = None
    default_unit_id: Optional[UUID] = None
    role_ids: Optional[List[UUID]] = Field(default_factory=list)
    mfa_enabled: bool = False
    status: str = Field(default=UserStatus.ACTIVE.value)

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        """Validate that passwords match."""
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserUpdate(BaseSchema):
    """User update schema."""

    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=200)
    employee_code: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    timezone: Optional[str] = Field(None, max_length=50)
    organization_id: Optional[UUID] = None
    default_unit_id: Optional[UUID] = None
    status: Optional[str] = None
    mfa_enabled: Optional[bool] = None


class UserRoleInfo(BaseSchema):
    """User role info schema."""

    id: UUID
    code: str
    name: str
    unit_id: Optional[UUID] = None
    unit_name: Optional[str] = None


class UserResponse(MaskedPIIModel, UserBase, AuditSchema):
    """User response schema."""

    id: UUID
    auth_type: str
    mfa_enabled: bool
    status: str
    organization_id: Optional[UUID] = None
    organization_name: Optional[str] = None
    default_unit_id: Optional[UUID] = None
    default_unit_name: Optional[str] = None
    last_login_at: Optional[datetime] = None
    roles: List[UserRoleInfo] = []
    permissions: List[str] = []


class UserListResponse(BaseSchema):
    """User list item response schema."""

    id: UUID
    username: str
    email: str
    full_name: str
    employee_code: Optional[str] = None
    status: str
    organization_name: Optional[str] = None
    default_unit_name: Optional[str] = None
    last_login_at: Optional[datetime] = None
    roles: List[str] = []
    is_active: bool


class UserRoleAssign(BaseSchema):
    """User role assignment schema."""

    role_id: UUID
    unit_id: Optional[UUID] = None
    effective_from: datetime
    effective_to: Optional[datetime] = None
