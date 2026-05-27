"""Portal Authentication Service.

Handles OTP-based authentication, session management, and device registration.
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.security import (
    generate_mfa_secret,
    get_mfa_provisioning_uri,
    get_password_hash,
    verify_mfa_code,
    verify_password,
)
from app.models.lending.entity import Entity
from app.models.portal.enums import (
    ConsentType,
    DeviceType,
    OTPPurpose,
    PortalActorRole,
    PortalRegistrationStatus,
    PortalUserStatus,
)
from app.models.portal.portal_user import (
    PortalConsent,
    PortalDevice,
    PortalOTP,
    PortalSession,
    PortalUser,
)
from app.models.portal.portal_user_entity import PortalUserEntity
from app.services.notification.communication_service import (
    Channel,
    DispatchStatus,
    Recipient,
    communication_service,
)


class PortalAuthService:
    """Portal authentication service."""

    OTP_LENGTH = 6
    OTP_EXPIRY_MINUTES = 10
    MAX_OTP_ATTEMPTS = 3
    SESSION_EXPIRY_HOURS = 24
    REFRESH_TOKEN_EXPIRY_DAYS = 30
    MAX_FAILED_LOGINS = 5
    LOCKOUT_MINUTES = 30
    INVITE_EXPIRY_HOURS = 72
    RESET_EXPIRY_HOURS = 2

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # OTP Management
    # =========================================================================

    async def send_otp(
        self,
        organization_id: UUID,
        mobile: str,
        purpose: OTPPurpose,
        reference_type: str | None = None,
        reference_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Generate and send OTP to mobile."""
        # Check rate limiting
        recent_otps = await self._get_recent_otps(organization_id, mobile)
        if len(recent_otps) >= 5:  # Max 5 OTPs in 15 minutes
            return {
                "success": False,
                "error": "Too many OTP requests. Please try after sometime.",
                "error_code": "OTP_RATE_LIMITED",
            }

        # Generate OTP
        otp_code = self._generate_otp()
        otp_hash = self._hash_otp(otp_code)

        # Create OTP record
        otp = PortalOTP(
            organization_id=organization_id,
            mobile=mobile,
            otp_code=otp_code,  # Stored for debugging; should be removed in production
            otp_hash=otp_hash,
            purpose=purpose,
            reference_type=reference_type,
            reference_id=reference_id,
            expires_at=datetime.utcnow() + timedelta(minutes=self.OTP_EXPIRY_MINUTES),
            sent_via="SMS",
        )
        self.db.add(otp)
        await self.db.flush()

        dispatch = await communication_service.send(
            channel=Channel.SMS,
            recipient=Recipient(phone=mobile),
            template_code=f"PORTAL_OTP_{purpose.value}",
            context={
                "message": self._build_otp_message(otp_code, purpose),
                "otp": otp_code,
                "purpose": purpose.value,
            },
        )
        otp.delivery_status = dispatch.status.value.upper()
        otp.delivery_vendor_ref = dispatch.provider_message_id
        if dispatch.status in {DispatchStatus.FAILED, DispatchStatus.DISABLED}:
            return {
                "success": False,
                "error": self._otp_delivery_error(dispatch.status),
                "error_code": (
                    "OTP_DELIVERY_DISABLED"
                    if dispatch.status == DispatchStatus.DISABLED
                    else "OTP_DELIVERY_FAILED"
                ),
            }

        return {
            "success": True,
            "message": "OTP sent successfully",
            "otp_id": otp.id,
            "expires_in_seconds": self.OTP_EXPIRY_MINUTES * 60,
            "delivery_status": dispatch.status.value,
        }

    async def verify_otp(
        self,
        organization_id: UUID,
        mobile: str,
        otp_code: str,
        purpose: OTPPurpose,
    ) -> tuple[bool, str | None]:
        """Verify OTP."""
        # Get latest OTP for this mobile and purpose
        stmt = (
            select(PortalOTP)
            .where(
                and_(
                    PortalOTP.organization_id == organization_id,
                    PortalOTP.mobile == mobile,
                    PortalOTP.purpose == purpose,
                    PortalOTP.is_used.is_(False),
                    PortalOTP.expires_at > datetime.utcnow(),
                )
            )
            .order_by(PortalOTP.generated_at.desc())
            .limit(1)
        )
        result = await self.db.execute(stmt)
        otp = result.scalar_one_or_none()

        if not otp:
            return False, "OTP expired or not found"

        # Check attempts
        if otp.attempts >= otp.max_attempts:
            return False, "Maximum attempts exceeded"

        # Verify OTP
        otp.attempts += 1
        if self._hash_otp(otp_code) != otp.otp_hash:
            return False, "Invalid OTP"

        # Mark OTP as used
        otp.is_used = True
        otp.verified_at = datetime.utcnow()

        return True, None

    # =========================================================================
    # User Registration & Login
    # =========================================================================

    async def register_user(
        self,
        organization_id: UUID,
        customer_id: UUID,
        mobile: str,
        email: str | None = None,
        preferred_language: str = "en",
    ) -> PortalUser:
        """Register a new portal user."""
        # Check if user already exists
        existing = await self.get_user_by_mobile(organization_id, mobile)
        if existing:
            raise ValueError("User already registered with this mobile number")

        user = PortalUser(
            organization_id=organization_id,
            customer_id=customer_id,
            mobile=mobile,
            mobile_verified=True,
            mobile_verified_at=datetime.utcnow(),
            email=email,
            preferred_language=preferred_language,
            status=PortalUserStatus.ACTIVE,
            actor_role=PortalActorRole.SCHEME_BORROWER,
        )
        self.db.add(user)
        return user

    async def login(
        self,
        organization_id: UUID,
        mobile: str,
        device_info: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict[str, Any]:
        """Login user and create session."""
        user = await self.get_user_by_mobile(organization_id, mobile)
        if not user:
            return {"success": False, "error": "User not found"}

        # Check user status
        if user.status != PortalUserStatus.ACTIVE:
            return {"success": False, "error": f"Account is {user.status.value}"}

        # Check lockout
        if user.locked_until and user.locked_until > datetime.utcnow():
            return {"success": False, "error": "Account is temporarily locked"}

        # Reset failed attempts on successful login
        user.failed_login_attempts = 0
        user.locked_until = None

        # Update login info
        user.last_login_at = datetime.utcnow()
        user.last_login_ip = ip_address
        user.login_count += 1

        # Register/update device
        device = None
        if device_info:
            device = await self._register_or_update_device(user.id, device_info, ip_address)
            user.last_login_device = device_info.get("device_type")

        # Create session
        session = await self._create_session(
            user.id,
            device_id=device.id if device else None,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return {
            "success": True,
            "user": await self._serialize_user(user),
            "access_token": session.session_token,
            "session_token": session.session_token,
            "refresh_token": session.refresh_token,
            "expires_at": session.expires_at.isoformat(),
            "requires_mfa": False,
        }

    async def login_with_password(
        self,
        organization_id: UUID,
        email: str,
        password: str,
        otp: str | None = None,
        device_info: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict[str, Any]:
        """Login an invited internal portal actor with email and password."""
        user = await self.get_user_by_email(organization_id, email)
        if not user or not user.password_hash:
            return {"success": False, "error": "Invalid email or password"}

        if user.status != PortalUserStatus.ACTIVE:
            return {"success": False, "error": f"Account is {user.status.value}"}

        if user.registration_status != PortalRegistrationStatus.ACTIVE:
            return {
                "success": False,
                "error": "Portal access is not active for this user",
            }

        if user.locked_until and user.locked_until > datetime.utcnow():
            return {"success": False, "error": "Account is temporarily locked"}

        if not verify_password(password, user.password_hash):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= self.MAX_FAILED_LOGINS:
                user.locked_until = datetime.utcnow() + timedelta(minutes=self.LOCKOUT_MINUTES)
            return {"success": False, "error": "Invalid email or password"}

        if user.is_2fa_enabled:
            if not user.mfa_secret:
                return {
                    "success": False,
                    "error": "MFA is enabled but not configured for this account",
                }
            if not otp:
                return {
                    "success": True,
                    "requires_mfa": True,
                    "message": "MFA verification required",
                }
            if not verify_mfa_code(user.mfa_secret, otp):
                return {"success": False, "error": "Invalid OTP code"}

        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.utcnow()
        user.last_login_ip = ip_address
        user.login_count += 1

        device = None
        if device_info:
            device = await self._register_or_update_device(user.id, device_info, ip_address)
            user.last_login_device = device_info.get("device_type")

        session = await self._create_session(
            user.id,
            device_id=device.id if device else None,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return {
            "success": True,
            "user": await self._serialize_user(user),
            "access_token": session.session_token,
            "session_token": session.session_token,
            "refresh_token": session.refresh_token,
            "expires_at": session.expires_at.isoformat(),
            "requires_mfa": False,
        }

    async def issue_activation_invite(
        self,
        user: PortalUser,
        invited_by: UUID,
    ) -> dict[str, Any]:
        """Create or rotate an activation invite for an internal scheme actor."""
        actor_role = (
            user.actor_role.value if hasattr(user.actor_role, "value") else str(user.actor_role)
        )
        if actor_role == PortalActorRole.SCHEME_BORROWER.value:
            raise ValueError("Borrower portal users are not activated by invite")
        if not user.email:
            raise ValueError("An email address is required before issuing an invite")

        token = self._generate_token()
        user.invited_at = datetime.utcnow()
        user.invited_by = invited_by
        user.invite_token_hash = self._hash_token(token)
        user.invite_token_expires_at = datetime.utcnow() + timedelta(hours=self.INVITE_EXPIRY_HOURS)
        activation_url = self._build_portal_url("/portal/activate", token)
        await self._send_internal_actor_email(
            user=user,
            template_code="PORTAL_ACTIVATION_INVITE",
            subject="Activate your SFC portal account",
            html_body=(
                "<html><body>"
                "<p>Your SFC portal account for role "
                f"<strong>{user.actor_role}</strong> is ready.</p>"
                f'<p><a href="{activation_url}">Activate account</a></p>'
                f"<p>This link expires at {user.invite_token_expires_at.isoformat()}.</p>"
                "</body></html>"
            ),
            message=("Your SFC portal account is ready. " f"Activate it here: {activation_url}"),
        )

        return {
            "portal_user_id": str(user.id),
            "email": user.email,
            "invite_expires_at": user.invite_token_expires_at,
            "activation_token": token,
            "activation_url": activation_url,
        }

    async def activate_invitation(
        self,
        token: str,
        password: str,
        device_info: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> dict[str, Any]:
        """Activate an invited internal portal actor and create a session."""
        user = await self._get_user_by_invite_token(token)
        if not user:
            raise ValueError("Invalid or expired activation link")

        self._validate_password(password)

        now = datetime.utcnow()
        user.password_hash = get_password_hash(password)
        user.password_changed_at = now
        user.activated_at = now
        user.email_verified = True
        user.email_verified_at = now
        user.failed_login_attempts = 0
        user.locked_until = None
        user.invite_token_hash = None
        user.invite_token_expires_at = None
        user.last_login_at = now
        user.last_login_ip = ip_address
        user.login_count += 1

        device = None
        if device_info:
            device = await self._register_or_update_device(user.id, device_info, ip_address)
            user.last_login_device = device_info.get("device_type")

        session = await self._create_session(
            user.id,
            device_id=device.id if device else None,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        return {
            "success": True,
            "user": await self._serialize_user(user),
            "access_token": session.session_token,
            "session_token": session.session_token,
            "refresh_token": session.refresh_token,
            "expires_at": session.expires_at.isoformat(),
            "requires_mfa": False,
        }

    async def create_password_reset(
        self,
        organization_id: UUID,
        email: str,
    ) -> dict[str, Any] | None:
        """Create a password-reset token for an internal portal actor."""
        user = await self.get_user_by_email(organization_id, email)
        if (
            not user
            or not user.email
            or not user.password_hash
            or user.status != PortalUserStatus.ACTIVE
        ):
            return None

        token = self._generate_token()
        user.reset_token_hash = self._hash_token(token)
        user.reset_token_expires_at = datetime.utcnow() + timedelta(hours=self.RESET_EXPIRY_HOURS)
        reset_url = self._build_portal_url("/portal/reset-password", token)
        await self._send_internal_actor_email(
            user=user,
            template_code="PORTAL_PASSWORD_RESET",
            subject="Reset your SFC portal password",
            html_body=(
                "<html><body>"
                "<p>A password reset was requested for your SFC portal account.</p>"
                f'<p><a href="{reset_url}">Reset password</a></p>'
                f"<p>This link expires at {user.reset_token_expires_at.isoformat()}.</p>"
                "</body></html>"
            ),
            message=(
                "A password reset was requested for your SFC portal account. "
                f"Reset it here: {reset_url}"
            ),
        )
        return {
            "email": user.email,
            "reset_token": token,
            "reset_url": reset_url,
            "expires_at": user.reset_token_expires_at,
        }

    async def reset_password(
        self,
        token: str,
        new_password: str,
    ) -> None:
        """Reset a portal user's password using the reset token."""
        user = await self._get_user_by_reset_token(token)
        if not user:
            raise ValueError("Invalid or expired reset link")

        self._validate_password(new_password)

        user.password_hash = get_password_hash(new_password)
        user.password_changed_at = datetime.utcnow()
        user.failed_login_attempts = 0
        user.locked_until = None
        user.reset_token_hash = None
        user.reset_token_expires_at = None

        await self.invalidate_all_sessions(user.id)

    async def begin_mfa_setup(self, user_id: UUID) -> dict[str, Any]:
        """Generate or reuse a TOTP secret for an internal portal user."""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ValueError("Portal user not found")
        if not user.email:
            raise ValueError("Email address is required before setting up MFA")

        if not user.mfa_secret:
            user.mfa_secret = generate_mfa_secret()

        return {
            "secret": user.mfa_secret,
            "provisioning_uri": get_mfa_provisioning_uri(user.mfa_secret, user.email),
            "is_enabled": user.is_2fa_enabled,
        }

    async def verify_and_enable_mfa(self, user_id: UUID, otp: str) -> dict[str, Any]:
        """Validate the provided TOTP code and enable MFA for the user."""
        user = await self.get_user_by_id(user_id)
        if not user or not user.mfa_secret:
            raise ValueError("MFA is not configured for this account")
        if not verify_mfa_code(user.mfa_secret, otp):
            raise ValueError("Invalid OTP code")
        user.is_2fa_enabled = True
        return {"is_enabled": True}

    async def logout(
        self,
        session_token: str,
        logout_reason: str = "USER_INITIATED",
    ) -> bool:
        """Logout user and invalidate session."""
        stmt = select(PortalSession).where(PortalSession.session_token == session_token)
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if session:
            session.is_active = False
            session.logout_at = datetime.utcnow()
            session.logout_reason = logout_reason
            return True
        return False

    async def refresh_session(
        self,
        refresh_token: str,
    ) -> dict[str, Any] | None:
        """Refresh session using refresh token."""
        stmt = select(PortalSession).where(
            and_(
                PortalSession.refresh_token == refresh_token,
                PortalSession.is_active.is_(True),
            )
        )
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            return None

        # Generate new tokens
        session.session_token = self._generate_token()
        session.refresh_token = self._generate_token()
        session.expires_at = datetime.utcnow() + timedelta(hours=self.SESSION_EXPIRY_HOURS)
        session.last_activity_at = datetime.utcnow()

        return {
            "access_token": session.session_token,
            "session_token": session.session_token,
            "refresh_token": session.refresh_token,
            "expires_at": session.expires_at.isoformat(),
        }

    # =========================================================================
    # Session Validation
    # =========================================================================

    async def validate_session(
        self,
        session_token: str,
    ) -> PortalUser | None:
        """Validate session and return user."""
        stmt = (
            select(PortalSession)
            .options(selectinload(PortalSession.user))
            .where(
                and_(
                    PortalSession.session_token == session_token,
                    PortalSession.is_active.is_(True),
                    PortalSession.expires_at > datetime.utcnow(),
                )
            )
        )
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if session:
            session.last_activity_at = datetime.utcnow()
            return session.user
        return None

    async def get_active_sessions(
        self,
        user_id: UUID,
    ) -> list:
        """Get all active sessions for a user."""
        stmt = select(PortalSession).where(
            and_(
                PortalSession.user_id == user_id,
                PortalSession.is_active.is_(True),
                PortalSession.expires_at > datetime.utcnow(),
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def invalidate_all_sessions(
        self,
        user_id: UUID,
        except_session_token: str | None = None,
    ) -> int:
        """Invalidate all sessions for a user."""
        stmt = select(PortalSession).where(
            and_(
                PortalSession.user_id == user_id,
                PortalSession.is_active.is_(True),
            )
        )
        if except_session_token:
            stmt = stmt.where(PortalSession.session_token != except_session_token)

        result = await self.db.execute(stmt)
        sessions = list(result.scalars().all())

        count = 0
        for session in sessions:
            session.is_active = False
            session.logout_at = datetime.utcnow()
            session.logout_reason = "FORCED_LOGOUT"
            count += 1

        return count

    # =========================================================================
    # Device Management
    # =========================================================================

    async def get_user_devices(
        self,
        user_id: UUID,
    ) -> list:
        """Get all devices for a user."""
        stmt = (
            select(PortalDevice)
            .where(
                and_(
                    PortalDevice.user_id == user_id,
                    PortalDevice.is_active.is_(True),
                )
            )
            .order_by(PortalDevice.last_seen_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def trust_device(
        self,
        device_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Mark a device as trusted."""
        stmt = select(PortalDevice).where(
            and_(
                PortalDevice.id == device_id,
                PortalDevice.user_id == user_id,
            )
        )
        result = await self.db.execute(stmt)
        device = result.scalar_one_or_none()

        if device:
            device.is_trusted = True
            device.trusted_at = datetime.utcnow()
            return True
        return False

    async def block_device(
        self,
        device_id: UUID,
        user_id: UUID,
        reason: str,
    ) -> bool:
        """Block a device."""
        stmt = select(PortalDevice).where(
            and_(
                PortalDevice.id == device_id,
                PortalDevice.user_id == user_id,
            )
        )
        result = await self.db.execute(stmt)
        device = result.scalar_one_or_none()

        if device:
            device.is_active = False
            device.blocked_at = datetime.utcnow()
            device.block_reason = reason
            return True
        return False

    # =========================================================================
    # Consent Management
    # =========================================================================

    async def record_consent(
        self,
        user_id: UUID,
        consent_type: ConsentType,
        consent_version: str,
        is_granted: bool,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> PortalConsent:
        """Record customer consent."""
        consent = PortalConsent(
            user_id=user_id,
            consent_type=consent_type,
            consent_version=consent_version,
            is_granted=is_granted,
            granted_at=datetime.utcnow() if is_granted else None,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(consent)
        return consent

    async def get_user_consents(
        self,
        user_id: UUID,
    ) -> dict[str, Any]:
        """Get all consents for a user."""
        stmt = (
            select(PortalConsent)
            .where(PortalConsent.user_id == user_id)
            .order_by(PortalConsent.consent_type, PortalConsent.created_at.desc())
        )
        result = await self.db.execute(stmt)
        consents = list(result.scalars().all())

        # Group by type, take latest
        consent_map = {}
        for consent in consents:
            if consent.consent_type not in consent_map:
                consent_map[consent.consent_type.value] = {
                    "is_granted": consent.is_granted,
                    "version": consent.consent_version,
                    "granted_at": consent.granted_at.isoformat() if consent.granted_at else None,
                }

        return consent_map

    # =========================================================================
    # User Lookup
    # =========================================================================

    async def get_user_by_mobile(
        self,
        organization_id: UUID,
        mobile: str,
    ) -> PortalUser | None:
        """Get user by mobile number."""
        stmt = select(PortalUser).where(
            and_(
                PortalUser.organization_id == organization_id,
                PortalUser.mobile == mobile,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_email(
        self,
        organization_id: UUID,
        email: str,
    ) -> PortalUser | None:
        """Get user by email address, case-insensitively."""
        stmt = select(PortalUser).where(
            and_(
                PortalUser.organization_id == organization_id,
                func.lower(PortalUser.email) == email.strip().lower(),
                PortalUser.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_id(
        self,
        user_id: UUID,
    ) -> PortalUser | None:
        """Get user by ID."""
        stmt = select(PortalUser).where(PortalUser.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # =========================================================================
    # Private Methods
    # =========================================================================

    def _generate_otp(self) -> str:
        """Generate random OTP."""
        return "".join([str(secrets.randbelow(10)) for _ in range(self.OTP_LENGTH)])

    def _build_otp_message(self, otp_code: str, purpose: OTPPurpose) -> str:
        purpose_label = purpose.value.replace("_", " ").title()
        return (
            f"Your SFC portal {purpose_label} OTP is {otp_code}. "
            f"It is valid for {self.OTP_EXPIRY_MINUTES} minutes. Do not share it."
        )

    def _otp_delivery_error(self, status: DispatchStatus) -> str:
        if status == DispatchStatus.DISABLED:
            return "OTP delivery is not configured for this environment"
        return "OTP delivery failed. Please try again."

    def _hash_otp(self, otp: str) -> str:
        """Hash OTP for secure storage."""
        return hashlib.sha256(otp.encode()).hexdigest()

    def _generate_token(self) -> str:
        """Generate secure session token."""
        return secrets.token_urlsafe(32)

    def _hash_token(self, token: str) -> str:
        """Hash a non-OTP token for storage."""
        return hashlib.sha256(token.encode()).hexdigest()

    def _build_portal_url(self, path: str, token: str) -> str:
        """Build a frontend activation/reset URL for demo flows."""
        base_url = getattr(settings, "FRONTEND_BASE_URL", None)
        if base_url:
            return f"{base_url.rstrip('/')}{path}?token={token}"
        return f"{path}?token={token}"

    async def _send_internal_actor_email(
        self,
        *,
        user: PortalUser,
        template_code: str,
        subject: str,
        html_body: str,
        message: str,
    ) -> None:
        dispatch = await communication_service.send(
            channel=Channel.EMAIL,
            recipient=Recipient(
                user_id=str(user.id),
                email=user.email,
            ),
            template_code=template_code,
            context={
                "subject": subject,
                "html_body": html_body,
                "message": message,
            },
        )
        if dispatch.status in {DispatchStatus.FAILED, DispatchStatus.DISABLED}:
            raise ValueError(
                "Email delivery is not available for internal scheme actor communication"
            )

    def _validate_password(self, password: str) -> None:
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            raise ValueError(
                f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long"
            )

    async def _get_user_by_invite_token(self, token: str) -> PortalUser | None:
        stmt = select(PortalUser).where(
            and_(
                PortalUser.invite_token_hash == self._hash_token(token),
                PortalUser.invite_token_expires_at.is_not(None),
                PortalUser.invite_token_expires_at > datetime.utcnow(),
                PortalUser.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_user_by_reset_token(self, token: str) -> PortalUser | None:
        stmt = select(PortalUser).where(
            and_(
                PortalUser.reset_token_hash == self._hash_token(token),
                PortalUser.reset_token_expires_at.is_not(None),
                PortalUser.reset_token_expires_at > datetime.utcnow(),
                PortalUser.deleted_at.is_(None),
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def _get_recent_otps(
        self,
        organization_id: UUID,
        mobile: str,
        minutes: int = 15,
    ) -> list:
        """Get recent OTPs for rate limiting."""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        stmt = select(PortalOTP).where(
            and_(
                PortalOTP.organization_id == organization_id,
                PortalOTP.mobile == mobile,
                PortalOTP.generated_at > cutoff,
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def _create_session(
        self,
        user_id: UUID,
        device_id: UUID | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> PortalSession:
        """Create a new session."""
        session = PortalSession(
            user_id=user_id,
            session_token=self._generate_token(),
            refresh_token=self._generate_token(),
            device_id=device_id,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.utcnow() + timedelta(hours=self.SESSION_EXPIRY_HOURS),
        )
        self.db.add(session)
        return session

    async def _register_or_update_device(
        self,
        user_id: UUID,
        device_info: dict[str, Any],
        ip_address: str | None = None,
    ) -> PortalDevice:
        """Register new device or update existing."""
        device_id = device_info.get("device_id")

        if device_id:
            stmt = select(PortalDevice).where(
                and_(
                    PortalDevice.user_id == user_id,
                    PortalDevice.device_id == device_id,
                )
            )
            result = await self.db.execute(stmt)
            device = result.scalar_one_or_none()

            if device:
                device.last_seen_at = datetime.utcnow()
                device.login_count += 1
                device.app_version = device_info.get("app_version")
                device.fcm_token = device_info.get("fcm_token")
                return device

        # Create new device
        device = PortalDevice(
            user_id=user_id,
            device_id=device_id or secrets.token_urlsafe(16),
            device_type=DeviceType(device_info.get("device_type", "WEB")),
            device_name=device_info.get("device_name"),
            device_model=device_info.get("device_model"),
            os_version=device_info.get("os_version"),
            app_version=device_info.get("app_version"),
            fcm_token=device_info.get("fcm_token"),
            apns_token=device_info.get("apns_token"),
        )
        self.db.add(device)
        return device

    async def _serialize_user(self, user: PortalUser) -> dict[str, Any]:
        """Return the SFC portal user payload for frontend session storage."""

        links_stmt = (
            select(PortalUserEntity, Entity)
            .join(Entity, Entity.id == PortalUserEntity.entity_id)
            .where(
                PortalUserEntity.portal_user_id == user.id,
                PortalUserEntity.is_link_active.is_(True),
                PortalUserEntity.deleted_at.is_(None),
                Entity.deleted_at.is_(None),
            )
            .order_by(Entity.legal_name.asc())
        )
        rows = (await self.db.execute(links_stmt)).all()
        linked_entities = [
            {
                "id": str(entity.id),
                "legal_name": entity.legal_name,
            }
            for _, entity in rows
        ]

        display_name = user.registration_authorized_signatory_name or user.email or user.mobile

        return {
            "id": str(user.id),
            "mobile": user.mobile,
            "email": user.email,
            "preferred_language": user.preferred_language,
            "display_name": display_name,
            "full_name": display_name,
            "organization_id": str(user.organization_id),
            "registration_status": user.registration_status.value,
            "actor_role": (
                user.actor_role.value
                if hasattr(user.actor_role, "value")
                else str(user.actor_role or PortalActorRole.SCHEME_BORROWER.value)
            ),
            "is_2fa_enabled": user.is_2fa_enabled,
            "password_login_enabled": bool(user.password_hash),
            "invite_pending": bool(user.invite_token_hash and user.invite_token_expires_at),
            "activated_at": (user.activated_at.isoformat() if user.activated_at else None),
            "linked_entities": linked_entities,
        }
