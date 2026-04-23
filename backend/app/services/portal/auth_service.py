"""Portal Authentication Service.

Handles OTP-based authentication, session management, and device registration.
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from uuid import UUID

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.portal.portal_user import (
    PortalUser,
    PortalSession,
    PortalDevice,
    PortalOTP,
    PortalConsent,
)
from app.models.portal.enums import (
    PortalUserStatus,
    DeviceType,
    OTPPurpose,
    ConsentType,
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
        reference_type: Optional[str] = None,
        reference_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """Generate and send OTP to mobile."""
        # Check rate limiting
        recent_otps = await self._get_recent_otps(organization_id, mobile)
        if len(recent_otps) >= 5:  # Max 5 OTPs in 15 minutes
            return {
                "success": False,
                "error": "Too many OTP requests. Please try after sometime.",
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

        # TODO: Integrate SMS gateway to send OTP
        # sms_result = await self._send_sms(mobile, f"Your OTP is {otp_code}")

        return {
            "success": True,
            "message": "OTP sent successfully",
            "otp_id": otp.id,
            "expires_in_seconds": self.OTP_EXPIRY_MINUTES * 60,
            # Remove in production:
            "debug_otp": otp_code,
        }

    async def verify_otp(
        self,
        organization_id: UUID,
        mobile: str,
        otp_code: str,
        purpose: OTPPurpose,
    ) -> Tuple[bool, Optional[str]]:
        """Verify OTP."""
        # Get latest OTP for this mobile and purpose
        stmt = (
            select(PortalOTP)
            .where(
                and_(
                    PortalOTP.organization_id == organization_id,
                    PortalOTP.mobile == mobile,
                    PortalOTP.purpose == purpose,
                    PortalOTP.is_used == False,
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
        email: Optional[str] = None,
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
        )
        self.db.add(user)
        return user

    async def login(
        self,
        organization_id: UUID,
        mobile: str,
        device_info: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Dict[str, Any]:
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
            device = await self._register_or_update_device(
                user.id, device_info, ip_address
            )
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
            "user": {
                "id": str(user.id),
                "mobile": user.mobile,
                "email": user.email,
                "preferred_language": user.preferred_language,
            },
            "session_token": session.session_token,
            "refresh_token": session.refresh_token,
            "expires_at": session.expires_at.isoformat(),
        }

    async def logout(
        self,
        session_token: str,
        logout_reason: str = "USER_INITIATED",
    ) -> bool:
        """Logout user and invalidate session."""
        stmt = select(PortalSession).where(
            PortalSession.session_token == session_token
        )
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
    ) -> Optional[Dict[str, Any]]:
        """Refresh session using refresh token."""
        stmt = select(PortalSession).where(
            and_(
                PortalSession.refresh_token == refresh_token,
                PortalSession.is_active == True,
            )
        )
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()

        if not session:
            return None

        # Generate new tokens
        session.session_token = self._generate_token()
        session.refresh_token = self._generate_token()
        session.expires_at = datetime.utcnow() + timedelta(
            hours=self.SESSION_EXPIRY_HOURS
        )
        session.last_activity_at = datetime.utcnow()

        return {
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
    ) -> Optional[PortalUser]:
        """Validate session and return user."""
        stmt = (
            select(PortalSession)
            .options(selectinload(PortalSession.user))
            .where(
                and_(
                    PortalSession.session_token == session_token,
                    PortalSession.is_active == True,
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
                PortalSession.is_active == True,
                PortalSession.expires_at > datetime.utcnow(),
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def invalidate_all_sessions(
        self,
        user_id: UUID,
        except_session_token: Optional[str] = None,
    ) -> int:
        """Invalidate all sessions for a user."""
        stmt = select(PortalSession).where(
            and_(
                PortalSession.user_id == user_id,
                PortalSession.is_active == True,
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
                    PortalDevice.is_active == True,
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
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
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
    ) -> Dict[str, Any]:
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
    ) -> Optional[PortalUser]:
        """Get user by mobile number."""
        stmt = select(PortalUser).where(
            and_(
                PortalUser.organization_id == organization_id,
                PortalUser.mobile == mobile,
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_id(
        self,
        user_id: UUID,
    ) -> Optional[PortalUser]:
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

    def _hash_otp(self, otp: str) -> str:
        """Hash OTP for secure storage."""
        return hashlib.sha256(otp.encode()).hexdigest()

    def _generate_token(self) -> str:
        """Generate secure session token."""
        return secrets.token_urlsafe(32)

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
        device_id: Optional[UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
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
        device_info: Dict[str, Any],
        ip_address: Optional[str] = None,
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
