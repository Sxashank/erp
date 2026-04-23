"""Vendor Portal Authentication Routes."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import UnauthorizedException
from app.core.rate_limit import portal_generic_limit, portal_login_limit
from app.services.vendor_portal.auth_service import VendorPortalAuthService
from app.models.vendor_portal.enums import VendorOTPPurpose
from app.schemas.vendor_portal.auth import (
    VendorLoginRequest,
    VendorLoginResponse,
    VendorOTPRequest,
    VendorOTPVerifyRequest,
    VendorPasswordResetRequest,
    VendorChangePasswordRequest,
    VendorRefreshTokenRequest,
    VendorUserProfile,
    VendorUserProfileUpdate,
)

router = APIRouter()


def get_client_ip(request: Request) -> str:
    """Get client IP from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_device_type(request: Request) -> str:
    """Get device type from user agent."""
    user_agent = request.headers.get("User-Agent", "").lower()
    if "mobile" in user_agent:
        return "mobile"
    elif "tablet" in user_agent:
        return "tablet"
    return "desktop"


@router.post("/login", response_model=VendorLoginResponse)
@portal_login_limit()
async def login(
    request: Request,
    data: VendorLoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Login with email/password or OTP."""
    service = VendorPortalAuthService(db)
    ip_address = get_client_ip(request)
    device_type = get_device_type(request)

    if data.otp:
        session, user = await service.login_with_otp(
            email=data.email,
            otp=data.otp,
            ip_address=ip_address,
            device_type=device_type,
        )
    else:
        if not data.password:
            raise UnauthorizedException("Password or OTP is required")
        session, user = await service.login_with_password(
            email=data.email,
            password=data.password,
            ip_address=ip_address,
            device_type=device_type,
        )

    return VendorLoginResponse(
        access_token=session.session_token,
        refresh_token=session.refresh_token,
        token_type="bearer",
        expires_in=86400,  # 24 hours
        user=VendorUserProfile(
            id=user.id,
            email=user.email,
            phone=user.phone,
            first_name=user.first_name,
            last_name=user.last_name,
            vendor_id=user.vendor_id,
            organization_id=user.organization_id,
            is_primary_contact=user.is_primary_contact,
            permissions={
                "can_view_pos": user.can_view_pos,
                "can_acknowledge_pos": user.can_acknowledge_pos,
                "can_submit_invoices": user.can_submit_invoices,
                "can_create_asn": user.can_create_asn,
                "can_view_payments": user.can_view_payments,
                "can_manage_users": user.can_manage_users,
                "can_manage_compliance": user.can_manage_compliance,
            },
        ),
    )


@router.post("/request-otp", status_code=status.HTTP_204_NO_CONTENT)
@portal_login_limit()
async def request_otp(
    request: Request,
    data: VendorOTPRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Request OTP for login or password reset."""
    service = VendorPortalAuthService(db)
    purpose = VendorOTPPurpose(data.purpose) if data.purpose else VendorOTPPurpose.LOGIN

    await service.generate_otp(
        email=data.email,
        phone=data.phone,
        purpose=purpose,
        organization_id=data.organization_id,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/verify-otp")
@portal_login_limit()
async def verify_otp(
    request: Request,
    data: VendorOTPVerifyRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Verify OTP."""
    service = VendorPortalAuthService(db)
    purpose = VendorOTPPurpose(data.purpose) if data.purpose else VendorOTPPurpose.LOGIN

    is_valid = await service.verify_otp(
        email=data.email,
        phone=data.phone,
        otp=data.otp,
        purpose=purpose,
    )

    return {"valid": is_valid}


@router.post("/refresh")
@portal_generic_limit()
async def refresh_token(
    request: Request,
    data: VendorRefreshTokenRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Refresh access token."""
    service = VendorPortalAuthService(db)

    access_token, refresh_token = await service.refresh_token(data.refresh_token)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 86400,
    }


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    session_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Logout and invalidate session."""
    service = VendorPortalAuthService(db)
    await service.logout(session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/forgot-password", status_code=status.HTTP_204_NO_CONTENT)
async def forgot_password(
    data: VendorOTPRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Request password reset OTP."""
    service = VendorPortalAuthService(db)

    await service.generate_otp(
        email=data.email,
        purpose=VendorOTPPurpose.PASSWORD_RESET,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    data: VendorPasswordResetRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Reset password using OTP."""
    service = VendorPortalAuthService(db)

    await service.reset_password(
        email=data.email,
        otp=data.otp,
        new_password=data.new_password,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    user_id: UUID,  # From auth middleware
    data: VendorChangePasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Change password."""
    service = VendorPortalAuthService(db)

    await service.change_password(
        user_id=user_id,
        current_password=data.current_password,
        new_password=data.new_password,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=VendorUserProfile)
async def get_current_user(
    user_id: UUID,  # From auth middleware
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get current user profile."""
    service = VendorPortalAuthService(db)
    user = await service.get_current_user(user_id)

    return VendorUserProfile(
        id=user.id,
        email=user.email,
        phone=user.phone,
        first_name=user.first_name,
        last_name=user.last_name,
        designation=user.designation,
        department=user.department,
        vendor_id=user.vendor_id,
        organization_id=user.organization_id,
        is_primary_contact=user.is_primary_contact,
        email_verified=user.email_verified,
        phone_verified=user.phone_verified,
        last_login_at=user.last_login_at,
        permissions={
            "can_view_pos": user.can_view_pos,
            "can_acknowledge_pos": user.can_acknowledge_pos,
            "can_submit_invoices": user.can_submit_invoices,
            "can_create_asn": user.can_create_asn,
            "can_view_payments": user.can_view_payments,
            "can_manage_users": user.can_manage_users,
            "can_manage_compliance": user.can_manage_compliance,
        },
    )


@router.put("/me", response_model=VendorUserProfile)
async def update_current_user(
    user_id: UUID,  # From auth middleware
    data: VendorUserProfileUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Update current user profile."""
    # This would use profile service to update user
    # For now, just return the current user
    service = VendorPortalAuthService(db)
    user = await service.get_current_user(user_id)

    return VendorUserProfile(
        id=user.id,
        email=user.email,
        phone=user.phone,
        first_name=user.first_name,
        last_name=user.last_name,
        designation=user.designation,
        department=user.department,
        vendor_id=user.vendor_id,
        organization_id=user.organization_id,
        is_primary_contact=user.is_primary_contact,
        email_verified=user.email_verified,
        phone_verified=user.phone_verified,
        last_login_at=user.last_login_at,
        permissions={
            "can_view_pos": user.can_view_pos,
            "can_acknowledge_pos": user.can_acknowledge_pos,
            "can_submit_invoices": user.can_submit_invoices,
            "can_create_asn": user.can_create_asn,
            "can_view_payments": user.can_view_payments,
            "can_manage_users": user.can_manage_users,
            "can_manage_compliance": user.can_manage_compliance,
        },
    )
