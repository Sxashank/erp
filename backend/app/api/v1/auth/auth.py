"""Authentication API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.core.rate_limit import auth_login_limit, auth_refresh_limit
from app.models.auth.user import User
from app.services.auth.auth_service import AuthService
from app.schemas.auth.token import (
    Token,
    LoginRequest,
    RefreshTokenRequest,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.schemas.auth.user import UserResponse
from app.schemas.base import MessageResponse

router = APIRouter()


@router.post("/login", response_model=Token)
@auth_login_limit()
async def login(
    request: Request,
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Login with username/email and password.
    Returns JWT access and refresh tokens.

    Rate-limited to 5/min per source IP (CLAUDE.md §8.3).
    """
    # Get client info
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    auth_service = AuthService(db)
    token, requires_mfa = await auth_service.login(data, ip_address, user_agent)

    if requires_mfa:
        # Return indication that MFA is required
        return {"requires_mfa": True, "message": "MFA verification required"}

    return token


@router.post("/refresh", response_model=Token)
@auth_refresh_limit()
async def refresh_token(
    request: Request,
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Refresh access token using refresh token.

    Rate-limited to 20/min per source IP (CLAUDE.md §8.3).
    """
    ip_address = request.client.host if request.client else None

    auth_service = AuthService(db)
    return await auth_service.refresh_token(data.refresh_token, ip_address)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Logout by revoking refresh token.
    """
    auth_service = AuthService(db)
    await auth_service.logout(data.refresh_token)
    return MessageResponse(message="Successfully logged out")


@router.post("/logout-all", response_model=MessageResponse)
async def logout_all(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Logout from all devices by revoking all refresh tokens.
    """
    auth_service = AuthService(db)
    count = await auth_service.logout_all(current_user.id)
    return MessageResponse(message=f"Logged out from {count} sessions")


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Change current user's password.
    """
    auth_service = AuthService(db)
    await auth_service.change_password(
        current_user.id,
        data.current_password,
        data.new_password,
    )
    return MessageResponse(message="Password changed successfully")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current authenticated user's profile.
    """
    from app.repositories.auth.user_repo import UserRepository

    user_repo = UserRepository(db)
    permissions = await user_repo.get_user_permissions(current_user.id)

    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        employee_code=current_user.employee_code,
        phone=current_user.phone,
        timezone=current_user.timezone,
        auth_type=current_user.auth_type,
        mfa_enabled=current_user.mfa_enabled,
        status=current_user.status,
        organization_id=current_user.organization_id,
        organization_name=current_user.organization.name if current_user.organization else None,
        default_unit_id=current_user.default_unit_id,
        default_unit_name=current_user.default_unit.name if current_user.default_unit else None,
        last_login_at=current_user.last_login_at,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        is_active=current_user.is_active,
        roles=[
            {
                "id": ur.role.id,
                "code": ur.role.code,
                "name": ur.role.name,
                "unit_id": ur.unit_id,
                "unit_name": ur.unit.name if ur.unit else None,
            }
            for ur in current_user.user_roles
            if ur.is_valid
        ],
        permissions=list(permissions),
    )


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Request password reset.
    In production, this would send an email with the reset link.
    For development, returns the token in response.
    """
    auth_service = AuthService(db)
    token = await auth_service.forgot_password(data.email)

    # In production, send email here and don't return token
    # For now, return success message regardless (security best practice)
    if token:
        # Development only - return token for testing
        return MessageResponse(
            message="Password reset instructions sent",
            data={"reset_token": token}  # Remove this in production
        )

    return MessageResponse(message="If the email exists, password reset instructions have been sent")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Reset password using reset token.
    """
    auth_service = AuthService(db)
    await auth_service.reset_password(data.token, data.new_password)
    return MessageResponse(message="Password reset successfully")
