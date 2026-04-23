"""Security utilities for authentication and authorization."""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.core.constants import TokenType

# Password hashing context using Argon2
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate password hash."""
    return pwd_context.hash(password)


def create_access_token(
    subject: str | UUID,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[dict[str, Any]] = None,
) -> str:
    """Create JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": TokenType.ACCESS.value,
    }

    if additional_claims:
        to_encode.update(additional_claims)

    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_refresh_token(
    subject: str | UUID,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create JWT refresh token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": TokenType.REFRESH.value,
        "jti": secrets.token_urlsafe(32),  # Unique token ID
    }

    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def verify_token(token: str, token_type: TokenType = TokenType.ACCESS) -> Optional[dict]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        # Verify token type
        if payload.get("type") != token_type.value:
            return None

        return payload
    except JWTError:
        return None


def create_password_reset_token(email: str) -> str:
    """Create password reset token."""
    expire = datetime.now(timezone.utc) + timedelta(hours=1)

    to_encode = {
        "sub": email,
        "exp": expire,
        "type": TokenType.RESET_PASSWORD.value,
    }

    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def verify_password_reset_token(token: str) -> Optional[str]:
    """Verify password reset token and return email."""
    payload = verify_token(token, TokenType.RESET_PASSWORD)
    if payload:
        return payload.get("sub")
    return None


def generate_mfa_secret() -> str:
    """Generate a secret for MFA (TOTP)."""
    import pyotp
    return pyotp.random_base32()


def verify_mfa_code(secret: str, code: str) -> bool:
    """Verify MFA (TOTP) code."""
    import pyotp
    totp = pyotp.TOTP(secret)
    return totp.verify(code)


def get_mfa_provisioning_uri(secret: str, email: str) -> str:
    """Get MFA provisioning URI for QR code generation."""
    import pyotp
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=settings.APP_NAME)


# Re-export get_current_user from api.deps for backward compatibility
# Using lazy import to avoid circular dependency
def __getattr__(name: str):
    """Lazy import for backward compatibility."""
    if name == "get_current_user":
        from app.api.deps import get_current_user
        return get_current_user
    if name == "get_current_user_optional":
        from app.api.deps import get_current_user_optional
        return get_current_user_optional
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
