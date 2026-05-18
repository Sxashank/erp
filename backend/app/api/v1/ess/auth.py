"""ESS Portal Authentication API endpoints."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, status, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.core.rate_limit import portal_generic_limit, portal_login_limit
from app.services.ess.auth_service import ESSAuthService
from app.core.exceptions import NotFoundException, UnauthorizedException


router = APIRouter(prefix="/auth", tags=["ESS Authentication"])


# ==================== Schemas ====================

class SendOTPRequest(BaseModel):
    """Request to send OTP."""
    mobile: str = Field(..., pattern=r"^\d{10}$", description="10-digit mobile number")


class SendOTPResponse(BaseModel):
    """Response after sending OTP."""
    success: bool
    message: str
    expires_in_seconds: int = 300


class VerifyOTPRequest(BaseModel):
    """Request to verify OTP and login."""
    mobile: str = Field(..., pattern=r"^\d{10}$")
    otp: str = Field(..., min_length=6, max_length=6)


class DeviceInfo(BaseModel):
    """Device information for session."""
    device_type: Optional[str] = None
    device_name: Optional[str] = None
    os_name: Optional[str] = None
    os_version: Optional[str] = None
    browser: Optional[str] = None
    app_version: Optional[str] = None


class LoginRequest(BaseModel):
    """Login request with OTP."""
    mobile: str = Field(..., pattern=r"^\d{10}$")
    otp: str = Field(..., min_length=6, max_length=6)
    device_info: Optional[DeviceInfo] = None


class TokenResponse(BaseModel):
    """Token response after successful login."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class RefreshTokenRequest(BaseModel):
    """Request to refresh token."""
    refresh_token: str


class RegisterDeviceRequest(BaseModel):
    """Request to register device for push notifications."""
    device_uuid: str
    device_name: str
    device_type: str
    fcm_token: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    os_name: Optional[str] = None
    os_version: Optional[str] = None


class SessionResponse(BaseModel):
    """Active session information."""
    id: str
    device_type: Optional[str]
    device_name: Optional[str]
    ip_address: Optional[str]
    login_at: str
    last_activity: Optional[str]
    is_current: bool = False


# ==================== Endpoints ====================

@router.post("/send-otp", response_model=SendOTPResponse, response_model_by_alias=True)
@portal_login_limit()
async def send_otp(
    request: Request,
    data: SendOTPRequest,
    session: AsyncSession = Depends(get_session),
):
    """Send OTP to mobile number for login.

    Rate-limited to 5/min per source IP (CLAUDE.md §8.3).
    """
    service = ESSAuthService(session)

    # Check if user exists
    ess_user = await service.get_ess_user_by_mobile(data.mobile)
    if not ess_user:
        raise NotFoundException(
            detail="No ESS account found for this mobile number",
            error_code="NO_ESS_ACCOUNT_FOUND_FOR_THIS",
        )

    # Send OTP
    otp_code, expires_at = await service.send_otp(
        mobile=data.mobile,
        otp_type="LOGIN",
        ess_user_id=ess_user.id,
    )

    await session.commit()

    return SendOTPResponse(
        success=True,
        message="OTP sent successfully",
        expires_in_seconds=300,
    )


@router.post("/login", response_model=TokenResponse, response_model_by_alias=True)
@portal_login_limit()
async def login(
    request: Request,
    data: LoginRequest,
    session: AsyncSession = Depends(get_session),
):
    """Login with OTP.

    Rate-limited to 5/min per source IP (CLAUDE.md §8.3).
    """
    service = ESSAuthService(session)

    # Get client IP
    ip_address = request.client.host if request.client else None

    # Attempt login
    tokens, error = await service.login_with_otp(
        mobile=data.mobile,
        otp_code=data.otp,
        device_info=data.device_info.model_dump() if data.device_info else None,
        ip_address=ip_address,
    )

    if error:
        raise UnauthorizedException(detail=error, error_code="UNAUTHORIZED")

    await session.commit()

    return TokenResponse(**tokens)


@router.post("/refresh", response_model=TokenResponse, response_model_by_alias=True)
@portal_generic_limit()
async def refresh_token(
    request: Request,
    data: RefreshTokenRequest,
    session: AsyncSession = Depends(get_session),
):
    """Refresh access token.

    Rate-limited to 60/min per source IP (CLAUDE.md §8.3).
    """
    service = ESSAuthService(session)

    tokens, error = await service.refresh_token(data.refresh_token)

    if error:
        raise UnauthorizedException(detail=error, error_code="UNAUTHORIZED")

    await session.commit()

    # Return same format but without user info
    return {
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "token_type": tokens["token_type"],
        "expires_in": tokens["expires_in"],
        "user": {},
    }


@router.post("/logout")
async def logout(
    authorization: str = None,  # Get from header
    session: AsyncSession = Depends(get_session),
):
    """Logout current session."""
    if not authorization:
        raise UnauthorizedException(
            detail="No authorization token provided",
            error_code="NO_AUTHORIZATION_TOKEN_PROVIDED",
        )

    # Extract token from header
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization

    service = ESSAuthService(session)
    await service.logout(token)
    await session.commit()

    return {"success": True, "message": "Logged out successfully"}


@router.post("/logout-all")
async def logout_all_sessions(
    ess_user_id: UUID,  # This would come from authenticated user
    session: AsyncSession = Depends(get_session),
):
    """Logout all sessions for the user."""
    service = ESSAuthService(session)
    count = await service.logout_all_sessions(ess_user_id)
    await session.commit()

    return {"success": True, "message": f"Logged out from {count} sessions"}


@router.get("/sessions", response_model=list[SessionResponse], response_model_by_alias=True)
async def get_active_sessions(
    ess_user_id: UUID,  # This would come from authenticated user
    session: AsyncSession = Depends(get_session),
):
    """Get all active sessions."""
    service = ESSAuthService(session)
    sessions = await service.get_active_sessions(ess_user_id)

    return [
        SessionResponse(
            id=str(s.id),
            device_type=s.device_type,
            device_name=s.device_name,
            ip_address=s.ip_address,
            login_at=s.login_at.isoformat() if s.login_at else None,
            last_activity=s.last_activity.isoformat() if s.last_activity else None,
        )
        for s in sessions
    ]


@router.post("/register-device")
async def register_device(
    request: RegisterDeviceRequest,
    ess_user_id: UUID,  # This would come from authenticated user
    session: AsyncSession = Depends(get_session),
):
    """Register device for push notifications."""
    service = ESSAuthService(session)

    device = await service.register_device(
        ess_user_id=ess_user_id,
        **request.model_dump()
    )

    await session.commit()

    return {
        "success": True,
        "device_id": str(device.id),
        "message": "Device registered successfully",
    }
