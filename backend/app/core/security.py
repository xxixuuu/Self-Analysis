"""
Security utilities for authentication, encryption, and password hashing.
"""
import base64
from datetime import datetime, timedelta
from typing import Optional, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import secrets

from app.core.config import settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password

    Returns:
        True if password matches
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create JWT access token.

    Args:
        data: Data to encode in token
        expires_delta: Token expiration time

    Returns:
        JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.jwt_expiration_minutes
        )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode JWT access token.

    Args:
        token: JWT token

    Returns:
        Decoded token data or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except JWTError:
        return None


class EncryptionManager:
    """Manager for encrypting sensitive data."""

    def __init__(self):
        """Initialize encryption manager."""
        # Derive encryption key from settings
        if settings.enable_encryption:
            try:
                # Try to use the encryption key directly if it's base64
                self.key = base64.urlsafe_b64decode(settings.encryption_key)
            except Exception:
                # Otherwise, derive a key from the string
                kdf = PBKDF2(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=b"lifemetrics_salt",  # In production, use a proper salt
                    iterations=100000,
                )
                self.key = base64.urlsafe_b64encode(
                    kdf.derive(settings.encryption_key.encode())
                )

            self.cipher = Fernet(self.key)
        else:
            self.cipher = None

    def encrypt(self, data: str) -> str:
        """
        Encrypt data.

        Args:
            data: Plain text data

        Returns:
            Encrypted data (base64 encoded)
        """
        if not settings.enable_encryption or not self.cipher:
            return data

        encrypted = self.cipher.encrypt(data.encode())
        return base64.urlsafe_b64encode(encrypted).decode()

    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt data.

        Args:
            encrypted_data: Encrypted data (base64 encoded)

        Returns:
            Decrypted plain text data
        """
        if not settings.enable_encryption or not self.cipher:
            return encrypted_data

        try:
            decoded = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.cipher.decrypt(decoded)
            return decrypted.decode()
        except Exception:
            # If decryption fails, return as-is (might be unencrypted legacy data)
            return encrypted_data

    def encrypt_dict(self, data: dict, fields: list[str]) -> dict:
        """
        Encrypt specific fields in a dictionary.

        Args:
            data: Dictionary with data
            fields: List of field names to encrypt

        Returns:
            Dictionary with encrypted fields
        """
        result = data.copy()
        for field in fields:
            if field in result and result[field]:
                result[field] = self.encrypt(str(result[field]))
        return result

    def decrypt_dict(self, data: dict, fields: list[str]) -> dict:
        """
        Decrypt specific fields in a dictionary.

        Args:
            data: Dictionary with encrypted data
            fields: List of field names to decrypt

        Returns:
            Dictionary with decrypted fields
        """
        result = data.copy()
        for field in fields:
            if field in result and result[field]:
                result[field] = self.decrypt(str(result[field]))
        return result


# Global encryption manager instance
encryption_manager = EncryptionManager()


def generate_state_token() -> str:
    """
    Generate a random state token for OAuth2 flows.

    Returns:
        Random state token
    """
    return secrets.token_urlsafe(32)


def generate_api_key() -> str:
    """
    Generate a random API key.

    Returns:
        Random API key
    """
    return secrets.token_urlsafe(48)
