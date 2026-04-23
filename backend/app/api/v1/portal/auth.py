"""Portal Authentication API endpoints."""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.rate_limit import portal_generic_limit, portal_login_limit
from app.models.portal.enums import OTPPurpose, ConsentType, DeviceType
from app.services.portal.auth_service import PortalAuthService

router = APIRouter(prefix="/auth", tags=["Portal Auth"])


# =============================================================================
# Request/Response Schemas
# =============================================================================


class SendOTPRequest(BaseModel):
    """Send OTP request."""

    organization_id: UUID
    mobile: str = Field(..., min_length=10, max_length=15)
    purpose: OTPPurpose = OTPPurpose.LOGIN


class SendOTPResponse(BaseModel):
    """Send OTP response."""

    success: bool
    message: str
    otp_id: Optional[UUID] = None
    expires_in_seconds: int = 600


class VerifyOTPRequest(BaseModel):
    """Verify OTP request."""

    organization_id: UUID
    mobile: str
    otp: str = Field(..., min_length=4, max_length=8)
    purpose: OTPPurpose = OTPPurpose.LOGIN
    device_info: Optional[Dict[str, Any]] = None


class LoginResponse(BaseModel):
    """Login response."""

    success: bool
    error: Optional[str] = None
    user: Optional[Dict[str, Any]] = None
    session_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""

    refresh_token: str


class DeviceInfo(BaseModel):
    """Device information."""

    device_id: str
    device_type: DeviceType
    device_name: Optional[str] = None
    device_model: Optional[str] = None
    os_version: Optional[str] = None
    app_version: Optional[str] = None
    fcm_token: Optional[str] = None


class DeviceResponse(BaseModel):
    """Device response."""

    id: UUID
    device_id: str
    device_type: str
    device_name: Optional[str] = None
    is_trusted: bool
    first_seen_at: str
    last_seen_at: str


class SessionResponse(BaseModel):
    """Session response."""

    id: UUID
    device_type: Optional[str] = None
    ip_address: Optional[str] = None
    login_at: str
    last_activity_at: str
    is_current: bool


class ConsentRequest(BaseModel):
    """Record consent request."""

    consent_type: ConsentType
    consent_version: str
    is_granted: bool


class ConsentResponse(BaseModel):
    """Consent status response."""

    consents: Dict[str, Any]


# =============================================================================
# Helper to get current portal user
# =============================================================================


async def get_portal_user(
    authorization: str = Header(..., description="Bearer token"),
    db: AsyncSession = Depends(get_db),
):
    """Validate portal session and return user."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
        )

    token = authorization[7:]
    service = PortalAuthService(db)
    user = await service.validate_session(token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
        )

    return user


# =============================================================================
# OTP Endpoints
# =============================================================================


@router.post(
    "/send-otp",
    response_model=SendOTPResponse,
    summary="Send OTP",
)
@portal_login_limit()
async def send_otp(
    request: Request,
    data: SendOTPRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Send OTP to mobile number.

    Rate-limited to 5 requests/min per source IP at the middleware layer
    (CLAUDE.md §8.3); additional service-level throttling further caps to
    5 OTPs per 15 minutes per mobile.
    """
    service = PortalAuthService(db)
    result = await service.send_otp(
        organization_id=data.organization_id,
        mobile=data.mobile,
        purpose=data.purpose,
    )
    await db.commit()

    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=result.get("error"),
        )

    return SendOTPResponse(
        success=True,
        message="OTP sent successfully",
        otp_id=result.get("otp_id"),
        expires_in_seconds=result.get("expires_in_seconds", 600),
    )


@router.post(
    "/verify-otp",
    response_model=LoginResponse,
    summary="Verify OTP & Login",
)
@portal_login_limit()
async def verify_otp(
    request: Request,
    data: VerifyOTPRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Verify OTP and create login session.

    Rate-limited to 5/min per source IP (CLAUDE.md §8.3).
    Returns session tokens on successful verification.
    """
    service = PortalAuthService(db)

    # Verify OTP
    is_valid, error = await service.verify_otp(
        organization_id=data.organization_id,
        mobile=data.mobile,
        otp_code=data.otp,
        purpose=data.purpose,
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error or "OTP verification failed",
        )

    # Create session
    login_result = await service.login(
        organization_id=data.organization_id,
        mobile=data.mobile,
        device_info=data.device_info,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()

    if not login_result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=login_result.get("error"),
        )

    return LoginResponse(**login_result)


# =============================================================================
# Session Management
# =============================================================================


@router.post(
    "/refresh",
    response_model=LoginResponse,
    summary="Refresh Session",
)
@portal_generic_limit()
async def refresh_session(
    request: Request,
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Refresh session using refresh token.

    Rate-limited to 60/min per source IP (CLAUDE.md §8.3).
    """
    service = PortalAuthService(db)
    result = await service.refresh_session(data.refresh_token)
    await db.commit()

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    return LoginResponse(
        success=True,
        session_token=result.get("session_token"),
        refresh_token=result.get("refresh_token"),
        expires_at=result.get("expires_at"),
    )


@router.post(
    "/logout",
    summary="Logout",
)
async def logout(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    """Logout and invalidate session."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header",
        )

    token = authorization[7:]
    service = PortalAuthService(db)
    await service.logout(token)
    await db.commit()

    return {"message": "Logged out successfully"}


@router.get(
    "/sessions",
    response_model=List[SessionResponse],
    summary="Get Active Sessions",
)
async def get_sessions(
    user=Depends(get_portal_user),
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
):
    """Get all active sessions for the user."""
    current_token = authorization[7:] if authorization.startswith("Bearer ") else ""

    service = PortalAuthService(db)
    sessions = await service.get_active_sessions(user.id)

    return [
        SessionResponse(
            id=s.id,
            device_type=s.user_agent[:50] if s.user_agent else None,
            ip_address=s.ip_address,
            login_at=s.login_at.isoformat(),
            last_activity_at=s.last_activity_at.isoformat(),
            is_current=s.session_token == current_token,
        )
        for s in sessions
    ]


@router.delete(
    "/sessions",
    summary="Logout All Sessions",
)
async def logout_all_sessions(
    authorization: str = Header(...),
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """Logout from all sessions except current."""
    current_token = authorization[7:] if authorization.startswith("Bearer ") else ""

    service = PortalAuthService(db)
    count = await service.invalidate_all_sessions(
        user.id, except_session_token=current_token
    )
    await db.commit()

    return {"message": f"Logged out from {count} sessions"}


# =============================================================================
# Device Management
# =============================================================================


@router.get(
    "/devices",
    response_model=List[DeviceResponse],
    summary="Get Registered Devices",
)
async def get_devices(
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all registered devices."""
    service = PortalAuthService(db)
    devices = await service.get_user_devices(user.id)

    return [
        DeviceResponse(
            id=d.id,
            device_id=d.device_id,
            device_type=d.device_type.value,
            device_name=d.device_name,
            is_trusted=d.is_trusted,
            first_seen_at=d.first_seen_at.isoformat(),
            last_seen_at=d.last_seen_at.isoformat(),
        )
        for d in devices
    ]


@router.post(
    "/devices/{device_id}/trust",
    summary="Trust Device",
)
async def trust_device(
    device_id: UUID,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a device as trusted."""
    service = PortalAuthService(db)
    success = await service.trust_device(device_id, user.id)
    await db.commit()

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    return {"message": "Device marked as trusted"}


@router.delete(
    "/devices/{device_id}",
    summary="Block Device",
)
async def block_device(
    device_id: UUID,
    reason: str = "User requested",
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """Block a device."""
    service = PortalAuthService(db)
    success = await service.block_device(device_id, user.id, reason)
    await db.commit()

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found",
        )

    return {"message": "Device blocked"}


# =============================================================================
# Consent Management
# =============================================================================


@router.post(
    "/consents",
    summary="Record Consent",
)
async def record_consent(
    request: ConsentRequest,
    req: Request,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """Record customer consent."""
    service = PortalAuthService(db)
    await service.record_consent(
        user_id=user.id,
        consent_type=request.consent_type,
        consent_version=request.consent_version,
        is_granted=request.is_granted,
        ip_address=req.client.host if req.client else None,
        user_agent=req.headers.get("user-agent"),
    )
    await db.commit()

    return {"message": "Consent recorded"}


@router.get(
    "/consents",
    response_model=ConsentResponse,
    summary="Get Consents",
)
async def get_consents(
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all consents for the user."""
    service = PortalAuthService(db)
    consents = await service.get_user_consents(user.id)

    return ConsentResponse(consents=consents)
