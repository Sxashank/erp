"""Token and authentication schemas."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import EmailStr, Field, field_validator

from app.schemas.base import BaseSchema


class LoginRequest(BaseSchema):
    """Login request schema."""

    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=1)
    otp: Optional[str] = Field(None, min_length=6, max_length=6)


class Token(BaseSchema):
    """Token response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: Optional["UserBasicInfo"] = None


class TokenPayload(BaseSchema):
    """JWT token payload schema."""

    sub: str  # user_id
    exp: datetime
    iat: datetime
    type: str  # access, refresh
    jti: Optional[str] = None  # JWT ID for refresh tokens
    roles: Optional[List[str]] = None
    permissions: Optional[List[str]] = None


class RefreshTokenRequest(BaseSchema):
    """Refresh token request schema."""

    refresh_token: str


class ChangePasswordRequest(BaseSchema):
    """Change password request schema."""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        """Validate that passwords match."""
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class ResetPasswordRequest(BaseSchema):
    """Reset password request schema."""

    token: str
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        """Validate that passwords match."""
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class ForgotPasswordRequest(BaseSchema):
    """Forgot password request schema."""

    email: EmailStr


class MFASetupResponse(BaseSchema):
    """MFA setup response schema."""

    secret: str
    provisioning_uri: str
    qr_code_base64: Optional[str] = None


class MFAVerifyRequest(BaseSchema):
    """MFA verification request schema."""

    otp: str = Field(..., min_length=6, max_length=6)
    mfa_token: Optional[str] = None  # Temporary token from login


class UserBasicInfo(BaseSchema):
    """Basic user info for token response."""

    id: UUID
    username: str
    email: str
    full_name: str
    roles: List[str] = []
    permissions: List[str] = []


# Update forward reference
Token.model_rebuild()
