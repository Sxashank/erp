"""Portal Authentication API endpoints."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.database import clear_tenant_context, set_tenant_context
from app.config import settings
from app.core.rate_limit import portal_generic_limit, portal_login_limit
from app.models.masters.organization import Organization
from app.models.portal.enums import ConsentType, DeviceType, OTPPurpose
from app.models.portal.portal_user import PortalUser
from app.services.portal.auth_service import PortalAuthService
from app.core.exceptions import AppException, BadRequestException, ForbiddenException as _ForbiddenException, NotFoundException, ServiceUnavailableException, UnauthorizedException

router = APIRouter(prefix="/auth", tags=["Portal Auth"])


# =============================================================================
# Request/Response Schemas
# =============================================================================


class SendOTPRequest(BaseModel):
    """Send OTP request."""

    organization_id: UUID | None = None
    mobile: str = Field(..., min_length=10, max_length=15)
    purpose: OTPPurpose = OTPPurpose.LOGIN


class SendOTPResponse(BaseModel):
    """Send OTP response."""

    success: bool
    message: str
    otp_id: UUID | None = None
    expires_in_seconds: int = 600


class VerifyOTPRequest(BaseModel):
    """Verify OTP request."""

    organization_id: UUID | None = None
    mobile: str
    otp: str = Field(..., min_length=4, max_length=8)
    purpose: OTPPurpose = OTPPurpose.LOGIN
    device_info: dict[str, Any] | None = None


class LoginResponse(BaseModel):
    """Login response."""

    success: bool
    error: str | None = None
    user: dict[str, Any] | None = None
    access_token: str | None = None
    session_token: str | None = None
    refresh_token: str | None = None
    expires_at: str | None = None
    requires_mfa: bool = False
    message: str | None = None


class RefreshTokenRequest(BaseModel):
    """Refresh token request."""

    refresh_token: str


class PasswordLoginRequest(BaseModel):
    organization_id: UUID | None = None
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=8, max_length=255)
    otp: str | None = Field(None, min_length=6, max_length=6)
    device_info: dict[str, Any] | None = None


class ActivateInviteRequest(BaseModel):
    token: str = Field(..., min_length=20)
    password: str = Field(..., min_length=8, max_length=255)
    device_info: dict[str, Any] | None = None


class ForgotPasswordRequest(BaseModel):
    organization_id: UUID | None = None
    email: str = Field(..., min_length=5, max_length=255)


class ForgotPasswordResponse(BaseModel):
    success: bool
    message: str
    reset_token: str | None = None
    reset_url: str | None = None
    expires_at: str | None = None


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=20)
    new_password: str = Field(..., min_length=8, max_length=255)


class MfaSetupResponse(BaseModel):
    secret: str
    provisioning_uri: str
    is_enabled: bool


class MfaVerifyRequest(BaseModel):
    otp: str = Field(..., min_length=6, max_length=6)


class DeviceInfo(BaseModel):
    """Device information."""

    device_id: str
    device_type: DeviceType
    device_name: str | None = None
    device_model: str | None = None
    os_version: str | None = None
    app_version: str | None = None
    fcm_token: str | None = None


class DeviceResponse(BaseModel):
    """Device response."""

    id: UUID
    device_id: str
    device_type: str
    device_name: str | None = None
    is_trusted: bool
    first_seen_at: str
    last_seen_at: str


class SessionResponse(BaseModel):
    """Session response."""

    id: UUID
    device_type: str | None = None
    ip_address: str | None = None
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

    consents: dict[str, Any]


# =============================================================================
# Helper to get current portal user
# =============================================================================


async def get_portal_user(
    authorization: str = Header(..., description="Bearer token"),
    db: AsyncSession = Depends(get_db),
):
    """Validate portal session and return user.

    Rejects users whose ``registration_status`` is not ACTIVE — this
    keeps a borrower stuck at PENDING_APPROVAL (or rejected) from
    using any portal surface, even with a leftover session token from
    a previously-active state. The OTP/login plumbing remains
    available so they can still log in *if* an admin re-activates them.
    """
    if not authorization.startswith("Bearer "):
        raise UnauthorizedException(
            detail="Invalid authorization header",
            error_code="INVALID_AUTHORIZATION_HEADER",
        )

    token = authorization[7:]
    await clear_tenant_context(db)
    service = PortalAuthService(db)
    user = await service.validate_session(token)

    if not user:
        raise UnauthorizedException(
            detail="Invalid or expired session",
            error_code="INVALID_OR_EXPIRED_SESSION",
        )

    # CLAUDE.md §1 / §3.4 — block any non-ACTIVE registration from
    # transacting. We raise 403 with a typed error_code so the FE can
    # route to the "your registration is pending approval" screen.
    from app.models.portal.enums import (
        PortalRegistrationStatus as _PortalRegistrationStatus,
    )

    if user.registration_status != _PortalRegistrationStatus.ACTIVE:
        raise _ForbiddenException(
            detail=("Portal user is not active. Registration must be " "approved by the lender."),
            error_code="PORTAL_USER_NOT_ACTIVE",
        )

    return user


async def get_portal_db_with_tenant(
    db: AsyncSession = Depends(get_db),
    user: PortalUser = Depends(get_portal_user),
) -> AsyncSession:
    """Return a DB session scoped to the authenticated portal user's tenant."""

    await set_tenant_context(db, user.organization_id)
    return db


async def _resolve_portal_organization_id(
    db: AsyncSession,
    mobile: str,
    explicit_org_id: UUID | None,
) -> UUID:
    """Resolve the scheme portal's organization for login-related OTP flows."""

    if explicit_org_id is not None:
        return explicit_org_id

    configured = getattr(settings, "PORTAL_DEFAULT_ORGANIZATION_ID", None)
    if configured:
        row = (
            await db.execute(
                select(Organization.id).where(
                    Organization.id == configured,
                    Organization.deleted_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        if row is not None:
            return row

    mobile_matches = list(
        (
            await db.execute(
                select(PortalUser.organization_id)
                .where(
                    PortalUser.mobile == mobile,
                    PortalUser.deleted_at.is_(None),
                )
                .distinct()
            )
        )
        .scalars()
        .all()
    )
    if len(mobile_matches) == 1:
        return mobile_matches[0]

    active_orgs = list(
        (await db.execute(select(Organization.id).where(Organization.deleted_at.is_(None))))
        .scalars()
        .all()
    )
    if len(active_orgs) == 1:
        return active_orgs[0]

    raise BadRequestException(
        detail="Unable to resolve scheme organization for login. "
            "Provide organization_id or configure PORTAL_DEFAULT_ORGANIZATION_ID.",
        error_code="UNABLE_TO_RESOLVE_SCHEME_ORGANIZATION_FOR",
    )


async def _resolve_portal_organization_id_for_email(
    db: AsyncSession,
    email: str,
    explicit_org_id: UUID | None,
) -> UUID:
    """Resolve the scheme portal's organization for internal actor login flows."""

    if explicit_org_id is not None:
        return explicit_org_id

    configured = getattr(settings, "PORTAL_DEFAULT_ORGANIZATION_ID", None)
    if configured:
        row = (
            await db.execute(
                select(Organization.id).where(
                    Organization.id == configured,
                    Organization.deleted_at.is_(None),
                )
            )
        ).scalar_one_or_none()
        if row is not None:
            return row

    email_matches = list(
        (
            await db.execute(
                select(PortalUser.organization_id)
                .where(
                    func.lower(PortalUser.email) == email.strip().lower(),
                    PortalUser.deleted_at.is_(None),
                )
                .distinct()
            )
        )
        .scalars()
        .all()
    )
    if len(email_matches) == 1:
        return email_matches[0]

    active_orgs = list(
        (await db.execute(select(Organization.id).where(Organization.deleted_at.is_(None))))
        .scalars()
        .all()
    )
    if len(active_orgs) == 1:
        return active_orgs[0]

    raise BadRequestException(
        detail="Unable to resolve scheme organization for this email. "
            "Provide organization_id or configure PORTAL_DEFAULT_ORGANIZATION_ID.",
        error_code="UNABLE_TO_RESOLVE_SCHEME_ORGANIZATION_FOR",
    )


# =============================================================================
# OTP Endpoints
# =============================================================================


@router.post(
    "/send-otp",
    response_model=SendOTPResponse, response_model_by_alias=True,
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
    org_id = await _resolve_portal_organization_id(
        db,
        mobile=data.mobile,
        explicit_org_id=data.organization_id,
    )
    result = await service.send_otp(
        organization_id=org_id,
        mobile=data.mobile,
        purpose=data.purpose,
    )
    await db.commit()

    if not result.get("success"):
        error_code = result.get("error_code")
        if error_code == "OTP_RATE_LIMITED":
            status_code = status.HTTP_429_TOO_MANY_REQUESTS
        elif error_code == "OTP_DELIVERY_DISABLED":
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        else:
            status_code = status.HTTP_502_BAD_GATEWAY
        raise AppException(
            status_code=status_code,
            detail=result.get("error"),
            error_code="UPSTREAM_ERROR",
        )

    return SendOTPResponse(
        success=True,
        message="OTP sent successfully",
        otp_id=result.get("otp_id"),
        expires_in_seconds=result.get("expires_in_seconds", 600),
    )


@router.post(
    "/verify-otp",
    response_model=LoginResponse, response_model_by_alias=True,
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
    org_id = await _resolve_portal_organization_id(
        db,
        mobile=data.mobile,
        explicit_org_id=data.organization_id,
    )

    # Verify OTP
    is_valid, error = await service.verify_otp(
        organization_id=org_id,
        mobile=data.mobile,
        otp_code=data.otp,
        purpose=data.purpose,
    )

    if not is_valid:
        raise UnauthorizedException(detail=error or "OTP verification failed", error_code="UNAUTHORIZED")

    # Create session
    login_result = await service.login(
        organization_id=org_id,
        mobile=data.mobile,
        device_info=data.device_info,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()

    if not login_result.get("success"):
        raise UnauthorizedException(detail=login_result.get("error"), error_code="UNAUTHORIZED")

    return LoginResponse(**login_result)


@router.post(
    "/login/password",
    response_model=LoginResponse, response_model_by_alias=True,
    summary="Login internal scheme actor with email and password",
)
@portal_login_limit()
async def login_with_password(
    request: Request,
    data: PasswordLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate an invited lender, SMFCL, ministry, or admin actor."""
    service = PortalAuthService(db)
    org_id = await _resolve_portal_organization_id_for_email(
        db,
        email=data.email,
        explicit_org_id=data.organization_id,
    )
    login_result = await service.login_with_password(
        organization_id=org_id,
        email=data.email,
        password=data.password,
        otp=data.otp,
        device_info=data.device_info,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()

    if not login_result.get("success") and not login_result.get("requires_mfa"):
        raise UnauthorizedException(detail=login_result.get("error"), error_code="UNAUTHORIZED")

    return LoginResponse(**login_result)


@router.post(
    "/activate-invite",
    response_model=LoginResponse, response_model_by_alias=True,
    summary="Activate an invited internal scheme actor account",
)
@portal_generic_limit()
async def activate_invite(
    request: Request,
    data: ActivateInviteRequest,
    db: AsyncSession = Depends(get_db),
):
    service = PortalAuthService(db)
    try:
        result = await service.activate_invitation(
            token=data.token,
            password=data.password,
            device_info=data.device_info,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    except ValueError as exc:
        raise BadRequestException(detail=str(exc), error_code="BAD_REQUEST") from exc

    await db.commit()
    return LoginResponse(**result)


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse, response_model_by_alias=True,
    summary="Request a password-reset link for an internal scheme actor",
)
@portal_generic_limit()
async def forgot_password(
    request: Request,
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    service = PortalAuthService(db)
    org_id = await _resolve_portal_organization_id_for_email(
        db,
        email=data.email,
        explicit_org_id=data.organization_id,
    )
    try:
        result = await service.create_password_reset(org_id, data.email)
    except ValueError as exc:
        raise ServiceUnavailableException(detail=str(exc), error_code="SERVICE_UNAVAILABLE") from exc
    await db.commit()

    if result is None:
        return ForgotPasswordResponse(
            success=True,
            message="If the email exists, password reset instructions have been prepared",
        )

    return ForgotPasswordResponse(
        success=True,
        message="Password reset instructions have been prepared",
        reset_token=result["reset_token"],
        reset_url=result["reset_url"],
        expires_at=result["expires_at"].isoformat(),
    )


@router.post(
    "/reset-password",
    response_model=ForgotPasswordResponse, response_model_by_alias=True,
    summary="Reset password using a scheme-portal reset link",
)
@portal_generic_limit()
async def reset_password(
    request: Request,
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    service = PortalAuthService(db)
    try:
        await service.reset_password(data.token, data.new_password)
    except ValueError as exc:
        raise BadRequestException(detail=str(exc), error_code="BAD_REQUEST") from exc

    await db.commit()
    return ForgotPasswordResponse(
        success=True,
        message="Password reset successfully",
    )


# =============================================================================
# Session Management
# =============================================================================


@router.post(
    "/refresh",
    response_model=LoginResponse, response_model_by_alias=True,
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
        raise UnauthorizedException(
            detail="Invalid or expired refresh token",
            error_code="INVALID_OR_EXPIRED_REFRESH_TOKEN",
        )

    return LoginResponse(
        success=True,
        access_token=result.get("access_token") or result.get("session_token"),
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
        raise UnauthorizedException(
            detail="Invalid authorization header",
            error_code="INVALID_AUTHORIZATION_HEADER",
        )

    token = authorization[7:]
    service = PortalAuthService(db)
    await service.logout(token)
    await db.commit()

    return {"message": "Logged out successfully"}


@router.get(
    "/me",
    summary="Get current authenticated scheme-portal user",
)
async def me(
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    service = PortalAuthService(db)
    return await service._serialize_user(user)


@router.get(
    "/sessions",
    response_model=list[SessionResponse], response_model_by_alias=True,
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
    count = await service.invalidate_all_sessions(user.id, except_session_token=current_token)
    await db.commit()

    return {"message": f"Logged out from {count} sessions"}


@router.post(
    "/mfa/setup",
    response_model=MfaSetupResponse, response_model_by_alias=True,
    summary="Generate the TOTP secret for the current scheme-portal user",
)
async def setup_mfa(
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    service = PortalAuthService(db)
    try:
        result = await service.begin_mfa_setup(user.id)
    except ValueError as exc:
        raise BadRequestException(detail=str(exc), error_code="BAD_REQUEST") from exc

    await db.commit()
    return MfaSetupResponse(**result)


@router.post(
    "/mfa/verify",
    summary="Verify a TOTP code and enable MFA for the current scheme-portal user",
)
async def verify_mfa(
    data: MfaVerifyRequest,
    user=Depends(get_portal_user),
    db: AsyncSession = Depends(get_db),
):
    service = PortalAuthService(db)
    try:
        result = await service.verify_and_enable_mfa(user.id, data.otp)
    except ValueError as exc:
        raise BadRequestException(detail=str(exc), error_code="BAD_REQUEST") from exc

    await db.commit()
    return result


# =============================================================================
# Device Management
# =============================================================================


@router.get(
    "/devices",
    response_model=list[DeviceResponse], response_model_by_alias=True,
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
        raise NotFoundException(detail="Device not found", error_code="DEVICE_NOT_FOUND")

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
        raise NotFoundException(detail="Device not found", error_code="DEVICE_NOT_FOUND")

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
    response_model=ConsentResponse, response_model_by_alias=True,
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
