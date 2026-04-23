"""Encryption utilities for sensitive data storage."""

import base64
import os
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.config import settings


class EncryptionService:
    """Service for encrypting/decrypting sensitive configuration data."""

    _instance: Optional["EncryptionService"] = None
    _fernet: Optional[Fernet] = None

    def __new__(cls) -> "EncryptionService":
        """Singleton pattern for encryption service."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """Initialize Fernet cipher with derived key."""
        # Use JWT_SECRET_KEY as base for encryption key derivation
        password = settings.JWT_SECRET_KEY.encode()

        # Use a fixed salt derived from app name (deterministic)
        salt = settings.APP_NAME.encode().ljust(16, b"\0")[:16]

        # Derive a key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        self._fernet = Fernet(key)

    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string.

        Args:
            plaintext: The string to encrypt

        Returns:
            Base64-encoded encrypted string
        """
        if not plaintext:
            return ""
        if self._fernet is None:
            raise RuntimeError("Encryption service not initialized")
        encrypted = self._fernet.encrypt(plaintext.encode())
        return encrypted.decode()

    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt an encrypted string.

        Args:
            ciphertext: Base64-encoded encrypted string

        Returns:
            Decrypted plaintext string
        """
        if not ciphertext:
            return ""
        if self._fernet is None:
            raise RuntimeError("Encryption service not initialized")
        decrypted = self._fernet.decrypt(ciphertext.encode())
        return decrypted.decode()

    def encrypt_dict(self, data: dict, sensitive_keys: list[str]) -> dict:
        """
        Encrypt specific keys in a dictionary.

        Args:
            data: Dictionary with values to encrypt
            sensitive_keys: List of keys whose values should be encrypted

        Returns:
            Dictionary with specified keys encrypted
        """
        result = data.copy()
        for key in sensitive_keys:
            if key in result and result[key]:
                result[key] = self.encrypt(str(result[key]))
        return result

    def decrypt_dict(self, data: dict, sensitive_keys: list[str]) -> dict:
        """
        Decrypt specific keys in a dictionary.

        Args:
            data: Dictionary with encrypted values
            sensitive_keys: List of keys whose values should be decrypted

        Returns:
            Dictionary with specified keys decrypted
        """
        result = data.copy()
        for key in sensitive_keys:
            if key in result and result[key]:
                try:
                    result[key] = self.decrypt(str(result[key]))
                except Exception:
                    # If decryption fails, keep original value
                    pass
        return result


# Singleton instance
encryption_service = EncryptionService()


def encrypt_value(plaintext: str) -> str:
    """Convenience function for encrypting a value."""
    return encryption_service.encrypt(plaintext)


def decrypt_value(ciphertext: str) -> str:
    """Convenience function for decrypting a value."""
    return encryption_service.decrypt(ciphertext)
